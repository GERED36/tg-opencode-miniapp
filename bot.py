"""Telegram bot for OpenCode. Multi-user with auto-configured agents."""

import asyncio
import logging
import sys

import json

from aiohttp import web, WSMsgType
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import BOT_TOKEN, validate_config
from services.agent_bridge import AgentBridge
from services.session_manager import SessionManager
from handlers.commands import setup_handlers
from handlers.messages import setup_message_handlers
from handlers.callbacks import setup_callbacks
from utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

AGENT_SERVER_PORT = 8080
TMA_ORIGIN = "*"

_tma_ws: dict[int, web.WebSocketResponse] = {}
_ws_agents: dict[str, web.WebSocketResponse] = {}
_ws_agent_owners: dict[str, str] = {}


async def handle_tma_ws(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(max_msg_size=0)
    await ws.prepare(request)

    user_id = int(request.query.get("user_id", "0"))
    if not user_id:
        await ws.close()
        return ws

    _tma_ws[user_id] = ws
    logger.info("TMA connected: user %s", user_id)

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                msg_type = data.get("type")

                if msg_type == "message":
                    agent_id = data.get("agent_id", "")
                    text = data.get("text", "")
                    task_id = data.get("task_id", "")
                    agent_ws = _ws_agents.get(agent_id)
                    if not agent_ws:
                        await ws.send_json({"type": "error", "task_id": task_id, "message": "Агент не подключён"})
                        continue
                    try:
                        await agent_ws.send_json({"type": "run", "task_id": task_id, "message": text})
                    except ConnectionResetError:
                        _ws_agents.pop(agent_id, None)
                        await ws.send_json({"type": "error", "task_id": task_id, "message": "Агент недоступен"})

                elif msg_type == "new_session":
                    agent_id = data.get("agent_id", "")
                    agent_ws = _ws_agents.get(agent_id)
                    if agent_ws:
                        try:
                            await agent_ws.send_json({"type": "new_session"})
                        except ConnectionResetError:
                            _ws_agents.pop(agent_id, None)

                elif msg_type == "cancel":
                    agent_id = data.get("agent_id", "")
                    agent_ws = _ws_agents.get(agent_id)
                    if agent_ws:
                        try:
                            await agent_ws.send_json({"type": "cancel"})
                        except ConnectionResetError:
                            _ws_agents.pop(agent_id, None)

            elif msg.type == WSMsgType.ERROR:
                break
    except asyncio.CancelledError:
        pass
    finally:
        _tma_ws.pop(user_id, None)
    return ws


async def handle_agent_ws(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(max_msg_size=0)
    await ws.prepare(request)

    agent_id = ""
    user_id = ""

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                msg_type = data.get("type")

                if msg_type == "register":
                    agent_id = data.get("agent_id", "")
                    user_id_str = data.get("user_id", "")
                    user_id = user_id_str
                    _ws_agents[agent_id] = ws
                    _ws_agent_owners[agent_id] = user_id_str
                    logger.info("WS Agent registered: %s (user %s)", agent_id, user_id)

                elif msg_type == "chunk":
                    task_id = data.get("task_id", "")
                    uid = data.get("user_id", "")
                    if uid:
                        tma = _tma_ws.get(int(uid))
                        if tma:
                            try:
                                await tma.send_json({
                                    "type": "chunk", "task_id": task_id,
                                    "kind": data.get("kind", "answer"),
                                    "token": data.get("token", ""),
                                })
                            except ConnectionResetError:
                                _tma_ws.pop(int(uid), None)

                elif msg_type == "done":
                    task_id = data.get("task_id", "")
                    uid = data.get("user_id", "")
                    if uid:
                        tma = _tma_ws.get(int(uid))
                        if tma:
                            try:
                                await tma.send_json({"type": "done", "task_id": task_id})
                            except ConnectionResetError:
                                _tma_ws.pop(int(uid), None)

                elif msg_type == "error":
                    task_id = data.get("task_id", "")
                    uid = data.get("user_id", "")
                    message = data.get("message", "")
                    if uid:
                        tma = _tma_ws.get(int(uid))
                        if tma:
                            try:
                                await tma.send_json({"type": "error", "task_id": task_id, "message": message})
                            except ConnectionResetError:
                                _tma_ws.pop(int(uid), None)

                elif msg_type == "pong":
                    pass

            elif msg.type == WSMsgType.ERROR:
                break
    except asyncio.CancelledError:
        pass
    finally:
        if agent_id:
            _ws_agents.pop(agent_id, None)
            _ws_agent_owners.pop(agent_id, None)
    return ws


async def main() -> None:
    try:
        validate_config()
    except ValueError as e:
        logger.error("Config error: %s", e)
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    bridge = AgentBridge()
    session_manager = SessionManager()

    setup_handlers(dp, bridge, session_manager)
    setup_message_handlers(dp, bridge, session_manager)
    setup_callbacks(dp, bridge)

    commands = [
        BotCommand(command="start", description="Подключить ПК"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="status", description="Статус подключения"),
        BotCommand(command="disconnect", description="Отключить ПК"),
        BotCommand(command="sessions", description="Статус сессии"),
        BotCommand(command="new", description="Новая сессия"),
        BotCommand(command="delete", description="Удалить сессию"),
        BotCommand(command="cancel", description="Отменить запрос"),
        BotCommand(command="context", description="Установить контекст"),
        BotCommand(command="models", description="Список моделей"),
        BotCommand(command="model", description="Выбрать модель"),
        BotCommand(command="stats", description="Статистика opencode"),
        BotCommand(command="version", description="Версия opencode"),
        BotCommand(command="admin", description="Панель админа"),
        BotCommand(command="broadcast", description="Рассылка"),
    ]
    await bot.set_my_commands(commands)

    agent_app = bridge.create_app()

    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        if request.method == "OPTIONS":
            response = web.Response()
            response.headers["Access-Control-Allow-Origin"] = TMA_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response
        response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = TMA_ORIGIN
        return response

    agent_app.middlewares.append(cors_middleware)
    agent_app.router.add_get("/ws", handle_tma_ws)
    agent_app.router.add_get("/ws/agent", handle_agent_ws)

    runner = web.AppRunner(agent_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", AGENT_SERVER_PORT)
    await site.start()
    logger.info("Agent server started on port %d", AGENT_SERVER_PORT)

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

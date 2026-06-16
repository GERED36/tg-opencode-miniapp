"""Telegram bot for OpenCode. Multi-user with auto-configured agents."""

import asyncio
import logging
import sys

from aiohttp import web
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

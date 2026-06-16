import asyncio
import json
import logging

from aiohttp import web, WSMsgType

from hub.config import HUB_PORT, BOT_TOKEN, HOST, TMA_ORIGIN
from hub.ws_manager import WsManager
from hub.auth import verify_init_data, create_token, verify_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hub")

ws_manager = WsManager()


async def handle_tma_ws(request: web.Request) -> web.WebSocketResponse:
    init_data = request.query.get("initData", "")
    user = verify_init_data(init_data)
    if not user:
        user_id = int(request.query.get("user_id", "0"))
        if not user_id:
            return web.json_response({"error": "Unauthorized"}, status=401)
    else:
        user_id = user["id"]

    ws = web.WebSocketResponse(max_msg_size=0)
    await ws.prepare(request)

    tma = ws_manager.register_tma(user_id, ws)

    # Send agent list on connect
    agents = ws_manager.get_agents_for_user(user_id)
    await ws.send_json({"type": "agents", "agents": agents})

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

                    agent = ws_manager.get_agent(agent_id)
                    if not agent:
                        await ws.send_json({
                            "type": "error",
                            "task_id": task_id,
                            "message": "Агент не подключён",
                        })
                        continue

                    agent.busy = True
                    tma.active_agent_id = agent_id

                    ok = await ws_manager.send_to_agent(agent_id, {
                        "type": "run",
                        "task_id": task_id,
                        "message": text,
                    })
                    if not ok:
                        await ws.send_json({
                            "type": "error",
                            "task_id": task_id,
                            "message": "Агент недоступен",
                        })

                elif msg_type == "switch_agent":
                    tma.active_agent_id = data.get("agent_id", "")

                elif msg_type == "new_session":
                    agent_id = data.get("agent_id", "")
                    await ws_manager.send_to_agent(agent_id, {
                        "type": "new_session",
                    })

                elif msg_type == "cancel":
                    agent_id = data.get("agent_id", "")
                    await ws_manager.send_to_agent(agent_id, {
                        "type": "cancel",
                    })

            elif msg.type == WSMsgType.ERROR:
                break
    except asyncio.CancelledError:
        pass
    finally:
        ws_manager.unregister_tma(user_id)

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
                    user_id = data.get("user_id", "")
                    ws_manager.register_agent(agent_id, user_id, ws)

                    # Notify TMA about new agent
                    await ws_manager.send_to_tma(int(user_id), {
                        "type": "agents",
                        "agents": ws_manager.get_agents_for_user(int(user_id)),
                    })

                elif msg_type == "chunk":
                    task_id = data.get("task_id", "")
                    user_id = data.get("user_id", "")
                    if user_id:
                        await ws_manager.send_to_tma(int(user_id), {
                            "type": "chunk",
                            "task_id": task_id,
                            "kind": data.get("kind", "answer"),
                            "token": data.get("token", ""),
                        })

                elif msg_type == "done":
                    task_id = data.get("task_id", "")
                    user_id = data.get("user_id", "")
                    if agent_id:
                        agent = ws_manager.get_agent(agent_id)
                        if agent:
                            agent.busy = False
                    if user_id:
                        await ws_manager.send_to_tma(int(user_id), {
                            "type": "done",
                            "task_id": task_id,
                        })

                elif msg_type == "error":
                    task_id = data.get("task_id", "")
                    user_id = data.get("user_id", "")
                    message = data.get("message", "")
                    if agent_id:
                        agent = ws_manager.get_agent(agent_id)
                        if agent:
                            agent.busy = False
                    if user_id:
                        await ws_manager.send_to_tma(int(user_id), {
                            "type": "error",
                            "task_id": task_id,
                            "message": message,
                        })

                elif msg_type == "pong":
                    if agent_id:
                        agent = ws_manager.get_agent(agent_id)
                        if agent:
                            agent.last_seen = asyncio.get_event_loop().time()

            elif msg.type == WSMsgType.ERROR:
                break
    except asyncio.CancelledError:
        pass
    finally:
        if agent_id:
            ws_manager.unregister_agent(agent_id)
            # Notify TMA
            if user_id:
                await ws_manager.send_to_tma(int(user_id), {
                    "type": "agents",
                    "agents": ws_manager.get_agents_for_user(int(user_id)),
                })

    return ws


async def handle_auth(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    init_data = data.get("initData", "")
    user = verify_init_data(init_data)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    token = create_token(user["id"])
    return web.json_response({
        "ok": True,
        "token": token,
        "user": user,
    })


async def handle_agents_list(request: web.Request) -> web.Response:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        return web.json_response({"error": "Unauthorized"}, status=401)

    user_id = payload["user_id"]
    agents = ws_manager.get_agents_for_user(user_id)
    return web.json_response({"agents": agents})


async def handle_ping(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


def create_app() -> web.Application:
    app = web.Application()

    # CORS middleware
    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        if request.method == "OPTIONS":
            response = web.Response()
            response.headers["Access-Control-Allow-Origin"] = TMA_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
        response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = TMA_ORIGIN
        return response

    app.middlewares.append(cors_middleware)

    # Serve TMA static files (built SPA)
    app.router.add_static("/", path="tma/dist", show_index=True)

    # API routes
    app.router.add_post("/api/auth/tg", handle_auth)
    app.router.add_get("/api/agents", handle_agents_list)
    app.router.add_get("/api/ping", handle_ping)

    # WebSocket routes
    app.router.add_get("/ws", handle_tma_ws)
    app.router.add_get("/ws/agent", handle_agent_ws)

    return app


async def heartbeat_loop():
    """Send ping to all agents every 15 seconds."""
    while True:
        await asyncio.sleep(15)
        for agent_id, conn in list(ws_manager._agents.items()):
            try:
                await conn.ws.send_json({"type": "ping"})
            except ConnectionResetError:
                ws_manager.unregister_agent(agent_id)


async def main():
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, HUB_PORT)
    await site.start()
    logger.info("Hub started on %s:%d", HOST, HUB_PORT)

    asyncio.create_task(heartbeat_loop())

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

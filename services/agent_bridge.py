import asyncio
import json
import logging
import secrets
from pathlib import Path

from aiohttp import web

logger = logging.getLogger(__name__)

FILES_DIR = Path(__file__).resolve().parent.parent / "bot_files"


class AgentBridge:
    def __init__(self) -> None:
        self._pending_commands: dict[str, asyncio.Event] = {}
        self._command_responses: dict[str, dict] = {}
        self._connected_agents: dict[str, dict] = {}

    @property
    def connected_agents(self) -> dict[str, dict]:
        return self._connected_agents

    def is_connected(self, user_id: int) -> bool:
        return str(user_id) in self._connected_agents

    def disconnect(self, user_id: int) -> bool:
        uid = str(user_id)
        if uid in self._connected_agents:
            del self._connected_agents[uid]
            return True
        return False

    def get_connected_count(self) -> int:
        return len(self._connected_agents)

    def create_app(self) -> web.Application:
        app = web.Application()
        app.router.add_post("/agent/register", self._handle_register)
        app.router.add_post("/agent/poll", self._handle_poll)
        app.router.add_post("/agent/response", self._handle_response)
        app.router.add_get("/files/{filename}", self._handle_file_download)
        app.router.add_post("/files/upload", self._handle_file_upload)
        return app

    async def _handle_register(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"ok": False, "error": "Invalid JSON"})
        user_id = data.get("user_id", "")
        token = data.get("token", "")
        if not user_id or not token:
            return web.json_response({"ok": False, "error": "Missing fields"})
        self._connected_agents[user_id] = {
            "token": token,
            "last_seen": asyncio.get_event_loop().time(),
        }
        logger.info("Agent registered: user %s", user_id)
        return web.json_response({"ok": True})

    async def _handle_poll(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"ok": False, "error": "Invalid JSON"})
        user_id = data.get("user_id", "")
        token = data.get("token", "")
        agent = self._connected_agents.get(user_id)
        if not agent or agent["token"] != token:
            return web.json_response({"ok": False, "error": "Unauthorized"})
        agent["last_seen"] = asyncio.get_event_loop().time()
        for rid in list(self._command_responses.keys()):
            if rid.startswith(f"{user_id}_") and self._command_responses[rid] is not None:
                cmd_data = self._command_responses[rid]
                self._command_responses[rid] = None
                cmd_data["request_id"] = rid
                return web.json_response(cmd_data)
        return web.json_response({"cmd": "wait"})

    async def _handle_response(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"ok": False, "error": "Invalid JSON"})
        user_id = data.get("user_id", "")
        token = data.get("token", "")
        request_id = data.get("request_id", "")
        result = data.get("result", "")
        agent = self._connected_agents.get(user_id)
        if not agent or agent["token"] != token:
            return web.json_response({"ok": False, "error": "Unauthorized"})
        if request_id and request_id in self._command_responses:
            self._command_responses[request_id] = {"cmd": "run", "result": result}
            if request_id in self._pending_commands:
                self._pending_commands[request_id].set()
        else:
            for rid in list(self._command_responses.keys()):
                if rid.startswith(f"{user_id}_"):
                    self._command_responses[rid] = {"cmd": "run", "result": result}
                    if rid in self._pending_commands:
                        self._pending_commands[rid].set()
                    break
        return web.json_response({"ok": True})

    async def _handle_file_download(self, request: web.Request) -> web.Response:
        filename = request.match_info.get("filename", "")
        filepath = FILES_DIR / filename
        if not filepath.exists() or not filepath.is_file():
            raise web.HTTPNotFound()
        return web.FileResponse(filepath)

    async def _handle_file_upload(self, request: web.Request) -> web.Response:
        reader = await request.multipart()
        field = await reader.next()
        if not field or not field.filename:
            return web.json_response({"ok": False, "error": "No file"})
        filename = Path(field.filename).name
        filepath = FILES_DIR / filename
        with open(filepath, "wb") as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                f.write(chunk)
        return web.json_response({"ok": True, "filename": filename})

    async def ask_agent(
        self,
        user_id: int,
        message: str,
        continue_session: bool = False,
        files: list[str] | None = None,
        timeout: int = 360,
    ) -> str:
        uid = str(user_id)
        if uid not in self._connected_agents:
            return "❌ Ваш ПК не подключён. Отправьте /start для инструкций."

        request_id = f"{uid}_{secrets.token_hex(4)}"
        self._pending_commands[request_id] = asyncio.Event()
        cmd_data: dict = {
            "cmd": "run",
            "message": message,
            "continue_session": continue_session,
        }
        if files:
            cmd_data["files"] = files
        self._command_responses[request_id] = cmd_data

        try:
            await asyncio.wait_for(self._pending_commands[request_id].wait(), timeout=timeout)
            result = self._command_responses.get(request_id, {})
            return result.get("result", "⏳ Нет ответа от агента.")
        except asyncio.TimeoutError:
            return "❌ Агент не ответил за 6 минут. Проверьте, что agent.py запущен."
        finally:
            self._pending_commands.pop(request_id, None)
            self._command_responses.pop(request_id, None)

    async def cancel_request(self, user_id: int) -> bool:
        uid = str(user_id)
        for rid in list(self._pending_commands.keys()):
            if rid.startswith(f"{uid}_"):
                self._pending_commands[rid].set()
                self._command_responses[rid] = {"cmd": "cancelled", "result": "❌ Запрос отменён."}
                return True
        return False

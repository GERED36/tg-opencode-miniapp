import asyncio
import json
import logging
import time

from aiohttp import web, WSMsgType

logger = logging.getLogger(__name__)


class AgentConnection:
    def __init__(self, ws: web.WebSocketResponse, agent_id: str, user_id: str):
        self.ws = ws
        self.agent_id = agent_id
        self.user_id = user_id
        self.last_seen = time.time()
        self.busy = False


class TmaConnection:
    def __init__(self, ws: web.WebSocketResponse, user_id: int):
        self.ws = ws
        self.user_id = user_id
        self.active_agent_id: str | None = None


class WsManager:
    def __init__(self):
        self._agents: dict[str, AgentConnection] = {}
        self._tma_by_uid: dict[int, TmaConnection] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def register_agent(self, agent_id: str, user_id: str, ws: web.WebSocketResponse) -> AgentConnection:
        conn = AgentConnection(ws, agent_id, user_id)
        self._agents[agent_id] = conn
        logger.info("Agent registered: %s (user %s)", agent_id, user_id)
        return conn

    def unregister_agent(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)
        logger.info("Agent unregistered: %s", agent_id)

    def register_tma(self, user_id: int, ws: web.WebSocketResponse) -> TmaConnection:
        conn = TmaConnection(ws, user_id)
        self._tma_by_uid[user_id] = conn
        logger.info("TMA connected: user %s", user_id)
        return conn

    def unregister_tma(self, user_id: int) -> None:
        self._tma_by_uid.pop(user_id, None)

    def get_agent(self, agent_id: str) -> AgentConnection | None:
        return self._agents.get(agent_id)

    def get_agents_for_user(self, user_id: int) -> list[dict]:
        result = []
        uid = str(user_id)
        for agent_id, conn in self._agents.items():
            if conn.user_id == uid:
                result.append({
                    "id": agent_id,
                    "name": agent_id,
                    "status": "busy" if conn.busy else "online",
                })
        return result

    def get_tma(self, user_id: int) -> TmaConnection | None:
        return self._tma_by_uid.get(user_id)

    async def send_to_tma(self, user_id: int, data: dict) -> bool:
        tma = self.get_tma(user_id)
        if not tma:
            return False
        try:
            await tma.ws.send_json(data)
            return True
        except ConnectionResetError:
            self.unregister_tma(user_id)
            return False

    async def send_to_agent(self, agent_id: str, data: dict) -> bool:
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        try:
            await agent.ws.send_json(data)
            return True
        except ConnectionResetError:
            self.unregister_agent(agent_id)
            return False

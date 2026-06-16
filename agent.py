"""OpenCode Agent — connects to Cloud Hub via WebSocket.
Usage:
    python agent.py --hub-url WS_URL --user-id ID --token TOKEN [--work-dir DIR]
"""

import argparse
import asyncio
import json
import logging
import secrets
import shutil
import sys
import tempfile
import pathlib
from pathlib import Path

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent")

OPENCODE_BIN = shutil.which("opencode") or "opencode"
OPENCODE_TIMEOUT = 300
AGENT_TOKEN = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenCode Agent")
    parser.add_argument("--hub-url", type=str, default="ws://127.0.0.1:8081/ws/agent",
                        help="Cloud Hub WebSocket URL")
    parser.add_argument("--user-id", type=str, required=True,
                        help="Your Telegram user ID")
    parser.add_argument("--token", type=str, default="",
                        help="Authorization token (auto-generated if empty)")
    parser.add_argument("--work-dir", type=str, default=str(Path.cwd()),
                        help="Working directory for opencode")
    return parser.parse_args()


async def stream_opencode(
    message: str,
    work_dir: str,
    user_id: str,
    task_id: str,
    ws: aiohttp.ClientWebSocketResponse,
    session_id: str = "",
    file_urls: list[str] | None = None,
) -> None:
    try:
        cmd = [OPENCODE_BIN, "run", message, "--dir", work_dir,
               "--dangerously-skip-permissions"]
        if session_id:
            cmd.extend(["--session", session_id])

        if file_urls:
            dest = tempfile.mkdtemp(prefix="oc_files_")
            for url in file_urls:
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(url) as resp:
                        fname = url.rsplit("/", 1)[-1] or "file"
                        fpath = str(Path(dest) / fname)
                        with open(fpath, "wb") as f:
                            while chunk := await resp.content.read(8192):
                                f.write(chunk)
                        cmd.extend(["-f", fpath])

        logger.info("Streaming opencode: %s ...", cmd[:3])
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        in_thought = False

        async for line in process.stdout:
            text = line.decode("utf-8", errors="replace")
            stripped = text.strip()
            if not stripped:
                continue

            # Detect reasoning tags
            if "<thought>" in stripped:
                in_thought = True
                continue
            if "</thought>" in stripped:
                in_thought = False
                continue

            kind = "reasoning" if in_thought else "answer"
            await ws.send_json({
                "type": "chunk",
                "user_id": user_id,
                "task_id": task_id,
                "kind": kind,
                "token": text,
            })

        # Wait for process and check return code
        await process.wait()
        if process.returncode != 0:
            stderr_data = await process.stderr.read()
            err_text = stderr_data.decode("utf-8", errors="replace")[:500]
            await ws.send_json({
                "type": "error",
                "user_id": user_id,
                "task_id": task_id,
                "message": f"OpenCode error (code {process.returncode}): {err_text}",
            })
            return

        await ws.send_json({
            "type": "done",
            "user_id": user_id,
            "task_id": task_id,
        })

    except asyncio.TimeoutError:
        await ws.send_json({
            "type": "error",
            "user_id": user_id,
            "task_id": task_id,
            "message": f"OpenCode timeout ({OPENCODE_TIMEOUT}s)",
        })
    except FileNotFoundError:
        await ws.send_json({
            "type": "error",
            "user_id": user_id,
            "task_id": task_id,
            "message": "OpenCode not found. Install: pip install opencode",
        })
    except Exception as e:
        logger.exception("Stream error")
        await ws.send_json({
            "type": "error",
            "user_id": user_id,
            "task_id": task_id,
            "message": f"Error: {e}",
        })


async def run(hub_url: str, user_id: str, token: str, work_dir: str) -> None:
    global AGENT_TOKEN
    AGENT_TOKEN = token or secrets.token_hex(16)

    agent_id = f"user_{user_id}_{secrets.token_hex(4)}"
    logger.info("Connecting to hub: %s (agent_id: %s)", hub_url, agent_id)

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(hub_url) as ws:
            # Register
            await ws.send_json({
                "type": "register",
                "agent_id": agent_id,
                "user_id": user_id,
                "token": AGENT_TOKEN,
            })
            logger.info("Registered, waiting for commands...")

            # Handle incoming messages
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue

                    msg_type = data.get("type")

                    if msg_type == "run":
                        task_id = data.get("task_id", "")
                        message = data.get("message", "")
                        session_id = data.get("session_id", "")

                        await stream_opencode(
                            message, work_dir, user_id, task_id, ws,
                            session_id=session_id,
                        )

                    elif msg_type == "ping":
                        await ws.send_json({"type": "pong"})

                    elif msg_type == "cancel":
                        logger.info("Cancel requested for current task")

                    elif msg_type == "new_session":
                        logger.info("New session requested")

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break


def main() -> None:
    args = parse_args()
    print(f"\n{'='*50}")
    print(f"  OpenCode Agent (WebSocket)")
    print(f"{'='*50}")
    print(f"  Hub URL:    {args.hub_url}")
    print(f"  User ID:    {args.user_id}")
    print(f"  Token:      {args.token or '(auto)'}")
    print(f"  Work dir:   {args.work_dir}")
    print(f"{'='*50}\n")

    try:
        asyncio.run(run(args.hub_url, args.user_id, args.token, args.work_dir))
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()

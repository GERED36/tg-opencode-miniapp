"""OpenCode Agent — auto-generated. Connects to bot at 198.18.0.1:8080"""

import asyncio
import json
import logging
import shutil
import sys

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agent")

OPENCODE_BIN = shutil.which("opencode") or "opencode"
OPENCODE_TIMEOUT = 120
BOT_URL = "http://198.18.0.1:8080"
USER_ID = "1623003780"
TOKEN = "313bb333513869ac048b5741d61c78fa"


async def run_opencode(message: str, session_id: str = "") -> str:
    try:
        cmd = [OPENCODE_BIN, "run", message, "--dangerously-skip-permissions"]
        if session_id:
            cmd.extend(["--session", session_id])
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=OPENCODE_TIMEOUT)
        return stdout.decode("utf-8", errors="replace").strip() or stderr.decode("utf-8", errors="replace").strip()[:500]
    except asyncio.TimeoutError:
        return f"Таймаут (120 сек)"
    except FileNotFoundError:
        return "OpenCode не найден. pip install opencode"
    except Exception as e:
        return f"Ошибка: {e}"


async def register():
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BOT_URL}/agent/register", json={"user_id": USER_ID, "token": TOKEN}) as resp:
            return await resp.json()


async def poll():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.post(f"{BOT_URL}/agent/poll", json={"user_id": USER_ID, "token": TOKEN}, timeout=aiohttp.ClientTimeout(total=35)) as resp:
                    data = await resp.json()
                    if data.get("cmd") == "run":
                        result = await run_opencode(data.get("message", ""), data.get("session_id", ""))
                        request_id = data.get("request_id", "")
                        await session.post(f"{BOT_URL}/agent/response", json={"user_id": USER_ID, "token": TOKEN, "request_id": request_id, "result": result})
                    else:
                        await asyncio.sleep(3)
            except asyncio.TimeoutError:
                await asyncio.sleep(3)
            except Exception as e:
                logger.warning("Poll error: %s", e)
                await asyncio.sleep(5)


def main():
    print(f"OpenCode Agent")
    print(f"Bot: {BOT_URL}")
    print(f"User ID: {USER_ID}")
    print(f"Connecting...")
    asyncio.run(run())


async def run():
    await register()
    print("Connected! Polling for commands...")
    await poll()


if __name__ == "__main__":
    main()

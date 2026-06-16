import asyncio
import logging
import shutil

from config import OPENCODE_BIN_PATH

logger = logging.getLogger(__name__)

OPENCODE_TIMEOUT = 30
OPENCODE_BIN = OPENCODE_BIN_PATH or shutil.which("opencode") or "opencode"


async def get_opencode_version() -> str:
    cmd = [OPENCODE_BIN, "--version"]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=OPENCODE_TIMEOUT)
        text = stdout.decode("utf-8", errors="replace").strip()
        return text or "OpenCode установлен"
    except FileNotFoundError:
        return "❌ OpenCode не найден. Установите: pip install opencode"
    except asyncio.TimeoutError:
        return "❌ OpenCode не ответил"
    except Exception as e:
        return f"❌ Ошибка: {e}"

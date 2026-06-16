"""OpenCode client module. Sends messages to opencode and returns responses."""

import asyncio
import logging
import shutil

from config import OPENCODE_WORK_DIR, OPENCODE_BIN_PATH

logger = logging.getLogger(__name__)

OPENCODE_TIMEOUT = 120

OPENCODE_BIN = OPENCODE_BIN_PATH or shutil.which("opencode")


async def _run(cmd: list[str], timeout: int = OPENCODE_TIMEOUT) -> tuple[str, str, int]:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    return (
        stdout.decode("utf-8", errors="replace").strip(),
        stderr.decode("utf-8", errors="replace"),
        process.returncode or 0,
    )


async def ask_opencode(message: str, session_id: str = "") -> str:
    """Send a message to opencode and return the response."""
    if not message.strip() and not session_id:
        return "Пустое сообщение не может быть обработано."

    try:
        is_long = len(message) > 2000
        if is_long:
            import pathlib, tempfile, secrets
            msg_file = pathlib.Path(tempfile.gettempdir()) / ("oc_" + secrets.token_hex(4) + ".txt")
            msg_file.write_text(message, encoding="utf-8")
            ps_cmd = 'Get-Content "' + str(msg_file) + '" -Raw | & "' + OPENCODE_BIN + '" run --dir "' + OPENCODE_WORK_DIR + '" --dangerously-skip-permissions'
            if session_id:
                ps_cmd += ' --session "' + session_id + '"'
            cmd = ["powershell", "-NoProfile", "-Command", ps_cmd]
        else:
            cmd = [OPENCODE_BIN, "run", message, "--dir", OPENCODE_WORK_DIR, "--dangerously-skip-permissions"]
            if session_id:
                cmd.extend(["--session", session_id])

        logger.info("Running opencode: %s", cmd[0:3] if not is_long else cmd[:2])
        stdout_text, stderr_text, rc = await _run(cmd)

        logger.info("OpenCode stdout length: %d", len(stdout_text))
        if stderr_text:
            logger.info("OpenCode stderr: %s", stderr_text[:200])

        if rc != 0:
            return f"Ошибка OpenCode (код {rc}): {stderr_text[:500]}"

        return stdout_text or "OpenCode не вернул ответ."

    except asyncio.TimeoutError:
        return f"OpenCode не ответил вовремя (таймаут {OPENCODE_TIMEOUT} сек)."
    except FileNotFoundError:
        return "OpenCode не найден. Установите opencode и добавьте в PATH."
    except Exception as e:
        logger.exception("Unexpected error in ask_opencode")
        return f"Неожиданная ошибка: {e}"


async def run_opencode_cmd(args: list[str], timeout: int = 30) -> str:
    """Run an arbitrary opencode subcommand and return its output."""
    try:
        cmd = [OPENCODE_BIN] + args
        logger.info("Running opencode cmd: %s", cmd)
        stdout_text, stderr_text, rc = await _run(cmd, timeout=timeout)

        if rc != 0:
            return f"Ошибка (код {rc}): {stderr_text[:500]}"

        return stdout_text or stderr_text.strip() or "Готово."

    except asyncio.TimeoutError:
        return "Команда не выполнилась (таймаут)."
    except FileNotFoundError:
        return "OpenCode не найден."
    except Exception as e:
        return f"Ошибка: {e}"

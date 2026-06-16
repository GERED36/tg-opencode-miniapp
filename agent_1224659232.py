"""OpenCode Agent — auto-generated."""
import asyncio, json, logging, shutil, sys, tempfile, pathlib, secrets
import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agent")

OPENCODE_BIN = shutil.which("opencode") or "opencode"
OPENCODE_TIMEOUT = 300
BOT_URL = "http://127.0.0.1:8080"
USER_ID = "1224659232"
TOKEN = "5e189dff837418681bb9f2a6b4611fb2"


async def download_file(url: str, dest_dir: str) -> str:
    fname = url.rsplit("/", 1)[-1].split("?")[0] or "file"
    fpath = str(pathlib.Path(dest_dir) / fname)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            with open(fpath, "wb") as f:
                while chunk := await resp.content.read(8192):
                    f.write(chunk)
    return fpath


async def run_opencode(message: str, continue_session: bool = False, file_urls: list[str] | None = None) -> str:
    try:
        is_long = len(message) > 2000
        if is_long:
            msg_file = pathlib.Path(tempfile.gettempdir()) / ("oc_" + secrets.token_hex(4) + ".txt")
            msg_file.write_text(message, encoding="utf-8")
            ps_cmd = f'Get-Content "${msg_file}" -Raw | & "${OPENCODE_BIN}" run --dangerously-skip-permissions'
            if continue_session:
                ps_cmd += " --continue"
            if file_urls:
                dest = tempfile.mkdtemp(prefix="oc_files_")
                for url in file_urls:
                    local = await download_file(url, dest)
                    ps_cmd += f' -f "${local}"'
            cmd = ["powershell", "-NoProfile", "-Command", ps_cmd]
        else:
            cmd = [OPENCODE_BIN, "run", message, "--dangerously-skip-permissions"]
            if continue_session:
                cmd.append("--continue")
            if file_urls:
                dest = tempfile.mkdtemp(prefix="oc_files_")
                for url in file_urls:
                    local = await download_file(url, dest)
                    cmd.extend(["-f", local])
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=OPENCODE_TIMEOUT)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            return f"Таймаут ({OPENCODE_TIMEOUT} сек)"
        return stdout.decode("utf-8", errors="replace").strip() or stderr.decode("utf-8", errors="replace").strip()[:500]
    except FileNotFoundError:
        return "OpenCode не найден. pip install opencode"
    except Exception as e:
        return f"Ошибка: {e}"


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BOT_URL}/agent/register", json={"user_id": USER_ID, "token": TOKEN}) as resp:
            data = await resp.json()
            if not data.get("ok"):
                print("Registration failed:", data)
                return
        print("Connected! Polling for commands...")
        while True:
            try:
                async with session.post(f"{BOT_URL}/agent/poll", json={"user_id": USER_ID, "token": TOKEN}, timeout=aiohttp.ClientTimeout(total=35)) as resp:
                    data = await resp.json()
                    if data.get("cmd") == "run":
                        result = await run_opencode(data.get("message", ""), data.get("continue_session", False), data.get("files"))
                        await session.post(f"{BOT_URL}/agent/response", json={"user_id": USER_ID, "token": TOKEN, "request_id": data.get("request_id", ""), "result": result})
                    else:
                        await asyncio.sleep(3)
            except asyncio.TimeoutError:
                await asyncio.sleep(3)
            except Exception as e:
                logger.warning("Poll error: %s", e)
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())

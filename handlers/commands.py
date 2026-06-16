import asyncio
import logging
import secrets
from collections import deque
from pathlib import Path
from time import time

from aiogram import Dispatcher, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import is_admin, RATE_LIMIT_PER_MINUTE
from models_db import (
    MODELS_DB, get_model_by_id, format_context_limit,
    search_models, format_capabilities,
)
from services.agent_bridge import AgentBridge
from services.opencode_runner import get_opencode_version
from services.session_manager import SessionManager
from utils.formatter import _send, _encode_model_id, _typing_loop, _split_text

logger = logging.getLogger(__name__)

router = Router()

HELP_TEXT = """🤖 Команды OpenCode Bot:

🔗 Подключение:
/start — получить agent.py
/status — статус подключения
/disconnect — отключить ПК

💬 Сессии:
/sessions — статус сессии
/new — новая сессия (сброс контекста)
/delete — удалить текущую сессию
/delete all — удалить все сессии
/cancel — отменить текущий запрос

📝 Контекст:
/context — показать контекст
/context <текст> — установить контекст
/context delete — удалить контекст

🧠 Модели:
/models — список моделей
/model — выбрать модель
/model <название> — сменить модель
/stats — статистика opencode
/version — версия opencode

🔒 Admin:
/admin — панель управления
/broadcast <текст> — рассылка

❓ /help — эта справка"""

_model_hash_map: dict[str, str] = {}
_rate_limit_buckets: dict[int, deque] = {}
EMOJI_MAP: dict[str, str] = {}

_LOADED_EMOJI = False


def _load_emoji() -> None:
    global EMOJI_MAP, _LOADED_EMOJI
    if _LOADED_EMOJI:
        return
    emoji_file = Path(__file__).resolve().parent.parent / "premium_emoji.json"
    if emoji_file.exists():
        import json
        try:
            with open(emoji_file, "r", encoding="utf-8") as f:
                EMOJI_MAP = json.load(f)
            logger.info("Loaded %d premium emoji", len(EMOJI_MAP))
        except Exception as e:
            logger.warning("Failed to load emoji: %s", e)
    _LOADED_EMOJI = True


def _check_rate_limit(user_id: int) -> bool:
    now = time()
    bucket = _rate_limit_buckets.get(user_id)
    if bucket is None:
        _rate_limit_buckets[user_id] = deque(maxlen=RATE_LIMIT_PER_MINUTE)
        bucket = _rate_limit_buckets[user_id]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_PER_MINUTE:
        return False
    bucket.append(now)
    return True


def _generate_agent_py(user_id: str, token: str, bot_host: str = "127.0.0.1", bot_port: int = 8080) -> str:
    return f'''"""OpenCode Agent — auto-generated."""
import asyncio, json, logging, shutil, sys, tempfile, pathlib, secrets
import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agent")

OPENCODE_BIN = shutil.which("opencode") or "opencode"
OPENCODE_TIMEOUT = 300
BOT_URL = "http://{bot_host}:{bot_port}"
USER_ID = "{user_id}"
TOKEN = "{token}"


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
            ps_cmd = f'Get-Content "${{msg_file}}" -Raw | & "${{OPENCODE_BIN}}" run --dangerously-skip-permissions'
            if continue_session:
                ps_cmd += " --continue"
            if file_urls:
                dest = tempfile.mkdtemp(prefix="oc_files_")
                for url in file_urls:
                    local = await download_file(url, dest)
                    ps_cmd += f' -f "${{local}}"'
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
            return f"Таймаут ({{OPENCODE_TIMEOUT}} сек)"
        return stdout.decode("utf-8", errors="replace").strip() or stderr.decode("utf-8", errors="replace").strip()[:500]
    except FileNotFoundError:
        return "OpenCode не найден. pip install opencode"
    except Exception as e:
        return f"Ошибка: {{e}}"


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{{BOT_URL}}/agent/register", json={{"user_id": USER_ID, "token": TOKEN}}) as resp:
            data = await resp.json()
            if not data.get("ok"):
                print("Registration failed:", data)
                return
        print("Connected! Polling for commands...")
        while True:
            try:
                async with session.post(f"{{BOT_URL}}/agent/poll", json={{"user_id": USER_ID, "token": TOKEN}}, timeout=aiohttp.ClientTimeout(total=35)) as resp:
                    data = await resp.json()
                    if data.get("cmd") == "run":
                        result = await run_opencode(data.get("message", ""), data.get("continue_session", False), data.get("files"))
                        await session.post(f"{{BOT_URL}}/agent/response", json={{"user_id": USER_ID, "token": TOKEN, "request_id": data.get("request_id", ""), "result": result}})
                    else:
                        await asyncio.sleep(3)
            except asyncio.TimeoutError:
                await asyncio.sleep(3)
            except Exception as e:
                logger.warning("Poll error: %s", e)
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
'''


def setup_handlers(dp: Dispatcher, bridge: AgentBridge, session_manager: SessionManager) -> None:
    _load_emoji()
    dp.include_router(router)

    @dp.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        user_id = message.from_user.id
        uid = str(user_id)
        token = secrets.token_hex(16)

        agent_code = _generate_agent_py(uid, token)
        agent_file = Path(__file__).resolve().parent.parent / f"agent_{user_id}.py"
        agent_file.write_text(agent_code, encoding="utf-8")

        await message.answer(
            "🤖 **OpenCode Telegram Bot**\n\n"
            "📝 **Для подключения:**\n\n"
            "1. 📥 Установите opencode:\n"
            "   `pip install opencode aiohttp`\n\n"
            "2. 💾 Сохраните полученный `agent_{user_id}.py`\n\n"
            "3. ▶️ Запустите:\n"
            "   `python agent_{user_id}.py`\n\n"
            "4. ✅ Готово! Пишите сообщения — бот ответит через OpenCode",
            parse_mode="Markdown",
        )
        await message.answer_document(
            FSInputFile(agent_file),
            caption=f"agent_{user_id}.py — запустите на своём ПК",
        )

    @dp.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        for chunk in _split_text(HELP_TEXT, 4000):
            await message.answer(chunk)

    @dp.message(Command("status"))
    async def cmd_status(message: Message) -> None:
        user_id = message.from_user.id
        if not _check_rate_limit(user_id) and not is_admin(user_id):
            await message.answer("⏳ Слишком много запросов. Подождите.")
            return

        uid = str(user_id)
        connected = bridge.is_connected(user_id)
        has_session = session_manager.has_session(user_id)
        ctx = session_manager.get_context(user_id)

        lines = ["📊 **Статус:**\n"]
        lines.append(f"{'✅' if connected else '❌'} **ПК:** {'подключён' if connected else 'не подключён'}")
        lines.append(f"{'✅' if has_session else 'ℹ️'} **Сессия:** {'активна' if has_session else 'не активна'}")
        lines.append(f"{'📝' if ctx else 'ℹ️'} **Контекст:** {'задан' if ctx else 'не задан'}")
        await _send(message, "\n".join(lines), EMOJI_MAP)

    @dp.message(Command("disconnect"))
    async def cmd_disconnect(message: Message) -> None:
        if bridge.disconnect(message.from_user.id):
            await message.answer("✅ Агент отключён.")
        else:
            await message.answer("ℹ️ Нет подключённого агента.")

    @dp.message(Command("sessions"))
    @dp.message(Command("session"))
    async def cmd_sessions(message: Message) -> None:
        user_id = message.from_user.id
        if not _check_rate_limit(user_id) and not is_admin(user_id):
            await message.answer("⏳ Слишком много запросов. Подождите.")
            return

        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        if session_manager.has_session(user_id):
            await _send(message, "📋 **Сессия активна** — контекст диалога сохраняется.\nИспользуй `/new` чтобы начать новую.", EMOJI_MAP)
        else:
            await _send(message, "ℹ️ Нет активной сессии. Отправь сообщение — сессия создастся автоматически.", EMOJI_MAP)

    @dp.message(Command("new"))
    async def cmd_new(message: Message) -> None:
        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        session_manager.reset_session(user_id)
        await message.answer("✅ Новая сессия создана. Контекст сброшен.")

    @dp.message(Command("delete"))
    async def cmd_delete(message: Message) -> None:
        user_id = message.from_user.id
        args = message.text.split(maxsplit=1)
        if len(args) >= 2 and args[1].strip().lower() == "all":
            if session_manager.delete_all_sessions(user_id):
                await message.answer("✅ Все сессии удалены.")
            else:
                await message.answer("ℹ️ Нет сессий для удаления.")
        else:
            if session_manager.delete_session(user_id):
                await message.answer("✅ Сессия удалена.")
            else:
                await message.answer("ℹ️ Нет активной сессии для удаления.")

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: Message) -> None:
        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён.")
            return
        if await bridge.cancel_request(user_id):
            await message.answer("✅ Запрос отменён.")
        else:
            await message.answer("ℹ️ Нет активного запроса для отмены.")

    @dp.message(Command("context"))
    async def cmd_context(message: Message) -> None:
        user_id = message.from_user.id
        args = message.text.split(maxsplit=1)

        if len(args) >= 2 and args[1].strip():
            txt = args[1].strip()
            if txt.lower() == "delete":
                if session_manager.delete_context(user_id):
                    await message.answer("✅ Контекст удалён.")
                else:
                    await message.answer("ℹ️ Контекст не задан.")
            else:
                session_manager.set_context(user_id, txt)
                await message.answer("✅ Контекст установлен. Он будет использоваться при старте новой сессии.")
        else:
            current = session_manager.get_context(user_id)
            if current:
                await _send(message, f"📝 **Текущий контекст:**\n{current}\n\n*Используй `/context delete` чтобы удалить.*", EMOJI_MAP)
            else:
                await message.answer("ℹ️ Контекст не задан. Используй `/context <текст>` чтобы установить начальный контекст для новых сессий.")

    @dp.message(Command("models"))
    async def cmd_models(message: Message) -> None:
        user_id = message.from_user.id
        if not _check_rate_limit(user_id) and not is_admin(user_id):
            await message.answer("⏳ Слишком много запросов. Подождите.")
            return

        args = message.text.split(maxsplit=1)
        if len(args) >= 2 and args[1].strip():
            query = args[1].strip()
            results = search_models(query)
            if not results:
                await message.answer(f"❌ Ничего не найдено по запросу: `{query}`", parse_mode="Markdown")
                return
            lines = [f"📋 **Результаты поиска:** `{query}`\n"]
            for m in results[:20]:
                caps = format_capabilities(m)
                ctx = format_context_limit(m.context_limit)
                lines.append(f"{caps} `{m.model_id}` — {ctx}")
            await _send(message, "\n".join(lines), EMOJI_MAP)
            return

        lines = [f"📋 **Все модели ({len(MODELS_DB)}):**\n"]
        for m in MODELS_DB[:30]:
            caps = format_capabilities(m)
            ctx = format_context_limit(m.context_limit)
            name_short = m.model_id.replace("openrouter/", "").replace("opencode/", "")
            lines.append(f"{caps} `{name_short}` — {ctx}")
        if len(MODELS_DB) > 30:
            lines.append(f"\n*... и ещё {len(MODELS_DB) - 30} моделей. Используйте /models <поиск> для поиска.*")
        await _send(message, "\n".join(lines), EMOJI_MAP)

    @dp.message(Command("model"))
    async def cmd_model(message: Message) -> None:
        user_id = message.from_user.id
        if not _check_rate_limit(user_id) and not is_admin(user_id):
            await message.answer("⏳ Слишком много запросов. Подождите.")
            return

        args = message.text.split(maxsplit=1)
        if len(args) >= 2 and args[1].strip():
            model_name = args[1].strip()
            if not bridge.is_connected(user_id):
                await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
                return
            typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
            try:
                result = await bridge.ask_agent(user_id, f"config set model {model_name}")
            finally:
                typing_task.cancel()
            if "Ошибка" in result or "❌" in result:
                await message.answer(f"❌ {result}")
            else:
                model = get_model_by_id(model_name)
                if model:
                    params_text = f" ({model.parameters})" if model.parameters != "Unknown" else ""
                    ctx = format_context_limit(model.context_limit)
                    await message.answer(
                        f"✅ **Модель изменена:**\n\n"
                        f"📝 {model.name}{params_text}\n"
                        f"📊 Контекст: {ctx}\n"
                        f"🔗 `{model.model_id}`",
                        parse_mode="Markdown",
                    )
                else:
                    await message.answer(f"✅ Команда выполнена.\n\n{result}")
            return

        keyboard = [
            [InlineKeyboardButton(text="🆓 Free Models", callback_data="model_filter:free")],
            [InlineKeyboardButton(text="📌 OpenCode", callback_data="model_provider:opencode")],
            [InlineKeyboardButton(text="🔷 Google", callback_data="model_provider:google")],
            [InlineKeyboardButton(text="🟢 OpenAI", callback_data="model_provider:openai")],
            [InlineKeyboardButton(text="🟣 OpenRouter", callback_data="model_provider:openrouter")],
            [InlineKeyboardButton(text="📋 Все модели", callback_data="model_filter:all")],
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await message.answer("🧠 **Выберите провайдер моделей:**", reply_markup=markup, parse_mode="Markdown")

    @dp.message(Command("stats"))
    async def cmd_stats(message: Message) -> None:
        user_id = message.from_user.id
        if not _check_rate_limit(user_id) and not is_admin(user_id):
            await message.answer("⏳ Слишком много запросов. Подождите.")
            return
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён.")
            return
        typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
        try:
            result = await bridge.ask_agent(user_id, "stats")
        finally:
            typing_task.cancel()
        await _send(message, result, EMOJI_MAP)

    @dp.message(Command("version"))
    async def cmd_version(message: Message) -> None:
        result = await get_opencode_version()
        await message.answer(result)

    @dp.message(Command("admin"))
    async def cmd_admin(message: Message) -> None:
        user_id = message.from_user.id
        if not is_admin(user_id):
            await message.answer("❌ У вас нет прав для этой команды.")
            return
        lines = [
            "🔒 **Панель администратора**\n",
            f"👤 Подключённые агенты: {bridge.get_connected_count()}",
            f"💬 Активных сессий: {len(session_manager.get_all_active_users())}",
        ]
        await _send(message, "\n".join(lines), EMOJI_MAP)

    @dp.message(Command("broadcast"))
    async def cmd_broadcast(message: Message) -> None:
        user_id = message.from_user.id
        if not is_admin(user_id):
            await message.answer("❌ У вас нет прав для этой команды.")
            return
        args = message.text.split(maxsplit=1)
        if len(args) < 2 or not args[1].strip():
            await message.answer("❌ Использование: /broadcast <текст>")
            return
        text = args[1].strip()
        active_users = session_manager.get_all_active_users()
        if not active_users:
            await message.answer("ℹ️ Нет активных пользователей для рассылки.")
            return
        sent = 0
        for uid in active_users:
            try:
                await message.bot.send_message(uid, f"📢 **Рассылка:**\n\n{text}", parse_mode="Markdown")
                sent += 1
            except Exception:
                pass
        await message.answer(f"✅ Разослано {sent} из {len(active_users)} пользователям.")

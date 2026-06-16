# Telegram OpenCode Bot Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all bugs, unify agent protocol, add error/confirmation to every command, add admin tools, rate limiting, and refactor into modular structure.

**Architecture:** Monolithic `bot.py` (1121 lines) split into `handlers/`, `services/`, `utils/` modules. Two incompatible agent protocols unified into single long-polling protocol. Every command validated and returns clear success/error.

**Tech Stack:** Python 3.10+, aiogram 3.x, aiohttp, python-dotenv

---

### Task 1: Create `utils/logger.py`

**Files:**
- Create: `E:/tg opencode bot/utils/__init__.py`
- Create: `E:/tg opencode bot/utils/logger.py`

- [ ] **Step 1: Create `utils/__init__.py`** (empty file)

```
```

- [ ] **Step 2: Create `utils/logger.py`**

```python
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = LOG_DIR / "bot.log"


class PollFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "/agent/poll" in msg or "/agent/response" in msg or "/agent/register" in msg:
            return False
        return True


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        str(LOG_FILE), maxBytes=5_000_000, backupCount=2, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    aiohttp_logger = logging.getLogger("aiohttp.access")
    aiohttp_logger.addFilter(PollFilter())
    aiohttp_logger.setLevel(logging.INFO)
```

---

### Task 2: Create `utils/formatter.py`

**Files:**
- Create: `E:/tg opencode bot/utils/formatter.py`

Extract formatting logic from existing `bot.py:412-491`:

- `_format_code(text: str) -> str` — convert markdown code fences to HTML
- `_replace_emoji(text: str, emoji_map: dict) -> str` — replace emoji with tg-emoji tags
- `_split_text(text: str, max_length: int = 4000) -> list[str]` — split long text at boundaries
- `_encode_model_id(model_id: str, hash_map: dict) -> str` — encode model ID for callback data
- `_decode_model_id(encoded: str, hash_map: dict) -> str` — decode model ID from callback data
- `_send(message: types.Message, text: str, emoji_map: dict) -> None` — send HTML formatted response
- `_is_limit_error(response: str) -> bool` — check if response contains context limit error
- `_typing_loop(bot: Bot, chat_id: int, interval: float = 4.0) -> None` — typing indicator loop

- [ ] **Step 1: Create `utils/formatter.py`** with all formatting functions

```python
import hashlib
import html
import logging
import re
from asyncio import CancelledError, sleep, create_task

from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)


def _format_code(text: str) -> str:
    text = re.sub(r'```(\w*)\n', r'<pre><code class="language-\1">', text)
    text = text.replace("```", "</code></pre>")
    text = re.sub(r'`([^`]+)`', r"<code>\1</code>", text)
    return text


def _replace_emoji(text: str, emoji_map: dict[str, str]) -> str:
    if not emoji_map:
        return text
    result: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        best_len = 0
        best_id = None
        for l in range(min(6, n - i), 0, -1):
            chunk = text[i : i + l]
            if chunk in emoji_map:
                best_len = l
                best_id = emoji_map[chunk]
                break
        if best_len:
            chunk = text[i : i + best_len]
            result.append(f'<tg-emoji emoji-id="{best_id}">{chunk}</tg-emoji>')
            i += best_len
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def _split_text(text: str, max_length: int = 4000) -> list[str]:
    if len(text) <= max_length:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(" ", 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n").lstrip()
    return chunks


def _encode_model_id(model_id: str, hash_map: dict[str, str]) -> str:
    encoded = model_id.replace("/", ".").replace(":", "_")
    if len(encoded) > 60:
        short_hash = hashlib.md5(model_id.encode()).hexdigest()[:8]
        encoded = f"m.{short_hash}"
        hash_map[encoded] = model_id
    return encoded


def _decode_model_id(encoded: str, hash_map: dict[str, str]) -> str:
    if encoded in hash_map:
        return hash_map[encoded]
    return encoded.replace(".", "/").replace("_", ":")


async def _typing_loop(bot: Bot, chat_id: int, interval: float = 4.0) -> None:
    try:
        while True:
            await bot.send_chat_action(chat_id, "typing")
            await sleep(interval)
    except CancelledError:
        pass


def _is_limit_error(response: str) -> bool:
    lower = response.lower()
    clues = [
        "token limit", "context length", "maximum context", "too many tokens",
        "limit reached", "context window", "max_tokens", "token budget",
        "слишком длинный", "превышен лимит", "контекст", "токенов",
    ]
    return any(c in lower for c in clues)


async def _send(message: Message, text: str, emoji_map: dict[str, str] | None = None) -> None:
    text = html.escape(text)
    text = text.replace("&lt;pre&gt;", "<pre>").replace("&lt;/pre&gt;", "</pre>")
    text = text.replace("&lt;code&gt;", "<code>").replace("&lt;/code&gt;", "</code>")
    text = _format_code(text)
    if emoji_map:
        text = _replace_emoji(text, emoji_map)
    for chunk in _split_text(text, 4000):
        await message.answer(chunk, parse_mode="HTML")
```

---

### Task 3: Update `config.py` — add ADMIN_IDS and helper

**Files:**
- Modify: `E:/tg opencode bot/config.py`

Add `ADMIN_IDS` list and `is_admin()` function.

- [ ] **Step 1: Modify `config.py`**

```python
"""Configuration module. Loads settings from .env file. Interactive setup on first run."""

import os
from pathlib import Path

from dotenv import load_dotenv, set_key

ENV_PATH = Path(__file__).parent / ".env"

load_dotenv(ENV_PATH)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OPENCODE_WORK_DIR: str = os.getenv("OPENCODE_WORK_DIR", str(Path.cwd()))
OPENCODE_BIN_PATH: str = os.getenv("OPENCODE_BIN_PATH", "")
GOOGLE_STT_LANGUAGE: str = os.getenv("GOOGLE_STT_LANGUAGE", "ru-RU")
AGENTS_DB_PATH: str = os.getenv("AGENTS_DB_PATH", str(Path(__file__).parent / "connected_agents.json"))

ADMIN_IDS_RAW: str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = []
for part in ADMIN_IDS_RAW.split(","):
    part = part.strip()
    if part:
        try:
            ADMIN_IDS.append(int(part))
        except ValueError:
            pass

RATE_LIMIT_PER_MINUTE: int = 10


def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS:
        return True
    return user_id in ADMIN_IDS


def _setup_wizard() -> None:
    global BOT_TOKEN

    print("\n" + "=" * 50)
    print("  First run setup")
    print("=" * 50)

    if not BOT_TOKEN:
        print("\nTo create a bot, message @BotFather in Telegram.")
        token = input("Enter BOT_TOKEN: ").strip()
        if not token:
            print("Error: BOT_TOKEN is required.")
            exit(1)
        set_key(str(ENV_PATH), "BOT_TOKEN", token)
        BOT_TOKEN = token

    print("\n" + "=" * 50)
    print("  Setup complete! Starting bot...")
    print("=" * 50 + "\n")


def validate_config() -> None:
    global BOT_TOKEN

    if not BOT_TOKEN:
        _setup_wizard()

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set")
```

---

### Task 4: Create `services/session_manager.py`

**Files:**
- Create: `E:/tg opencode bot/services/__init__.py`
- Create: `E:/tg opencode bot/services/session_manager.py`

Extract session/context management from `bot.py:75-144` with `.bak` corruption handling.

- [ ] **Step 1: Create `services/__init__.py`** (empty)

```
```

- [ ] **Step 2: Create `services/session_manager.py`**

```python
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SESSIONS_FILE = Path(__file__).resolve().parent.parent / "user_sessions.json"
CONTEXTS_FILE = Path(__file__).resolve().parent.parent / "user_contexts.json"


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[int, bool] = {}
        self._contexts: dict[int, str] = {}
        self._load_sessions()
        self._load_contexts()

    # --- Sessions ---

    def _load_sessions(self) -> None:
        if not SESSIONS_FILE.exists():
            self._sessions = {}
            return
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._sessions = {int(k): bool(v) for k, v in raw.items()}
            logger.info("Loaded %d user sessions", len(self._sessions))
        except Exception as e:
            self._backup_corrupted(SESSIONS_FILE)
            logger.warning("Failed to load sessions, reset: %s", e)
            self._sessions = {}

    def _save_sessions(self) -> None:
        try:
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("Failed to save sessions: %s", e)

    def has_session(self, user_id: int) -> bool:
        return self._sessions.get(user_id, False)

    def mark_session_started(self, user_id: int) -> None:
        self._sessions[user_id] = True
        self._save_sessions()

    def reset_session(self, user_id: int) -> None:
        self._sessions[user_id] = False
        self._save_sessions()

    def delete_session(self, user_id: int) -> bool:
        if user_id in self._sessions:
            del self._sessions[user_id]
            self._save_sessions()
            return True
        return False

    def delete_all_sessions(self, user_id: int) -> bool:
        removed = False
        for uid in list(self._sessions.keys()):
            if uid == user_id or user_id == 0:
                del self._sessions[uid]
                removed = True
        if removed:
            self._save_sessions()
        return removed

    # --- Contexts ---

    def _load_contexts(self) -> None:
        if not CONTEXTS_FILE.exists():
            self._contexts = {}
            return
        try:
            with open(CONTEXTS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._contexts = {int(k): str(v) for k, v in raw.items()}
            logger.info("Loaded %d user contexts", len(self._contexts))
        except Exception as e:
            self._backup_corrupted(CONTEXTS_FILE)
            logger.warning("Failed to load contexts, reset: %s", e)
            self._contexts = {}

    def _save_contexts(self) -> None:
        try:
            with open(CONTEXTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._contexts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("Failed to save contexts: %s", e)

    def get_context(self, user_id: int) -> str:
        return self._contexts.get(user_id, "")

    def set_context(self, user_id: int, text: str) -> None:
        if text:
            self._contexts[user_id] = text
        else:
            self._contexts.pop(user_id, None)
        self._save_contexts()

    def delete_context(self, user_id: int) -> bool:
        if user_id in self._contexts:
            del self._contexts[user_id]
            self._save_contexts()
            return True
        return False

    # --- Helpers ---

    @staticmethod
    def _backup_corrupted(path: Path) -> None:
        try:
            bak = path.with_suffix(path.suffix + ".bak")
            path.rename(bak)
            logger.info("Backed up corrupted %s to %s", path.name, bak.name)
        except Exception:
            pass

    def get_all_active_users(self) -> list[int]:
        return [uid for uid, active in self._sessions.items() if active]

    def get_connected_user_ids(self) -> set[int]:
        return {uid for uid, active in self._sessions.items() if active}
```

---

### Task 5: Create `services/opencode_runner.py`

**Files:**
- Create: `E:/tg opencode bot/services/opencode_runner.py`

Direct opencode execution for local commands (version check).

- [ ] **Step 1: Create `services/opencode_runner.py`**

```python
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
```

---

### Task 6: Create `services/agent_bridge.py`

**Files:**
- Create: `E:/tg opencode bot/services/agent_bridge.py`

HTTP server routes + ask_agent() + file handling.

- [ ] **Step 1: Create `services/agent_bridge.py`**

```python
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
```

---

### Task 7: Create `handlers/commands.py`

**Files:**
- Create: `E:/tg opencode bot/handlers/__init__.py`
- Create: `E:/tg opencode bot/handlers/commands.py`

All command handlers with validation, error handling, and rate limiting.

- [ ] **Step 1: Create `handlers/__init__.py`** (empty)

```
```

- [ ] **Step 2: Create `handlers/commands.py`**

```python
import asyncio
import logging
import secrets
from collections import deque
from pathlib import Path
from time import time

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BOT_TOKEN, is_admin, RATE_LIMIT_PER_MINUTE
from models_db import (
    MODELS_DB, get_model_by_id, format_context_limit,
    search_models, get_models_by_provider, format_capabilities,
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


def setup_handlers(dp: Dispatcher, bridge: AgentBridge, session_manager: SessionManager) -> None:
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

        models_list = MODELS_DB
        lines = [f"📋 **Все модели ({len(models_list)}):**\n"]
        for m in models_list[:30]:
            caps = format_capabilities(m)
            ctx = format_context_limit(m.context_limit)
            name_short = m.model_id.replace("openrouter/", "").replace("opencode/", "")
            lines.append(f"{caps} `{name_short}` — {ctx}")
        if len(models_list) > 30:
            lines.append(f"\n*... и ещё {len(models_list) - 30} моделей. Используйте /models <поиск> для поиска.*")
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


def _generate_agent_py(user_id: str, token: str) -> str:
    return f'''"""OpenCode Agent — auto-generated. Connects to bot via long-polling."""
import asyncio, json, logging, shutil, sys, tempfile, pathlib, secrets
import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agent")

OPENCODE_BIN = shutil.which("opencode") or "opencode"
OPENCODE_TIMEOUT = 300
BOT_URL = "http://127.0.0.1:8080"
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
            ps_cmd = f\'Get-Content "${{msg_file}}" -Raw | & "${{OPENCODE_BIN}}" run --dangerously-skip-permissions\'
            if continue_session:
                ps_cmd += " --continue"
            if file_urls:
                dest = tempfile.mkdtemp(prefix="oc_files_")
                for url in file_urls:
                    local = await download_file(url, dest)
                    ps_cmd += f\' -f "${{local}}"\'
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
```

---

### Task 8: Create `handlers/messages.py`

**Files:**
- Create: `E:/tg opencode bot/handlers/messages.py`

Text, voice, photo, video, document handlers.

- [ ] **Step 1: Create `handlers/messages.py`**

```python
import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message
from aiogram import F

from config import GOOGLE_STT_LANGUAGE, is_admin, RATE_LIMIT_PER_MINUTE
from services.agent_bridge import AgentBridge
from services.session_manager import SessionManager
from utils.formatter import _send, _typing_loop, _is_limit_error, _split_text

logger = logging.getLogger(__name__)

router = Router()

FILES_DIR = Path(__file__).resolve().parent.parent / "bot_files"


def setup_message_handlers(dp: Dispatcher, bridge: AgentBridge, session_manager: SessionManager) -> None:
    dp.include_router(router)

    @dp.message(F.text)
    async def handle_text(message: Message) -> None:
        text = message.text
        if not text or text.startswith("/"):
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        if message.reply_to_message and message.reply_to_message.text:
            text = f"[Ответ на сообщение]: {message.reply_to_message.text}\n\n[Мой вопрос]: {text}"

        has_session = session_manager.has_session(user_id)
        ctx = session_manager.get_context(user_id)

        typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
        try:
            if not has_session and ctx:
                await bridge.ask_agent(user_id, ctx, continue_session=False)
                session_manager.mark_session_started(user_id)
                response = await bridge.ask_agent(user_id, text, continue_session=True)
            else:
                response = await bridge.ask_agent(user_id, text, continue_session=has_session)
                if not has_session:
                    session_manager.mark_session_started(user_id)

            if _is_limit_error(response):
                summary = await bridge.ask_agent(
                    user_id,
                    f"Суммаризируй диалог кратко, выделив суть. Вот последнее сообщение пользователя: {text}",
                    continue_session=True,
                )
                session_manager.reset_session(user_id)
                ctx_text = f"[Сжатый контекст предыдущего диалога]: {summary}\n\n[Новый вопрос]: {text}"
                response = await bridge.ask_agent(user_id, ctx_text, continue_session=False)
                session_manager.mark_session_started(user_id)
        finally:
            typing_task.cancel()

        await _send(message, response)

    @dp.message(F.voice)
    async def handle_voice(message: Message) -> None:
        if not message.voice:
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        await message.bot.send_chat_action(message.chat.id, "record_voice")
        try:
            from stt import process_voice

            text = await process_voice(
                file_id=message.voice.file_id,
                bot=message.bot,
                language=GOOGLE_STT_LANGUAGE,
            )
            if not text:
                await message.answer("🎤 Не удалось распознать голосовое сообщение.")
                return
            await message.answer(f"🎤 Распознано: {text}")

            has_session = session_manager.has_session(user_id)
            ctx = session_manager.get_context(user_id)

            typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
            try:
                if not has_session and ctx:
                    await bridge.ask_agent(user_id, ctx, continue_session=False)
                    session_manager.mark_session_started(user_id)
                    response = await bridge.ask_agent(user_id, text, continue_session=True)
                else:
                    response = await bridge.ask_agent(user_id, text, continue_session=has_session)
                    if not has_session:
                        session_manager.mark_session_started(user_id)
            finally:
                typing_task.cancel()
            await _send(message, response)
        except Exception as e:
            logger.exception("Error processing voice")
            await message.answer(f"❌ Ошибка: {e}")

    async def _download_tg_file(bot: Bot, file_id: str, ext: str = "") -> str:
        file_info = await bot.get_file(file_id)
        suffix = ext or Path(file_info.file_path).suffix
        local_name = f"{file_id}{suffix}"
        local_path = FILES_DIR / local_name
        await bot.download_file(file_info.file_path, destination=str(local_path))
        return local_name

    async def _process_media(
        message: Message,
        file_id: str,
        ext: str,
        media_type: str,
        bridge: AgentBridge,
        session_manager: SessionManager,
    ) -> None:
        user_id = message.from_user.id
        caption = message.caption or ""

        has_session = session_manager.has_session(user_id)
        ctx = session_manager.get_context(user_id)

        local_name = await _download_tg_file(message.bot, file_id, ext)
        server_host = "127.0.0.1"
        file_url = f"http://{server_host}:8080/files/{local_name}"
        text = f"[{media_type}: {file_url}]\n{caption}" if caption else f"[{media_type}: {file_url}]"

        typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
        try:
            try:
                if not has_session and ctx:
                    await bridge.ask_agent(user_id, ctx, continue_session=False)
                    session_manager.mark_session_started(user_id)
                    response = await bridge.ask_agent(user_id, text, continue_session=True, files=[file_url])
                else:
                    response = await bridge.ask_agent(user_id, text, continue_session=has_session, files=[file_url])
                    if not has_session:
                        session_manager.mark_session_started(user_id)
            except Exception as e:
                err = str(e).lower()
                if "does not support image" in err or "image input" in err:
                    fallback = f"[{media_type} not supported by model]\n{caption}" if caption else f"[{media_type} not supported by model]"
                    if not has_session and ctx:
                        await bridge.ask_agent(user_id, ctx, continue_session=False)
                        session_manager.mark_session_started(user_id)
                        response = await bridge.ask_agent(user_id, fallback, continue_session=True)
                    else:
                        response = await bridge.ask_agent(user_id, fallback, continue_session=has_session)
                        if not has_session:
                            session_manager.mark_session_started(user_id)
                else:
                    raise
            await _send(message, response)
        except Exception as e:
            if "does not support image" not in str(e).lower() and "image input" not in str(e).lower():
                logger.exception("Error processing %s", media_type)
                await message.answer(f"❌ Ошибка: {e}")
        finally:
            typing_task.cancel()

    @dp.message(F.photo)
    async def handle_photo(message: Message) -> None:
        if not message.photo:
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        photo = message.photo[-1]
        await _process_media(message, photo.file_id, ".jpg", "Image", bridge, session_manager)

    @dp.message(F.video)
    async def handle_video(message: Message) -> None:
        if not message.video:
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        await _process_media(message, message.video.file_id, ".mp4", "Video", bridge, session_manager)

    @dp.message(F.document)
    async def handle_document(message: Message) -> None:
        if not message.document:
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        await _process_media(message, message.document.file_id, "", "File", bridge, session_manager)
```

---

### Task 9: Create `handlers/callbacks.py`

**Files:**
- Create: `E:/tg opencode bot/handlers/callbacks.py`

Inline keyboard callbacks for model selection (extracted from `bot.py:648-828`).

- [ ] **Step 1: Create `handlers/callbacks.py`**

```python
import asyncio
import logging

from aiogram import Dispatcher, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import F

from models_db import MODELS_DB, get_model_by_id, format_context_limit, format_capabilities, get_models_by_provider, get_free_models
from services.agent_bridge import AgentBridge
from utils.formatter import _encode_model_id, _decode_model_id, _typing_loop

logger = logging.getLogger(__name__)

router = Router()
_model_hash_map: dict[str, str] = {}


def setup_callbacks(dp: Dispatcher, bridge: AgentBridge) -> None:
    dp.include_router(router)

    @dp.callback_query(F.data.startswith("model_filter:"))
    async def callback_model_filter(callback: CallbackQuery) -> None:
        data = callback.data.split(":")
        filter_type = data[1]
        page = int(data[2]) if len(data) > 2 else 0
        await callback.answer()

        if filter_type == "free":
            models = get_free_models()
            title = "🆓 **Бесплатные модели:**"
        else:
            models = MODELS_DB
            title = "📋 **Все модели:**"

        per_page = 25
        total_pages = (len(models) + per_page - 1) // per_page
        start = page * per_page
        end = min(start + per_page, len(models))
        page_models = models[start:end]

        keyboard: list[list[InlineKeyboardButton]] = []
        for model in page_models:
            params_text = f" ({model.parameters})" if model.parameters != "Unknown" else ""
            context_text = format_context_limit(model.context_limit)
            caps = format_capabilities(model)
            button_text = f"{caps} {model.name}{params_text} [{context_text}]"
            encoded = _encode_model_id(model.model_id, _model_hash_map)
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"model:{encoded}")])

        nav_row: list[InlineKeyboardButton] = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"model_filter:{filter_type}:{page-1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="model_noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"model_filter:{filter_type}:{page+1}"))
        keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton(text="🏠 Меню", callback_data="model_back")])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            f"{title} (стр. {page+1}/{total_pages})",
            reply_markup=markup,
            parse_mode="Markdown",
        )

    @dp.callback_query(F.data.startswith("model_provider:"))
    async def callback_model_provider(callback: CallbackQuery) -> None:
        data = callback.data.split(":")
        provider = data[1]
        page = int(data[2]) if len(data) > 2 else 0
        await callback.answer()

        models = get_models_by_provider(provider)
        provider_names = {
            "opencode": "📌 OpenCode",
            "google": "🔷 Google",
            "openai": "🟢 OpenAI",
            "openrouter": "🟣 OpenRouter",
        }
        title = f"{provider_names.get(provider, provider)} **модели:**"

        per_page = 25
        total_pages = (len(models) + per_page - 1) // per_page
        start = page * per_page
        end = min(start + per_page, len(models))
        page_models = models[start:end]

        keyboard: list[list[InlineKeyboardButton]] = []
        for model in page_models:
            params_text = f" ({model.parameters})" if model.parameters != "Unknown" else ""
            context_text = format_context_limit(model.context_limit)
            caps = format_capabilities(model)
            button_text = f"{caps} {model.name}{params_text} [{context_text}]"
            encoded = _encode_model_id(model.model_id, _model_hash_map)
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"model:{encoded}")])

        nav_row: list[InlineKeyboardButton] = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"model_provider:{provider}:{page-1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="model_noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"model_provider:{provider}:{page+1}"))
        keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton(text="🏠 Меню", callback_data="model_back")])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            f"{title} (стр. {page+1}/{total_pages})",
            reply_markup=markup,
            parse_mode="Markdown",
        )

    @dp.callback_query(F.data == "model_noop")
    async def callback_model_noop(callback: CallbackQuery) -> None:
        await callback.answer()

    @dp.callback_query(F.data == "model_back")
    async def callback_model_back(callback: CallbackQuery) -> None:
        await callback.answer()
        keyboard = [
            [InlineKeyboardButton(text="🆓 Free Models", callback_data="model_filter:free")],
            [InlineKeyboardButton(text="📌 OpenCode", callback_data="model_provider:opencode")],
            [InlineKeyboardButton(text="🔷 Google", callback_data="model_provider:google")],
            [InlineKeyboardButton(text="🟢 OpenAI", callback_data="model_provider:openai")],
            [InlineKeyboardButton(text="🟣 OpenRouter", callback_data="model_provider:openrouter")],
            [InlineKeyboardButton(text="📋 Все модели", callback_data="model_filter:all")],
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "🧠 **Выберите провайдер моделей:**",
            reply_markup=markup,
            parse_mode="Markdown",
        )

    @dp.callback_query(F.data.startswith("model:"))
    async def callback_model_select(callback: CallbackQuery) -> None:
        encoded_id = callback.data.split(":", 1)[1]
        model_id = _decode_model_id(encoded_id, _model_hash_map)
        model = get_model_by_id(model_id)

        if not model:
            await callback.answer("❌ Модель не найдена.", show_alert=True)
            return

        user_id = callback.from_user.id
        if not bridge.is_connected(user_id):
            await callback.answer("❌ ПК не подключён.", show_alert=True)
            return

        await callback.answer()

        typing_task = asyncio.create_task(_typing_loop(callback.message.bot, callback.message.chat.id))
        try:
            result = await bridge.ask_agent(user_id, f"config set model {model_id}")
        finally:
            typing_task.cancel()

        params_text = f" ({model.parameters})" if model.parameters != "Unknown" else ""
        context_text = format_context_limit(model.context_limit)

        caps_list = []
        if model.supports_text:
            caps_list.append("📝 Текст")
        if model.supports_image:
            caps_list.append("🖼 Изображения")
        if model.supports_video:
            caps_list.append("🎬 Видео")
        if model.supports_file:
            caps_list.append("📁 Файлы")
        caps_text = "\n".join(caps_list) if caps_list else "❌ Нет"

        await callback.message.answer(
            f"✅ **Модель изменена:**\n\n"
            f"📝 Название: {model.name}{params_text}\n"
            f"📊 Контекст: {context_text}\n"
            f"🔗 ID: `{model_id}`\n\n"
            f"**Возможности:**\n{caps_text}\n\n"
            f"```\n{result}\n```",
            parse_mode="Markdown",
        )
```

---

### Task 10: Rewrite `bot.py` (entry point)

**Files:**
- Modify: `E:/tg opencode bot/bot.py`

Rewrite as thin entry point.

- [ ] **Step 1: Rewrite `bot.py`**

```python
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
```

---

### Task 11: Rewrite `agent.py` (manual agent)

**Files:**
- Modify: `E:/tg opencode bot/agent.py`

Rewrite to use the unified long-polling protocol.

- [ ] **Step 1: Rewrite `agent.py`**

```python
"""OpenCode Agent — connects to bot via long-polling.
Usage:
    python agent.py --bot-host HOST --bot-port PORT --user-id ID --token TOKEN
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenCode Agent")
    parser.add_argument("--bot-host", type=str, default="127.0.0.1", help="Bot HTTP server host")
    parser.add_argument("--bot-port", type=int, default=8080, help="Bot HTTP server port")
    parser.add_argument("--user-id", type=str, required=True, help="Your Telegram user ID")
    parser.add_argument("--token", type=str, default="", help="Authorization token (auto-generated if empty)")
    parser.add_argument("--work-dir", type=str, default=str(Path.cwd()), help="Working directory for opencode")
    return parser.parse_args()


async def download_file(url: str, dest_dir: str) -> str:
    fname = url.rsplit("/", 1)[-1].split("?")[0] or "file"
    fpath = str(Path(dest_dir) / fname)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            with open(fpath, "wb") as f:
                while chunk := await resp.content.read(8192):
                    f.write(chunk)
    return fpath


async def run_opencode(message: str, work_dir: str, session_id: str = "", file_urls: list[str] | None = None) -> str:
    try:
        cmd = [OPENCODE_BIN, "run", message, "--dir", work_dir, "--dangerously-skip-permissions"]
        if session_id:
            cmd.extend(["--session", session_id])
        if file_urls:
            dest = tempfile.mkdtemp(prefix="oc_files_")
            for url in file_urls:
                local = await download_file(url, dest)
                cmd.extend(["-f", local])

        logger.info("Running opencode: %s ...", cmd[:3])
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=OPENCODE_TIMEOUT)
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        if process.returncode != 0:
            return f"Ошибка OpenCode (код {process.returncode}): {stderr_text[:500]}"

        return stdout_text or "OpenCode не вернул ответ."

    except asyncio.TimeoutError:
        return f"Таймаут OpenCode ({OPENCODE_TIMEOUT} сек)."
    except FileNotFoundError:
        return "OpenCode не найден. Установите: pip install opencode"
    except Exception as e:
        logger.exception("Error running opencode")
        return f"Ошибка: {e}"


async def poll_forever(bot_url: str, user_id: str, token: str, work_dir: str) -> None:
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.post(
                    f"{bot_url}/agent/poll",
                    json={"user_id": user_id, "token": token},
                    timeout=aiohttp.ClientTimeout(total=35),
                ) as resp:
                    data = await resp.json()

                    if data.get("cmd") == "run":
                        message = data.get("message", "")
                        session_id = data.get("session_id", "")
                        files = data.get("files")
                        request_id = data.get("request_id", "")

                        result = await run_opencode(message, work_dir, session_id, files)

                        await session.post(
                            f"{bot_url}/agent/response",
                            json={
                                "user_id": user_id,
                                "token": token,
                                "request_id": request_id,
                                "result": result,
                            },
                            timeout=aiohttp.ClientTimeout(total=5),
                        )
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.warning("Poll error: %s", e)
                await asyncio.sleep(5)


def main() -> None:
    args = parse_args()
    auth_token = args.token or secrets.token_hex(16)
    bot_url = f"http://{args.bot_host}:{args.bot_port}"

    print(f"\n{'='*50}")
    print(f"  OpenCode Agent")
    print(f"{'='*50}")
    print(f"  Bot URL:    {bot_url}")
    print(f"  User ID:    {args.user_id}")
    print(f"  Token:      {auth_token}")
    print(f"  Work dir:   {args.work_dir}")
    print(f"{'='*50}\n")

    asyncio.run(run(bot_url, args.user_id, auth_token, args.work_dir))


async def run(bot_url: str, user_id: str, token: str, work_dir: str) -> None:
    print("Registering with bot...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{bot_url}/agent/register",
                json={"user_id": user_id, "token": token},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    print(f"Registration failed: {data.get('error', 'unknown')}")
                    return
        except Exception as e:
            print(f"Failed to connect to bot: {e}")
            return

    print("Registered! Polling for commands...")
    await poll_forever(bot_url, user_id, token, work_dir)


if __name__ == "__main__":
    main()
```

---

### Task 12: Self-review of plan

- [ ] **Step 1: Verify spec coverage by plan**
  - Architecture split into modules → Task 1-10 cover all files
  - Unified agent protocol → Tasks 6, 7 (_generate_agent_py), 11
  - Every command with confirmation/error → Task 7 (commands.py)
  - Rate limiting (10/min) → Task 7 (commands.py, _check_rate_limit)
  - Admin commands → Task 7 (cmd_admin, cmd_broadcast)
  - Session corruption handling → Task 4 (SessionManager._backup_corrupted)
  - Logging suppression → Task 1 (PollFilter)

- [ ] **Step 2: Check for placeholders** — None found.

- [ ] **Step 3: Verify type/signature consistency**
  - `_encode_model_id(model_id, hash_map)` — signature matches throughout
  - `bridge.ask_agent(user_id, message, ...)` — consistent across handlers
  - `bridge.is_connected(user_id)` — returns bool, consistent usage
  - `session_manager.get_context(user_id)` — returns str, consistent
  - All callback_data prefixes match between commands.py and callbacks.py

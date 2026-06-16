# Telegram Bot for OpenCode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram bot that bridges a smartphone with the opencode CLI, supporting text and voice messages.

**Architecture:** Modular Python bot using aiogram 3.x. Each module handles one concern: config, opencode interaction, speech-to-text, and Telegram handlers. Communication with opencode via `opencode run --format json` subprocess calls.

**Tech Stack:** Python 3.10+, aiogram 3.x, python-dotenv, pydub, SpeechRecognition, FFmpeg

---

## File Structure

```
tg opencode bot/
├── bot.py              # Entry point, Telegram handlers
├── opencode_client.py  # OpenCode interaction via subprocess
├── stt.py              # Voice download + conversion + transcription
├── config.py           # Configuration from .env
├── requirements.txt    # Dependencies
└── .env                # Secrets (not committed)
```

---

### Task 1: Create config.py — Configuration Module

**Files:**
- Create: `E:\tg opencode bot\config.py`

- [ ] **Step 1: Create config.py with environment variable loading**

```python
"""Configuration module. Loads settings from .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(Path(__file__).parent / ".env")

# Telegram bot token from @BotFather
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Telegram user ID — only this user can interact with the bot
ALLOWED_USER_ID: int = int(os.getenv("ALLOWED_USER_ID", "0"))

# Working directory for opencode (default: current directory)
OPENCODE_WORK_DIR: str = os.getenv("OPENCODE_WORK_DIR", str(Path.cwd()))

# Google STT language code (default: Russian)
GOOGLE_STT_LANGUAGE: str = os.getenv("GOOGLE_STT_LANGUAGE", "ru-RU")


def validate_config() -> None:
    """Validate that required configuration variables are set."""
    errors = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is not set in .env")
    if ALLOWED_USER_ID == 0:
        errors.append("ALLOWED_USER_ID is not set in .env")
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))
```

- [ ] **Step 2: Verify config.py loads correctly**

Run: `python -c "import config; print('BOT_TOKEN:', bool(config.BOT_TOKEN)); print('USER_ID:', config.ALLOWED_USER_ID)"`
Expected: Shows False/0 (no .env yet), no import errors

---

### Task 2: Create .env and requirements.txt

**Files:**
- Create: `E:\tg opencode bot\.env`
- Create: `E:\tg opencode bot\requirements.txt`

- [ ] **Step 1: Create .env template**

```
# Telegram Bot Token from @BotFather
BOT_TOKEN=your_bot_token_here

# Your Telegram user ID (get it from @userinfobot)
ALLOWED_USER_ID=123456789

# Working directory for opencode (optional, defaults to current dir)
# OPENCODE_WORK_DIR=E:\projects

# Google STT language (optional, defaults to ru-RU)
# GOOGLE_STT_LANGUAGE=ru-RU
```

- [ ] **Step 2: Create requirements.txt**

```
aiogram>=3.0
python-dotenv
pydub
SpeechRecognition
```

- [ ] **Step 3: Install Python dependencies**

Run: `pip install -r "E:\tg opencode bot\requirements.txt"`
Expected: All packages install successfully

---

### Task 3: Create opencode_client.py — OpenCode Interaction

**Files:**
- Create: `E:\tg opencode bot\opencode_client.py`

- [ ] **Step 1: Create opencode_client.py**

```python
"""OpenCode client module. Sends messages to opencode and returns responses."""

import asyncio
import json
import logging
from pathlib import Path

from config import OPENCODE_WORK_DIR

logger = logging.getLogger(__name__)

# Timeout for opencode response (seconds)
OPENCODE_TIMEOUT = 120


async def ask_opencode(message: str) -> str:
    """
    Send a message to opencode and return the response.

    Args:
        message: The text message to send to opencode.

    Returns:
        The response text from opencode, or an error message.
    """
    if not message.strip():
        return "Пустое сообщение не может быть обработано."

    try:
        # Build command: opencode run "message" --format json --dir "work_dir"
        cmd = [
            "opencode", "run", message,
            "--format", "json",
            "--dir", OPENCODE_WORK_DIR,
        ]

        logger.info("Running opencode: %s", cmd[0:3])

        # Start subprocess with timeout
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for output with timeout
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=OPENCODE_TIMEOUT,
        )

        # Decode output
        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        if process.returncode != 0:
            logger.error("OpenCode error (code %d): %s", process.returncode, stderr_text)
            return f"Ошибка OpenCode (код {process.returncode}): {stderr_text[:500]}"

        # Parse JSON-lines output
        response_parts = []
        for line in stdout_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("type") == "text":
                    text = event.get("part", {}).get("text", "")
                    if text:
                        response_parts.append(text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON line: %s", line[:100])

        if response_parts:
            return "".join(response_parts)

        # If no text events found, return raw output
        return stdout_text.strip() or "OpenCode не вернул ответ."

    except asyncio.TimeoutError:
        logger.error("OpenCode timed out after %d seconds", OPENCODE_TIMEOUT)
        return f"OpenCode не ответил вовремя (таймаут {OPENCODE_TIMEOUT} сек)."
    except FileNotFoundError:
        return "OpenCode не найден. Убедитесь, что opencode установлен и доступен в PATH."
    except Exception as e:
        logger.exception("Unexpected error in ask_opencode")
        return f"Неожиданная ошибка: {e}"
```

- [ ] **Step 2: Verify opencode_client.py imports correctly**

Run: `python -c "from opencode_client import ask_opencode; print('OK')"`
Expected: Prints "OK" with no errors

---

### Task 4: Create stt.py — Speech-to-Text Module

**Files:**
- Create: `E:\tg opencode bot\stt.py`

- [ ] **Step 1: Create stt.py**

```python
"""Speech-to-Text module. Downloads voice messages, converts, and transcribes."""

import logging
import tempfile
from pathlib import Path

from pydub import AudioSegment
import speech_recognition as sr
from aiogram import Bot

from config import GOOGLE_STT_LANGUAGE

logger = logging.getLogger(__name__)

# Temp directory for audio files
TEMP_DIR = Path(tempfile.gettempdir()) / "tg_opencode_bot"


async def download_voice(file_id: str, bot: Bot) -> Path:
    """
    Download a voice message file from Telegram.

    Args:
        file_id: Telegram file_id of the voice message.
        bot: Aiogram Bot instance.

    Returns:
        Path to the downloaded OGG file.
    """
    TEMP_DIR.mkdir(exist_ok=True)

    # Get file info from Telegram
    file_info = await bot.get_file(file_id)
    ogg_path = TEMP_DIR / f"{file_id}.ogg"

    # Download file
    await bot.download_file(file_info.file_path, destination=str(ogg_path))
    logger.info("Downloaded voice to %s", ogg_path)

    return ogg_path


def convert_ogg_to_wav(ogg_path: Path) -> Path:
    """
    Convert OGG audio file to WAV format using pydub/FFmpeg.

    Args:
        ogg_path: Path to the OGG file.

    Returns:
        Path to the converted WAV file.
    """
    wav_path = ogg_path.with_suffix(".wav")

    # Load OGG and export as WAV
    audio = AudioSegment.from_ogg(str(ogg_path))
    audio.export(str(wav_path), format="wav")
    logger.info("Converted %s to %s", ogg_path.name, wav_path.name)

    return wav_path


def transcribe(wav_path: Path, language: str = GOOGLE_STT_LANGUAGE) -> str:
    """
    Transcribe a WAV audio file using Google Speech Recognition.

    Args:
        wav_path: Path to the WAV file.
        language: Language code for transcription (e.g., 'ru-RU', 'en-US').

    Returns:
        Transcribed text.
    """
    recognizer = sr.Recognizer()

    with sr.AudioFile(str(wav_path)) as source:
        audio_data = recognizer.record(source)

    try:
        # Use Google's free speech recognition API
        text = recognizer.recognize_google(audio_data, language=language)
        logger.info("Transcribed: %s", text[:100])
        return text
    except sr.UnknownValueError:
        logger.warning("Google STT could not understand the audio")
        return ""
    except sr.RequestError as e:
        logger.error("Google STT request failed: %s", e)
        raise RuntimeError(f"Ошибка сервиса распознавания: {e}") from e


async def process_voice(file_id: str, bot: Bot, language: str = GOOGLE_STT_LANGUAGE) -> str:
    """
    Process a voice message: download, convert, and transcribe.

    Args:
        file_id: Telegram file_id of the voice message.
        bot: Aiogram Bot instance.
        language: Language code for transcription.

    Returns:
        Transcribed text, or empty string if transcription failed.
    """
    # Step 1: Download
    ogg_path = await download_voice(file_id, bot)

    # Step 2: Convert OGG → WAV
    wav_path = convert_ogg_to_wav(ogg_path)

    # Step 3: Transcribe
    text = transcribe(wav_path, language)

    # Cleanup temp files
    try:
        ogg_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)
    except OSError:
        pass

    return text
```

- [ ] **Step 2: Verify stt.py imports correctly**

Run: `python -c "from stt import process_voice; print('OK')"`
Expected: Prints "OK" with no errors

---

### Task 5: Create bot.py — Main Bot Module

**Files:**
- Create: `E:\tg opencode bot\bot.py`

- [ ] **Step 1: Create bot.py**

```python
"""Telegram bot for OpenCode. Entry point and message handlers."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

from config import BOT_TOKEN, ALLOWED_USER_ID, GOOGLE_STT_LANGUAGE, validate_config
from opencode_client import ask_opencode
from stt import process_voice

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def is_allowed(message: types.Message) -> bool:
    """Check if the message is from the allowed user."""
    return message.from_user is not None and message.from_user.id == ALLOWED_USER_ID


@dp.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    """Handle /start command."""
    if not is_allowed(message):
        return

    await message.answer(
        "Привет! Я бот, связывающий Telegram с OpenCode.\n\n"
        "Отправь мне текстовое или голосовое сообщение, "
        "и я перешлём его в OpenCode и вернём ответ.\n\n"
        "Команды:\n"
        "/start — это сообщение"
    )


@dp.message(F.text)
async def handle_text(message: types.Message) -> None:
    """Handle text messages."""
    if not is_allowed(message):
        return

    text = message.text
    if not text:
        return

    logger.info("Text from %d: %s", message.from_user.id, text[:100])

    # Show typing indicator
    await message.chat.action("typing")

    # Get response from opencode
    response = await ask_opencode(text)

    # Send response (split if too long for Telegram's 4096 char limit)
    for chunk in _split_text(response, 4000):
        await message.answer(chunk)


@dp.message(F.voice)
async def handle_voice(message: types.Message) -> None:
    """Handle voice messages."""
    if not is_allowed(message):
        return

    if not message.voice:
        return

    logger.info("Voice from %d", message.from_user.id)

    # Show recording indicator
    await message.chat.action("record_voice")

    try:
        # Transcribe voice
        text = await process_voice(
            file_id=message.voice.file_id,
            bot=bot,
            language=GOOGLE_STT_LANGUAGE,
        )

        if not text:
            await message.answer("Не удалось распознать голосовое сообщение.")
            return

        # Show that we're processing
        await message.chat.action("typing")

        # Send transcribed text as a quote
        await message.answer(f"Распознано: {text}")

        # Get response from opencode
        response = await ask_opencode(text)

        # Send response
        for chunk in _split_text(response, 4000):
            await message.answer(chunk)

    except Exception as e:
        logger.exception("Error processing voice message")
        await message.answer(f"Ошибка при обработке голоса: {e}")


def _split_text(text: str, max_length: int) -> list[str]:
    """Split text into chunks for Telegram's message length limit."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Try to split at newline or space
        split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(" ", 0, max_length)
        if split_pos == -1:
            split_pos = max_length

        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n").lstrip()

    return chunks


async def main() -> None:
    """Main entry point."""
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    logger.info("Starting bot...")
    logger.info("Allowed user ID: %d", ALLOWED_USER_ID)

    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Verify bot.py imports correctly**

Run: `python -c "import bot; print('OK')"`
Expected: Prints "OK" (may show config warnings if .env not configured)

---

### Task 6: Manual Integration Test

- [ ] **Step 1: Update .env with real credentials**

Edit `E:\tg opencode bot\.env` and set:
- `BOT_TOKEN` = your bot token from @BotFather
- `ALLOWED_USER_ID` = your Telegram user ID (get from @userinfobot)

- [ ] **Step 2: Run the bot**

Run: `python "E:\tg opencode bot\bot.py"`
Expected: Bot starts polling, logs show "Starting bot..."

- [ ] **Step 3: Test text message**

In Telegram, send any text to your bot.
Expected: Bot shows "typing...", then responds with opencode's answer.

- [ ] **Step 4: Test voice message**

In Telegram, send a voice message to your bot.
Expected: Bot shows "recording...", then "typing...", then transcribes and responds.

- [ ] **Step 5: Stop the bot**

Press Ctrl+C in the terminal.
Expected: Bot stops gracefully.

---

### Task 7: Create README.md with Setup Instructions

**Files:**
- Create: `E:\tg opencode bot\README.md`

- [ ] **Step 1: Create README.md**

```markdown
# Telegram Bot for OpenCode

Telegram-бот, связывающий смартфон с утилитой OpenCode на ПК.

## Возможности

- Отправка текстовых сообщений → OpenCode → ответ
- Отправка голосовых сообщений → распознавание речи → OpenCode → ответ
- Безопасность: работает только для указанного user ID

## Требования

- Python 3.10+
- FFmpeg (для конвертации аудио)
- OpenCode CLI (установлен и в PATH)
- Telegram Bot Token (от @BotFather)

## Установка

### 1. Установите FFmpeg

**Windows:**
```bash
# Через winget
winget install Gyan.FFmpeg

# Или скачайте с https://ffmpeg.org/download.html и добавьте в PATH
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### 2. Установите Python-зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

Файл `.env`:
```
BOT_TOKEN=ваш_токен_бота
ALLOWED_USER_ID=ваш_telegram_id
```

Узнать свой Telegram ID: отправьте `/start` боту @userinfobot

### 4. Запустите бота

```bash
python bot.py
```

## Использование

1. Откройте чат с ботом в Telegram
2. Отправьте `/start`
3. Отправьте текстовое или голосовое сообщение
4. Бот перешлёт его в OpenCode и вернёт ответ

## Структура файлов

```
├── bot.py              # Точка входа, обработчики сообщений
├── opencode_client.py  # Взаимодействие с OpenCode
├── stt.py              # Распознавание голоса
├── config.py           # Конфигурация
├── requirements.txt    # Зависимости Python
├── .env                # Секреты (не коммитить!)
└── README.md           # Этот файл
```
```

- [ ] **Step 2: Verify complete project structure**

Run: `Get-ChildItem "E:\tg opencode bot" -File | Select-Object Name`
Expected: Shows bot.py, config.py, opencode_client.py, stt.py, requirements.txt, .env, README.md

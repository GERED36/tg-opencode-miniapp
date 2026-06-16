# Telegram Bot for OpenCode — Design Spec

## Overview

A Telegram bot that bridges a smartphone with the `opencode` CLI utility running on a PC. The bot accepts text and voice messages via Telegram, forwards them to opencode, and returns the AI-generated response.

## Goals

- Send text messages from Telegram → opencode → receive response
- Send voice messages from Telegram → STT transcription → opencode → receive response
- Security: only respond to a specific Telegram user ID
- Non-blocking async operation

## Architecture

Modular design with 4 Python modules:

```
tg opencode bot/
├── bot.py              # Entry point, Telegram handlers
├── opencode_client.py  # OpenCode interaction via subprocess
├── stt.py              # Voice download + conversion + transcription
├── config.py           # Configuration from .env
├── requirements.txt    # Dependencies
└── .env                # Secrets (not committed)
```

## Modules

### config.py

Loads environment variables via `python-dotenv`:

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | required |
| `ALLOWED_USER_ID` | Telegram user ID for access control | required |
| `OPENCODE_WORK_DIR` | Working directory for opencode | current dir |
| `GOOGLE_STT_LANGUAGE` | STT language code | `ru-RU` |

### opencode_client.py

Single async function:

```python
async def ask_opencode(message: str) -> str
```

- Executes: `opencode run "<message>" --format json --dir "<work_dir>"`
- Uses `asyncio.create_subprocess_exec` for non-blocking execution
- Parses JSON-lines output: each line is a separate JSON object
- Extracts text from lines where `type == "text"` (field `part.text`)
- Reads until `type == "step_finish"` to know response is complete
- Timeout: 120 seconds
- Returns concatenated text or error message on failure

Example JSON output per line:
```json
{"type":"text","part":{"text":"Hello!","type":"text"}}
{"type":"step_finish","part":{"type":"step-finish","reason":"stop"}}
```

### stt.py

Functions:

1. `download_voice(file_id: str, bot: Bot) -> Path` — Downloads OGG from Telegram to temp directory
2. `convert_ogg_to_wav(ogg_path: Path) -> Path` — Converts OGG to WAV via pydub (uses FFmpeg)
3. `transcribe(wav_path: Path, language: str) -> str` — Google Speech Recognition API transcription
4. `process_voice(file_id: str, bot: Bot, language: str) -> str` — Wrapper that chains all three

### bot.py

Entry point and Telegram handlers:

- `/start` — Welcome message with usage instructions
- Text message handler → `ask_opencode()` → reply
- Voice message handler → `process_voice()` → `ask_opencode()` → reply

Security: every handler checks `message.from_user.id == ALLOWED_USER_ID`, silently ignores others.

Status indicators:
- While opencode processes: show "typing..." action
- While processing voice: show "recording..." then "typing..."

## Data Flow

### Text message:
```
User sends text → bot.py handler → config check → opencode_client.ask_opencode()
→ subprocess: opencode run "text" --format json → parse JSON → reply to user
```

### Voice message:
```
User sends voice → bot.py handler → config check → stt.process_voice()
→ download OGG → convert to WAV → Google STT → text
→ opencode_client.ask_opencode() → reply to user
```

## Dependencies

### Python packages (requirements.txt):
- `aiogram>=3.0` — Telegram bot framework
- `python-dotenv` — .env file loading
- `pydub` — audio format conversion
- `SpeechRecognition` — Google STT API client

### System requirements:
- Python 3.10+
- FFmpeg (for audio conversion)
- opencode CLI (installed and in PATH)
- Telegram Bot Token (from @BotFather)

## Security

- `ALLOWED_USER_ID` check on every message handler
- Bot token and user ID stored in `.env` (not committed)
- No logging of sensitive data (messages, tokens)

## Error Handling

- opencode timeout → "OpenCode не ответил вовремя (таймаут 120 сек)"
- STT failure → "Не удалось распознать голосовое сообщение"
- opencode error → "Ошибка OpenCode: {error}"
- All errors returned as user-friendly Telegram messages

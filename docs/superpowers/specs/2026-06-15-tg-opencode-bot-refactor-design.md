# Telegram OpenCode Bot — Refactor Design

**Date:** 2026-06-15
**Status:** Draft

## 1. Problem Statement

The current Telegram bot for OpenCode has several critical issues:

- **Two incompatible agent communication protocols**: `bot.py` generates `agent_{user_id}.py` using HTTP long-polling (`/agent/register`, `/agent/poll`, `/agent/response`), but the manual `agent.py` uses a different protocol (`/register`, `/command`, `/response`). They are completely incompatible.
- **Broken commands**: `/delete` has a logic error (only fires when no args, ignores with args). `/session` is a stub.
- **Missing error handling**: `/stats`, `/version`, `/debug`, `/models` send requests to agent without checking if agent is connected. No clear error messages.
- **No confirmation on actions**: Most commands execute silently without feedback.
- **Log pollution**: Poll requests generate ~24K log lines per session.
- **Monolithic layout**: `bot.py` is 1121 lines mixing handlers, HTTP server, formatting, and state management.

## 2. Scope

This project fixes all known bugs, unifies the agent protocol, adds proper error/confirmation for every command, adds admin tools, rate limiting (10 msg/min per user), and refactors the codebase into a modular structure.

## 3. Architecture

### 3.1 Directory Structure

```
tg_opencode_bot/
├── bot.py                  # Entry point, starts bot + HTTP server
├── config.py               # Config (.env, BOT_TOKEN, ADMIN_IDS, rate limits)
├── models_db.py            # Model database (unchanged)
├── stt.py                  # Speech-to-text (unchanged)
├── requirements.txt
├── .env
│
├── handlers/
│   ├── __init__.py
│   ├── commands.py         # All command handlers
│   ├── messages.py         # Text, photo, video, document, voice
│   └── callbacks.py        # Inline keyboard callbacks (model selection)
│
├── services/
│   ├── __init__.py
│   ├── agent_bridge.py     # HTTP server + long-polling protocol
│   ├── session_manager.py  # Sessions + contexts + persistence
│   └── opencode_runner.py  # OpenCode execution
│
├── utils/
│   ├── __init__.py
│   ├── formatter.py        # HTML formatting, emoji, split, code blocks
│   └── logger.py           # Logging setup (poll noise suppressed)
│
└── agent/
    ├── agent.py            # Manual agent launcher (same protocol as generated)
    └── template.py         # Template for generated agent_{user_id}.py
```

### 3.2 Module Responsibilities

- **bot.py**: Parse config, start aiohttp server, register routes, start aiogram polling. Minimal wiring.
- **handlers/commands.py**: Decorated functions for each command. Validate args, check agent connection if needed, call services, send result.
- **handlers/messages.py**: Handle text, photo, video, document, voice messages. Manage sessions context.
- **handlers/callbacks.py**: Handle inline keyboard callbacks for model selection and pagination.
- **services/agent_bridge.py**: HTTP server routes (`/agent/register`, `/agent/poll`, `/agent/response`), file download/upload, `ask_agent()` function.
- **services/session_manager.py**: Load/save user sessions and contexts from JSON files. Handle corruption with backup.
- **services/opencode_runner.py**: Execute `opencode run` for direct commands (version check, etc.).
- **utils/formatter.py**: `_send()`, `_split_text()`, `_format_code()`, `_replace_emoji()`, `_encode/decode_model_id()`.
- **utils/logger.py**: RotatingFileHandler with DEBUG level for poll entries filtered out from INFO.

## 4. Agent Communication Protocol (Unified)

Both `agent.py` and generated `agent_{user_id}.py` use the same protocol:

### Registration
```
POST /agent/register
Request:  { "user_id": "<str>", "token": "<str>" }
Response: { "ok": true }
Response: { "ok": false, "error": "Missing fields" }
```

### Polling (agent → bot, every 3s)
```
POST /agent/poll
Request:  { "user_id": "<str>", "token": "<str>" }
Response: { "cmd": "wait" }
Response: { "cmd": "run", "message": "...", "continue_session": bool,
            "files": ["url1", ...], "request_id": "<str>" }
```
On `cmd: "run"`: agent executes `opencode run ...` and sends result back.

### Response (agent → bot)
```
POST /agent/response
Request:  { "user_id": "<str>", "token": "<str>", "request_id": "<str>", "result": "<str>" }
Response: { "ok": true }
```

### File transfer
```
GET  /files/{filename}       # Download file (agent → bot)
POST /files/upload           # Upload file (agent → bot)
```

### Pending command queue
- `user_id` + `secrets.token_hex(4)` → unique `request_id`
- `pending_commands[request_id]` = `asyncio.Event()` — signals when response arrives
- `command_responses[request_id]` = result dict — cleared after pickup
- Agent auth checked via token match in `connected_agents`

## 5. Command Specification

Every command follows the pattern:
1. Validate input (args, permissions)
2. Check agent connectivity if the command requires it
3. Execute action
4. Return clear success ✅ or error ❌ message

### Connection Commands

| Command | Behavior | Agent required | Output |
|---------|----------|:---:|--------|
| `/start` | Generate `agent_{user_id}.py`, send file + instructions | — | ✅ agent.py отправлен |
| `/status` | Show connection status, model, session, context | — | ✅ Панель статуса |
| `/disconnect` | Remove agent from `connected_agents` | — | ✅ Агент отключён / ❌ Нет подключения |

### Session Commands

| Command | Behavior | Agent required | Output |
|---------|----------|:---:|--------|
| `/sessions` | Show session state | ✅ | ✅ Сессия активна / ❌ Нет агента |
| `/session` | Show session info (alias for `/sessions`) | ✅ | ✅ Информация о сессии |
| `/new` | Reset session flag | ✅ | ✅ Новая сессия создана / ❌ Нет агента |
| `/delete` | Delete current session | — | ✅ Сессия удалена / ❌ Нет сессии |
| `/delete all` | Delete all user sessions | — | ✅ Все сессии удалены |
| `/cancel` | Cancel pending request | ✅ | ✅ Запрос отменён / ❌ Нет активного запроса |

### Context Commands

| Command | Behavior | Output |
|---------|----------|--------|
| `/context` | Show current context | ✅ Контекст / ℹ️ Контекст не задан |
| `/context <текст>` | Set context for new sessions | ✅ Контекст установлен |
| `/context delete` | Delete context | ✅ Контекст удалён |

### Model Commands

| Command | Behavior | Agent required | Output |
|---------|----------|:---:|--------|
| `/models` | List all models from local DB | — | 📋 Список (inline keyboard) |
| `/models <поиск>` | Search models locally | — | ✅ Результаты / ❌ Ничего не найдено |
| `/model` | Show provider filter keyboard | — | 🧠 Выберите провайдера |
| `/model <id>` | Set model via agent | ✅ | ✅ Модель сменена / ❌ Ошибка |

### OpenCode Commands

| Command | Behavior | Agent required | Output |
|---------|----------|:---:|--------|
| `/stats` | Forward to agent (`stats`) | ✅ | ✅ Статистика / ❌ Ошибка |
| `/version` | Run `opencode --version` locally | — | ✅ Версия / ❌ OpenCode не найден |

### Admin Commands (🔒)

| Command | Behavior | Output |
|---------|----------|--------|
| `/admin` | Panel with user list, stats | ✅ Панель / ❌ Нет прав |
| `/broadcast <msg>` 🔒 | Send message to all active users | ✅ Разослано N / ❌ Нет получателей |

### Error responses

| Scenario | Response |
|----------|----------|
| Agent not connected | ❌ Ваш ПК не подключён. Отправьте /start для инструкций. |
| Agent timeout | ❌ Агент не ответил за 6 минут. Проверьте agent.py. |
| Invalid args | ❌ Использование: /command <аргументы> |
| Permission denied | ❌ У вас нет прав для этой команды. |
| Rate limited | ⏳ Слишком много запросов. Подождите. |
| Internal error | ❌ Внутренняя ошибка. Попробуйте позже. |

## 6. Rate Limiting

- **10 messages per 60 seconds** per user
- Implemented as a simple deque of timestamps in memory
- If limit exceeded, respond with `⏳ Слишком много запросов. Подождите.`
- Admin excluded from rate limiting
- Commands under rate limit: all except `/start` and `/help`

## 7. Session Management

- `user_sessions.json`: `{user_id: bool}` — whether user has ongoing session
- `user_contexts.json`: `{user_id: str}` — initial context text for new sessions
- On JSON parse error: create `.bak` copy, start fresh, log warning
- Sessions auto-created on first message after `/new` or after agent connect

## 8. Error Handling

- All handler functions wrapped in try/except with user-friendly fallback
- Unhandled exceptions caught at Dispatcher level → user sees generic error
- Full traceback logged to file (DEBUG level)
- Config validation on startup (BOT_TOKEN required)

## 9. Logging

- RotatingFileHandler: 5MB per file, 2 backups
- Agent poll requests logged at DEBUG level (hidden from INFO)
- All command executions logged at INFO level
- Separate `bot.log` for main bot events

## 10. Out of Scope

- Database migration (SQLite/Postgres) — JSON persistence remains
- Web UI — Telegram is the only interface
- Multi-agent per user — one user = one agent
- SSH tunneling — manual network setup assumed
- Agent auto-update — agent must be restarted manually
- Tests — CI pipeline not included

## 11. Migration Path

1. Deploy new `bot.py` and supporting modules
2. Users regenerate `agent_{user_id}.py` via `/start`
3. Users running manual `agent.py` switch to new version
4. Old `connected_agents.json` format replaced by in-memory `connected_agents` dict

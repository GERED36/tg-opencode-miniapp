# Telegram OpenCode Mini App — Design

**Date:** 2026-06-16
**Status:** Draft

## 1. Overview

Telegram Mini App frontend that serves as a graphical interface for the existing Telegram OpenCode bot. Replaces the Telegram chat UI with a modern web app featuring real-time streaming, split reasoning/answer display, glassmorphism design, and multi-agent PC switching.

## 2. Architecture

### 2.1 Topology

```
[TMA (React SPA)] ←→ [Cloud Hub (VPS/Railway)] ←WebSocket→ [Agent (ПК #1)]
                                                    ←WebSocket→ [Agent (ПК #2)]
                                                    ←WebSocket→ [Agent (ПК #N)]
                           │
                           │ Telegram Bot API (команды)
                           ▼
                      [Bot.py — Telegram commands only]
```

### 2.2 Components

- **Cloud Hub** — lightweight publicly-accessible server. Hosts TMA SPA static files, WebSocket manager for streaming, REST API for agent listing/switching. Handles Telegram initData verification for auth.
- **TMA Client** — React SPA inside Telegram WebView, connects to Hub via WebSocket.
- **Agent** — runs on each user PC. Connects to Hub via WebSocket (replaces current long-polling). Streams opencode output chunk-by-chunk.
- **Bot.py** — unchanged Telegram bot for /start, /help, etc. Not involved in streaming.

### 2.3 Data Flow

1. TMA user selects agent PC and sends message → Hub (WebSocket JSON)
2. Hub routes to target Agent (WebSocket)
3. Agent spawns `opencode run ...` with streaming stdout
4. Each chunk → Agent → Hub → TMA (WebSocket NDJSON)
5. TMA parses chunks: `<thought...>` → Reasoning, rest → Answer
6. Markdown rendered incrementally in AnswerBlock

## 3. Communication Protocol

### 3.1 Hub REST API

```
POST   /api/auth/tg              — verify Telegram initData, return JWT
GET    /api/agents               — list user's connected PCs
POST   /api/agents/:id/send      — send message to agent (fallback)
```

### 3.2 WebSocket (Agent ↔ Hub)

Agent connects once, stays connected:

```json
// Agent → Hub: register
{"type":"register","agent_id":"user_123_pc_1","user_id":"123","token":"..."}

// Agent → Hub: heartbeats every 15s
{"type":"ping"}

// Hub → Agent: new task
{"type":"run","task_id":"t_abc","message":"hello","session_id":"...","files":[...]}

// Agent → Hub: streaming chunks
{"type":"chunk","task_id":"t_abc","kind":"reasoning","token":"текст чанка"}
{"type":"chunk","task_id":"t_abc","kind":"answer","token":"текст чанка"}
{"type":"done","task_id":"t_abc"}
{"type":"error","task_id":"t_abc","message":"..."}
```

### 3.3 WebSocket (Hub ↔ TMA)

Same chunk format forwarded 1:1. TMA also sends:

```json
// TMA → Hub: send message
{"type":"message","agent_id":"user_123_pc_1","text":"..."}

// TMA → Hub: switch agent
{"type":"switch_agent","agent_id":"user_123_pc_2"}

// TMA → Hub: new session
{"type":"new_session","agent_id":"user_123_pc_1"}

// TMA → Hub: cancel
{"type":"cancel","agent_id":"user_123_pc_1"}
```

### 3.4 Agent chit parsing

OpenCode outputs lines. Agent reads stdout line by line:

- If line contains `<thought...>` or starts with thinking marker → `kind: "reasoning"`
- Otherwise → `kind: "answer"`
- Empty lines with no new content skipped
- Lines forwarded as-is (TMA handles merging into markdown)

## 4. Frontend Component Tree

```
App
├── ThemeProvider           — maps Telegram theme → CSS vars
├── Header (glassmorphism)
│   ├── AgentSwitcher      — dropdown of connected PCs
│   ├── ConnectionStatus   — online/offline/reconnecting dot
│   └── NewSessionBtn
├── ChatArea
│   ├── MessageList
│   │   └── Message
│   │       ├── ReasoningBlock — collapsible <details>, dimmed
│   │       └── AnswerBlock    — react-markdown + code highlighting
│   └── StreamingMessage   — in-progress message, appends tokens
├── InputBar (glassmorphism)
│   ├── TextArea           — auto-resize, 1-4 rows
│   └── SendButton
└── ToastContainer
```

### 4.1 States

**Connection:** `DISCONNECTED → CONNECTING → AUTHENTICATING → CONNECTED → (RECONNECTING)`

**Agent:** `ONLINE` | `OFFLINE` | `BUSY`

**Message:** `SENDING` | `STREAMING` | `COMPLETE` | `ERROR`

### 4.2 State Management

React Context + useReducer, no external library:

```typescript
interface AppState {
  agents: Agent[]
  activeAgentId: string
  messages: Message[]
  streamingMessage: StreamingMessage | null
  wsStatus: WsStatus
  tg: TelegramTheme
}
```

## 5. Visual Design

### 5.1 Color Palette (OpenCode CLI tones)

```css
:root {
  --oc-bg:        #0d1117;
  --oc-surface:   #161b22;
  --oc-border:    #30363d;
  --oc-text:      #e6edf3;
  --oc-text-dim:  #8b949e;
  --oc-accent:    #58a6ff;
  --oc-green:     #3fb950;
  --oc-orange:    #d29922;
  --oc-red:       #f85149;
  --glass-bg:     rgba(22,27,34,0.75);
  --glass-border: rgba(48,54,61,0.4);
  --glass-blur:   16px;
}
```

### 5.2 Glassmorphism Elements

| Element | Technique |
|---------|-----------|
| Header | `background: var(--glass-bg); backdrop-filter: blur(var(--glass-blur))` |
| InputBar | Same glass bg, `border-radius: 16px`, thin border |
| AgentSwitcher dropdown | Glass with fade-in animation |
| Mobile bottom sheet | Glass background |

### 5.3 Reasoning & Answer

- **ReasoningBlock**: `<details>` tag, text `opacity: 0.65`, `font-size: 0.9em`, gray left border accent
- **AnswerBlock**: Full opacity, `line-height: 1.6`, Markdown + code blocks (one-dark-pro theme)
- **Code blocks**: `background: #1a1f29`, `border-radius: 8px`, copy button on hover
- **Animations**: Tokens fade in (`opacity 0→1, translateY(2px→0)`), Reasoning expands with `max-height` transition

### 5.4 Responsiveness

- 100% width, `max-width: 768px` centered on desktop
- Font sizes in rem, spacing in rem
- Supports Telegram light/dark themes via `tg-theme-color` CSS variables
- Touch-friendly targets (min 44px)

## 6. Agent Modifications

### 6.1 Current → New

| Aspect | Current | New |
|--------|---------|-----|
| Transport | HTTP long-polling to bot.py | WebSocket to Cloud Hub |
| Response | Full text after completion | Streaming chunks per line |
| Connection | Poll every 3s | Persistent WS + heartbeat 15s |
| Auth | Token in poll body | Token in register message |

### 6.2 Required changes to agent.py

1. Replace polling loop with aiohttp WebSocket connection (`ws_connect`)
2. On `"run"` command: spawn opencode subprocess, pipe stdout line-by-line
3. Each line → WebSocket `{"type":"chunk",...}`
4. After EOF → `{"type":"done"}`
5. Handle reconnect with exponential backoff
6. Remove polling-related code

### 6.3 Chunk Detection

OpenCode CLI outputs reasoning inside `[thought]...[\/thought]` markers. Agent tracks state:

```python
in_thought = False

async def stream_opencode(cmd, ws, task_id):
    global in_thought
    process = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    async for line in process.stdout:
        text = line.decode("utf-8", errors="replace")
        stripped = text.strip()
        if not stripped:
            continue
        if "[thought]" in stripped:
            in_thought = True
            continue
        if "[/thought]" in stripped:
            in_thought = False
            continue
        kind = "reasoning" if in_thought else "answer"
        await ws.send_json({"type":"chunk","task_id":task_id,"kind":kind,"token":text})
    await ws.send_json({"type":"done","task_id":task_id})
```

## 7. Cloud Hub

### 7.1 Technology

- **Runtime:** Node.js with Fastify (or Python with aiohttp — same as existing)
- **Database:** None (ephemeral state; agent list in memory)
- **Auth:** JWT signed from Telegram initData verification
- **Deploy:** Railway / Render / fly.io (5s startup, 256MB RAM enough)

### 7.2 Responsibilities

- Verify Telegram initData via Bot API token
- Issue JWT for TMA client
- Maintain WebSocket registry: agent_id → ws_connection
- Route `{type:"message"}` from TMA to correct Agent WS
- Forward streaming chunks from Agent to TMA
- Handle TMA reconnection: buffer last N chunks per task for reconnection

### 7.3 No persistence

- Agent list rebuilt on each WS connect
- No message history stored server-side
- Session management deferred to opencode (via `--session` flag)

## 8. Out of Scope

- Message history persistence in Hub
- File upload/download via TMA
- Voice messages in TMA
- Bot.py modification (unchanged)

## 9. Open Questions

- Cloud Hub runtime: Python aiohttp (matches existing stack) vs Node.js Fastify (better WS ecosystem)
- Streaming buffering strategy for TMA reconnection: how many chunks to buffer

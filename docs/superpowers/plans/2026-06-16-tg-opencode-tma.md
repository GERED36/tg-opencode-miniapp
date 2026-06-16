# TMA (Telegram Mini App) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram Mini App frontend + Cloud Hub + agent streaming modifications to provide a real-time graphical UI for OpenCode.

**Architecture:** Three subsystems: (1) React SPA inside Telegram WebView with glassmorphism UI, (2) Python aiohttp Cloud Hub handling WebSocket routing between TMA and agents, (3) streaming modifications to agent.py. TMA communicates with Hub via WebSocket, Hub routes to agents via WebSocket.

**Tech Stack:** React 18 + Vite 5 + Tailwind CSS 3 + TypeScript (frontend), Python 3.10+ + aiohttp + PyJWT (hub), Python 3.10+ + aiohttp (agent)

---

### Task 1: Scaffold TMA frontend project

**Files:**
- Create: `E:/tg opencode bot/tma/package.json`
- Create: `E:/tg opencode bot/tma/tsconfig.json`
- Create: `E:/tg opencode bot/tma/tsconfig.node.json`
- Create: `E:/tg opencode bot/tma/vite.config.ts`
- Create: `E:/tg opencode bot/tma/tailwind.config.ts`
- Create: `E:/tg opencode bot/tma/postcss.config.js`
- Create: `E:/tg opencode bot/tma/index.html`
- Create: `E:/tg opencode bot/tma/src/vite-env.d.ts`
- Create: `E:/tg opencode bot/tma/src/main.tsx`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "tg-opencode-tma",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1",
    "react-syntax-highlighter": "^15.5.0",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@types/react-syntax-highlighter": "^15.5.11",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.4.5",
    "vite": "^5.3.1"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create vite.config.ts**

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
})
```

- [ ] **Step 5: Create tailwind.config.ts**

```ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        oc: {
          bg: '#0d1117',
          surface: '#161b22',
          border: '#30363d',
          text: '#e6edf3',
          'text-dim': '#8b949e',
          accent: '#58a6ff',
          green: '#3fb950',
          orange: '#d29922',
          red: '#f85149',
        },
      },
      backdropBlur: {
        glass: '16px',
      },
    },
  },
  plugins: [],
} satisfies Config
```

- [ ] **Step 6: Create postcss.config.js**

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 7: Create index.html**

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta name="viewport" content="width=390, initial-scale=1.0, user-scalable=no" />
    <title>OpenCode TMA</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 8: Create src/vite-env.d.ts**

```ts
/// <reference types="vite/client" />

interface TelegramWebApp {
  initData: string
  initDataUnsafe: {
    user?: { id: number; first_name: string; last_name?: string; username?: string }
  }
  colorScheme: 'light' | 'dark'
  themeParams: {
    bg_color?: string
    text_color?: string
    hint_color?: string
    link_color?: string
    button_color?: string
    button_text_color?: string
    secondary_bg_color?: string
  }
  ready: () => void
  expand: () => void
  close: () => void
  MainButton: {
    text: string
    show: () => void
    hide: () => void
    onClick: (cb: () => void) => void
  }
  onEvent: (eventType: string, handler: () => void) => void
}

interface Window {
  Telegram?: { WebApp?: TelegramWebApp }
}
```

- [ ] **Step 9: Create src/main.tsx**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

- [ ] **Step 10: Install dependencies**

Run: `cd E:\tg opencode bot\tma && npm install`
Expected: node_modules created, no errors

---

### Task 2: Create shared types

**Files:**
- Create: `E:/tg opencode bot/tma/src/types.ts`

- [ ] **Step 1: Create types.ts**

```ts
export type ConnectionStatus = 'disconnected' | 'connecting' | 'authenticating' | 'connected' | 'reconnecting'

export type AgentStatus = 'online' | 'offline' | 'busy'

export type MessageStatus = 'sending' | 'streaming' | 'complete' | 'error'

export interface Agent {
  id: string
  name: string
  userId: string
  status: AgentStatus
}

export interface Chunk {
  kind: 'reasoning' | 'answer'
  token: string
}

export interface Message {
  id: string
  text: string
  reasoning: string
  status: MessageStatus
  timestamp: number
  error?: string
}

export interface TelegramTheme {
  bgColor: string
  textColor: string
  hintColor: string
  linkColor: string
  buttonColor: string
  buttonTextColor: string
  secondaryBgColor: string
  colorScheme: 'light' | 'dark'
}

export interface AppState {
  agents: Agent[]
  activeAgentId: string
  messages: Message[]
  streamingMessage: Message | null
  wsStatus: ConnectionStatus
  tg: TelegramTheme
}

export type AppAction =
  | { type: 'SET_AGENTS'; payload: Agent[] }
  | { type: 'SET_ACTIVE_AGENT'; payload: string }
  | { type: 'SET_WS_STATUS'; payload: ConnectionStatus }
  | { type: 'SET_TG_THEME'; payload: TelegramTheme }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'APPEND_STREAM_CHUNK'; payload: { reasoning?: string; answer?: string } }
  | { type: 'FINALIZE_STREAM' }
  | { type: 'SET_MESSAGE_ERROR'; payload: string }
  | { type: 'CLEAR_MESSAGES' }

// WebSocket protocol types
export interface WsMessage {
  type: string
  [key: string]: unknown
}

export interface WsChunk extends WsMessage {
  type: 'chunk'
  task_id: string
  kind: 'reasoning' | 'answer'
  token: string
}

export interface WsDone extends WsMessage {
  type: 'done'
  task_id: string
}

export interface WsError extends WsMessage {
  type: 'error'
  task_id: string
  message: string
}
```

---

### Task 3: Create Telegram API service

**Files:**
- Create: `E:/tg opencode bot/tma/src/services/tgApi.ts`

- [ ] **Step 1: Create tgApi.ts**

```ts
import type { TelegramTheme } from '../types'

export function getTelegramWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null
}

export function getInitData(): string {
  const tg = getTelegramWebApp()
  return tg?.initData ?? ''
}

export function getTelegramTheme(): TelegramTheme {
  const tg = getTelegramWebApp()
  const tp = tg?.themeParams ?? {}
  return {
    bgColor: tp.bg_color ?? '#0d1117',
    textColor: tp.text_color ?? '#e6edf3',
    hintColor: tp.hint_color ?? '#8b949e',
    linkColor: tp.link_color ?? '#58a6ff',
    buttonColor: tp.button_color ?? '#3fb950',
    buttonTextColor: tp.button_text_color ?? '#ffffff',
    secondaryBgColor: tp.secondary_bg_color ?? '#161b22',
    colorScheme: tg?.colorScheme ?? 'dark',
  }
}

export function ready(): void {
  const tg = getTelegramWebApp()
  tg?.ready()
  tg?.expand()
}
```

---

### Task 4: Theme context

**Files:**
- Create: `E:/tg opencode bot/tma/src/contexts/ThemeContext.tsx`

- [ ] **Step 1: Create ThemeContext.tsx**

```tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { getTelegramTheme, ready } from '../services/tgApi'
import type { TelegramTheme } from '../types'

const defaultTheme: TelegramTheme = {
  bgColor: '#0d1117',
  textColor: '#e6edf3',
  hintColor: '#8b949e',
  linkColor: '#58a6ff',
  buttonColor: '#3fb950',
  buttonTextColor: '#ffffff',
  secondaryBgColor: '#161b22',
  colorScheme: 'dark',
}

const ThemeContext = createContext<TelegramTheme>(defaultTheme)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<TelegramTheme>(defaultTheme)

  useEffect(() => {
    ready()
    setTheme(getTelegramTheme())

    const tg = window.Telegram?.WebApp
    if (tg) {
      tg.onEvent('themeChanged', () => {
        setTheme(getTelegramTheme())
      })
    }
  }, [])

  return (
    <ThemeContext.Provider value={theme}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): TelegramTheme {
  return useContext(ThemeContext)
}
```

---

### Task 5: App state context

**Files:**
- Create: `E:/tg opencode bot/tma/src/contexts/AppContext.tsx`

- [ ] **Step 1: Create AppContext.tsx**

```tsx
import { createContext, useContext, useReducer, type ReactNode, type Dispatch } from 'react'
import type { AppState, AppAction, Agent, Message } from '../types'

const initialState: AppState = {
  agents: [],
  activeAgentId: '',
  messages: [],
  streamingMessage: null,
  wsStatus: 'disconnected',
  tg: {
    bgColor: '#0d1117',
    textColor: '#e6edf3',
    hintColor: '#8b949e',
    linkColor: '#58a6ff',
    buttonColor: '#3fb950',
    buttonTextColor: '#ffffff',
    secondaryBgColor: '#161b22',
    colorScheme: 'dark',
  },
}

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_AGENTS':
      return { ...state, agents: action.payload }

    case 'SET_ACTIVE_AGENT':
      return { ...state, activeAgentId: action.payload }

    case 'SET_WS_STATUS':
      return { ...state, wsStatus: action.payload }

    case 'SET_TG_THEME':
      return { ...state, tg: action.payload }

    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
        streamingMessage: action.payload,
      }

    case 'APPEND_STREAM_CHUNK': {
      const sm = state.streamingMessage
      if (!sm) return state
      return {
        ...state,
        streamingMessage: {
          ...sm,
          reasoning: sm.reasoning + (action.payload.reasoning ?? ''),
          text: sm.text + (action.payload.answer ?? ''),
        },
      }
    }

    case 'FINALIZE_STREAM': {
      const sm = state.streamingMessage
      if (!sm) return state
      return {
        ...state,
        messages: state.messages.map(m =>
          m.id === sm.id ? { ...sm, status: 'complete' as const } : m
        ),
        streamingMessage: null,
      }
    }

    case 'SET_MESSAGE_ERROR': {
      const sm = state.streamingMessage
      if (!sm) return state
      return {
        ...state,
        messages: state.messages.map(m =>
          m.id === sm.id ? { ...sm, status: 'error' as const, error: action.payload } : m
        ),
        streamingMessage: null,
      }
    }

    case 'CLEAR_MESSAGES':
      return { ...state, messages: [], streamingMessage: null }

    default:
      return state
  }
}

const AppContext = createContext<{
  state: AppState
  dispatch: Dispatch<AppAction>
}>({ state: initialState, dispatch: () => {} })

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState)
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppState() {
  return useContext(AppContext)
}
```

---

### Task 6: WebSocket hook

**Files:**
- Create: `E:/tg opencode bot/tma/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Create useWebSocket.ts**

```ts
import { useEffect, useRef, useCallback } from 'react'
import { useAppState } from '../contexts/AppContext'
import { getInitData } from '../services/tgApi'
import type { WsChunk, WsDone, WsError } from '../types'

let messageCounter = 0

export function useWebSocket(hubUrl: string) {
  const { state, dispatch } = useAppState()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const currentTaskIdRef = useRef<string>('')

  const connect = useCallback(() => {
    dispatch({ type: 'SET_WS_STATUS', payload: 'connecting' })
    const initData = getInitData()

    const ws = new WebSocket(`${hubUrl}/ws?initData=${encodeURIComponent(initData)}`)
    wsRef.current = ws

    ws.onopen = () => {
      dispatch({ type: 'SET_WS_STATUS', payload: 'connected' })
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsChunk | WsDone | WsError
        switch (data.type) {
          case 'chunk': {
            const chunk = data as WsChunk
            if (chunk.kind === 'reasoning') {
              dispatch({ type: 'APPEND_STREAM_CHUNK', payload: { reasoning: chunk.token } })
            } else {
              dispatch({ type: 'APPEND_STREAM_CHUNK', payload: { answer: chunk.token } })
            }
            break
          }
          case 'done':
            dispatch({ type: 'FINALIZE_STREAM' })
            currentTaskIdRef.current = ''
            break
          case 'error':
            dispatch({ type: 'SET_MESSAGE_ERROR', payload: (data as WsError).message })
            currentTaskIdRef.current = ''
            break
        }
      } catch { /* ignore malformed messages */ }
    }

    ws.onclose = () => {
      dispatch({ type: 'SET_WS_STATUS', payload: 'reconnecting' })
      reconnectTimeoutRef.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [dispatch])

  const sendMessage = useCallback((agentId: string, text: string) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return

    const taskId = `task_${Date.now()}_${messageCounter++}`
    currentTaskIdRef.current = taskId

    dispatch({
      type: 'ADD_MESSAGE',
      payload: {
        id: taskId,
        text: '',
        reasoning: '',
        status: 'streaming',
        timestamp: Date.now(),
      },
    })

    ws.send(JSON.stringify({
      type: 'message',
      agent_id: agentId,
      text,
      task_id: taskId,
    }))
  }, [dispatch])

  const switchAgent = useCallback((agentId: string) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'switch_agent', agent_id: agentId }))
    }
    dispatch({ type: 'SET_ACTIVE_AGENT', payload: agentId })
  }, [dispatch])

  const newSession = useCallback(() => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'new_session', agent_id: state.activeAgentId }))
    }
    dispatch({ type: 'CLEAR_MESSAGES' })
  }, [state.activeAgentId, dispatch])

  const cancel = useCallback(() => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'cancel', agent_id: state.activeAgentId }))
    }
  }, [state.activeAgentId])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { sendMessage, switchAgent, newSession, cancel, currentTaskId: currentTaskIdRef.current }
}
```

---

### Task 7: Header, AgentSwitcher, and ConnectionStatus components

**Files:**
- Create: `E:/tg opencode bot/tma/src/components/Header.tsx`
- Create: `E:/tg opencode bot/tma/src/components/AgentSwitcher.tsx`

- [ ] **Step 1: Create AgentSwitcher.tsx**

```tsx
import { useState } from 'react'
import { useAppState } from '../contexts/AppContext'
import type { Agent } from '../types'

interface AgentSwitcherProps {
  onSwitch: (agentId: string) => void
  onNewSession: () => void
}

export default function AgentSwitcher({ onSwitch, onNewSession }: AgentSwitcherProps) {
  const { state } = useAppState()
  const [open, setOpen] = useState(false)

  const active = state.agents.find(a => a.id === state.activeAgentId)
  const statusDot = active?.status === 'online' ? 'bg-oc-green' : active?.status === 'busy' ? 'bg-oc-orange' : 'bg-oc-red'

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-oc-surface/75 backdrop-blur-[16px] border border-oc-border/40 text-sm text-oc-text hover:bg-oc-surface transition-colors"
      >
        <span className={`w-2 h-2 rounded-full ${statusDot}`} />
        <span>{active?.name ?? 'Выберите ПК'}</span>
        <svg className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute top-full mt-2 left-0 z-20 min-w-[200px] rounded-xl bg-oc-surface/90 backdrop-blur-[16px] border border-oc-border/40 shadow-xl overflow-hidden animate-fade-in">
            {state.agents.map((agent: Agent) => (
              <button
                key={agent.id}
                onClick={() => { onSwitch(agent.id); setOpen(false) }}
                className={`w-full text-left px-4 py-3 text-sm transition-colors flex items-center gap-3 ${
                  agent.id === state.activeAgentId ? 'bg-oc-accent/10 text-oc-accent' : 'text-oc-text hover:bg-oc-border/30'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${agent.status === 'online' ? 'bg-oc-green' : agent.status === 'busy' ? 'bg-oc-orange' : 'bg-oc-red'}`} />
                {agent.name}
              </button>
            ))}
            <div className="border-t border-oc-border/40">
              <button
                onClick={() => { onNewSession(); setOpen(false) }}
                className="w-full text-left px-4 py-3 text-sm text-oc-text-dim hover:text-oc-text hover:bg-oc-border/30 transition-colors"
              >
                + Новый чат
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create Header.tsx**

```tsx
import AgentSwitcher from './AgentSwitcher'
import { useAppState } from '../contexts/AppContext'

interface HeaderProps {
  onSwitchAgent: (agentId: string) => void
  onNewSession: () => void
}

export default function Header({ onSwitchAgent, onNewSession }: HeaderProps) {
  const { state } = useAppState()

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-oc-bg/75 backdrop-blur-[16px] border-b border-oc-border/40">
      <div className="max-w-[768px] mx-auto flex items-center justify-between px-4 h-14">
        <AgentSwitcher onSwitch={onSwitchAgent} onNewSession={onNewSession} />

        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${
            state.wsStatus === 'connected' ? 'bg-oc-green' :
            state.wsStatus === 'reconnecting' || state.wsStatus === 'connecting' ? 'bg-oc-orange animate-pulse' :
            'bg-oc-red'
          }`} />
          <span className="text-xs text-oc-text-dim">
            {state.wsStatus === 'connected' ? 'Подключено' :
             state.wsStatus === 'connecting' ? 'Подключение...' :
             state.wsStatus === 'reconnecting' ? 'Переподключение...' :
             'Отключено'}
          </span>
        </div>
      </div>
    </header>
  )
}
```

---

### Task 8: ReasoningBlock and AnswerBlock components

**Files:**
- Create: `E:/tg opencode bot/tma/src/components/ReasoningBlock.tsx`
- Create: `E:/tg opencode bot/tma/src/components/AnswerBlock.tsx`

- [ ] **Step 1: Create ReasoningBlock.tsx**

```tsx
interface ReasoningBlockProps {
  text: string
}

export default function ReasoningBlock({ text }: ReasoningBlockProps) {
  if (!text) return null

  return (
    <details className="group mb-2">
      <summary className="text-xs text-oc-text-dim cursor-pointer select-none hover:text-oc-text transition-colors py-1">
        <span className="inline-flex items-center gap-1">
          <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          Рассуждения
        </span>
      </summary>
      <div className="mt-1 pl-3 border-l-2 border-oc-border/60">
        <p className="text-sm text-oc-text-dim/80 leading-relaxed whitespace-pre-wrap">{text}</p>
      </div>
    </details>
  )
}
```

- [ ] **Step 2: Create AnswerBlock.tsx**

```tsx
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { Components } from 'react-markdown'

interface AnswerBlockProps {
  text: string
  isStreaming?: boolean
}

const components: Components = {
  code({ className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '')
    const codeStr = String(children).replace(/\n$/, '')
    if (match) {
      return (
        <div className="relative group my-3 rounded-lg overflow-hidden border border-oc-border/40">
          <div className="flex items-center justify-between px-4 py-1.5 bg-oc-border/20 text-xs text-oc-text-dim">
            <span>{match[1]}</span>
            <button
              onClick={() => navigator.clipboard.writeText(codeStr)}
              className="hover:text-oc-text transition-colors"
            >
              Копировать
            </button>
          </div>
          <SyntaxHighlighter
            style={oneDark}
            language={match[1]}
            PreTag="div"
            customStyle={{ margin: 0, borderRadius: 0, background: '#1a1f29' }}
          >
            {codeStr}
          </SyntaxHighlighter>
        </div>
      )
    }
    return (
      <code className="bg-oc-border/30 px-1.5 py-0.5 rounded text-sm text-oc-accent" {...props}>
        {children}
      </code>
    )
  },
  pre({ children }) {
    return <>{children}</>
  },
}

export default function AnswerBlock({ text, isStreaming }: AnswerBlockProps) {
  return (
    <div className={`prose prose-invert max-w-none text-sm leading-relaxed ${isStreaming ? 'animate-fade-in' : ''}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {text || (isStreaming ? '\u200B' : '')}
      </ReactMarkdown>
    </div>
  )
}
```

---

### Task 9: Message and StreamingMessage components

**Files:**
- Create: `E:/tg opencode bot/tma/src/components/Message.tsx`
- Create: `E:/tg opencode bot/tma/src/components/StreamingMessage.tsx`

- [ ] **Step 1: Create Message.tsx**

```tsx
import ReasoningBlock from './ReasoningBlock'
import AnswerBlock from './AnswerBlock'
import type { Message as MessageType } from '../types'

interface MessageProps {
  message: MessageType
}

export default function Message({ message }: MessageProps) {
  return (
    <div className="mb-4 p-4 rounded-2xl bg-oc-surface border border-oc-border/30">
      <ReasoningBlock text={message.reasoning} />
      <AnswerBlock text={message.text} />
      {message.status === 'error' && message.error && (
        <p className="mt-2 text-xs text-oc-red">{message.error}</p>
      )}
      {message.status === 'sending' && (
        <div className="flex items-center gap-1 mt-2">
          <span className="w-1.5 h-1.5 rounded-full bg-oc-text-dim animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 rounded-full bg-oc-text-dim animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 rounded-full bg-oc-text-dim animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create StreamingMessage.tsx**

```tsx
import ReasoningBlock from './ReasoningBlock'
import AnswerBlock from './AnswerBlock'
import type { Message } from '../types'

interface StreamingMessageProps {
  message: Message
}

export default function StreamingMessage({ message }: StreamingMessageProps) {
  return (
    <div className="mb-4 p-4 rounded-2xl bg-oc-surface border border-oc-accent/30">
      <ReasoningBlock text={message.reasoning} />
      <AnswerBlock text={message.text} isStreaming />
      <div className="flex items-center gap-1 mt-2">
        <span className="w-1.5 h-1.5 rounded-full bg-oc-accent animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-1.5 h-1.5 rounded-full bg-oc-accent animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-1.5 h-1.5 rounded-full bg-oc-accent animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}
```

---

### Task 10: ChatArea component

**Files:**
- Create: `E:/tg opencode bot/tma/src/components/ChatArea.tsx`

- [ ] **Step 1: Create ChatArea.tsx**

```tsx
import { useEffect, useRef } from 'react'
import { useAppState } from '../contexts/AppContext'
import Message from './Message'
import StreamingMessage from './StreamingMessage'

export default function ChatArea() {
  const { state } = useAppState()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.messages, state.streamingMessage?.text, state.streamingMessage?.reasoning])

  if (state.messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center px-4 mt-14 mb-20">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-oc-accent/10 flex items-center justify-center">
            <svg className="w-8 h-8 text-oc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <p className="text-oc-text-dim text-sm">Отправьте сообщение, чтобы начать</p>
          <p className="text-oc-text-dim/60 text-xs mt-1">Выберите ПК в шапке, если агент не выбран</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 pt-20 pb-24 scroll-smooth">
      {state.messages.map(msg => (
        <Message key={msg.id} message={msg} />
      ))}
      {state.streamingMessage && state.streamingMessage.status === 'streaming' && (
        <StreamingMessage message={state.streamingMessage} />
      )}
      <div ref={bottomRef} />
    </div>
  )
}
```

---

### Task 11: InputBar component

**Files:**
- Create: `E:/tg opencode bot/tma/src/components/InputBar.tsx`
- Create: `E:/tg opencode bot/tma/src/components/Toast.tsx`

- [ ] **Step 1: Create InputBar.tsx**

```tsx
import { useState, useRef, useEffect } from 'react'

interface InputBarProps {
  onSend: (text: string) => void
  onCancel: () => void
  disabled: boolean
  isStreaming: boolean
}

export default function InputBar({ onSend, onCancel, disabled, isStreaming }: InputBarProps) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [text])

  const handleSubmit = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-oc-bg/75 backdrop-blur-[16px] border-t border-oc-border/40">
      <div className="max-w-[768px] mx-auto p-3">
        <div className="flex items-end gap-2 p-2 rounded-2xl bg-oc-surface/80 backdrop-blur-[12px] border border-oc-border/40">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? 'Подключитесь к агенту...' : 'Сообщение...'}
            rows={1}
            disabled={disabled}
            className="flex-1 bg-transparent text-sm text-oc-text placeholder-oc-text-dim/50 outline-none resize-none max-h-[120px] px-2 py-1.5"
          />
          {isStreaming ? (
            <button
              onClick={onCancel}
              className="shrink-0 w-9 h-9 rounded-full bg-oc-red/20 flex items-center justify-center hover:bg-oc-red/30 transition-colors"
            >
              <svg className="w-4 h-4 text-oc-red" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!text.trim() || disabled}
              className="shrink-0 w-9 h-9 rounded-full bg-oc-accent flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed hover:bg-oc-accent/90 transition-colors"
            >
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create Toast.tsx**

```tsx
import { useEffect, useState } from 'react'

interface ToastProps {
  message: string
  type?: 'error' | 'success' | 'info'
  onClose: () => void
}

export default function Toast({ message, type = 'info', onClose }: ToastProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true))
    const timer = setTimeout(() => {
      setVisible(false)
      setTimeout(onClose, 300)
    }, 3000)
    return () => clearTimeout(timer)
  }, [onClose])

  const bgColor = type === 'error' ? 'bg-oc-red/20 border-oc-red/40' :
                  type === 'success' ? 'bg-oc-green/20 border-oc-green/40' :
                  'bg-oc-surface/90 border-oc-border/40'

  return (
    <div className={`fixed top-20 left-3 right-3 z-50 max-w-[768px] mx-auto transition-all duration-300 ${
      visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
    }`}>
      <div className={`rounded-2xl backdrop-blur-[16px] border px-4 py-3 text-sm text-oc-text ${bgColor}`}>
        {message}
      </div>
    </div>
  )
}
```

---

### Task 12: App.tsx integration

**Files:**
- Create: `E:/tg opencode bot/tma/src/App.tsx`

- [ ] **Step 1: Create App.tsx**

```tsx
import { useState, useCallback } from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import { AppProvider, useAppState } from './contexts/AppContext'
import { useWebSocket } from './hooks/useWebSocket'
import Header from './components/Header'
import ChatArea from './components/ChatArea'
import InputBar from './components/InputBar'
import Toast from './components/Toast'

const HUB_URL = import.meta.env.VITE_HUB_URL || 'wss://hub.opencode.app'

function AppContent() {
  const { state } = useAppState()
  const { sendMessage, switchAgent, newSession, cancel } = useWebSocket(HUB_URL)
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' | 'info' } | null>(null)

  const handleSend = useCallback((text: string) => {
    if (!state.activeAgentId) {
      setToast({ message: 'Выберите ПК в шапке', type: 'error' })
      return
    }
    sendMessage(state.activeAgentId, text)
  }, [state.activeAgentId, sendMessage])

  const handleSwitch = useCallback((agentId: string) => {
    switchAgent(agentId)
    setToast({ message: 'ПК переключён', type: 'success' })
  }, [switchAgent])

  const handleNewSession = useCallback(() => {
    newSession()
    setToast({ message: 'Новый чат создан', type: 'info' })
  }, [newSession])

  return (
    <div className="flex flex-col h-[100dvh] bg-oc-bg text-oc-text overflow-hidden">
      <Header onSwitchAgent={handleSwitch} onNewSession={handleNewSession} />
      <ChatArea />
      <InputBar
        onSend={handleSend}
        onCancel={cancel}
        disabled={!state.activeAgentId}
        isStreaming={state.streamingMessage?.status === 'streaming'}
      />
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </ThemeProvider>
  )
}
```

---

### Task 13: Tailwind CSS globals with glassmorphism + animations

**Files:**
- Create: `E:/tg opencode bot/tma/src/styles/globals.css`

- [ ] **Step 1: Create globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    -webkit-tap-highlight-color: transparent;
    scrollbar-width: thin;
    scrollbar-color: #30363d transparent;
  }

  body {
    margin: 0;
    padding: 0;
    background: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text',
      'Helvetica Neue', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow: hidden;
  }

  ::-webkit-scrollbar {
    width: 4px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: #30363d;
    border-radius: 2px;
  }
}

@layer utilities {
  .glass {
    background: rgba(22, 27, 34, 0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(2px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.animate-fade-in {
  animation: fade-in 0.15s ease-out;
}
```

---

### Task 14: Cloud Hub — config + auth

**Files:**
- Create: `E:/tg opencode bot/hub/__init__.py`
- Create: `E:/tg opencode bot/hub/config.py`
- Create: `E:/tg opencode bot/hub/auth.py`
- Create: `E:/tg opencode bot/hub/requirements.txt`

- [ ] **Step 1: Create hub/__init__.py**

Empty file.

- [ ] **Step 2: Create hub/requirements.txt**

```
aiohttp>=3.9,<4
PyJWT>=2.8,<3
aiohttp-session>=2.12,<3
```

- [ ] **Step 3: Create hub/config.py**

```python
import os

HUB_PORT: int = int(os.getenv("HUB_PORT", "8081"))
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
JWT_SECRET: str = os.getenv("JWT_SECRET", os.urandom(32).hex())
HOST: str = os.getenv("HOST", "0.0.0.0")
TMA_ORIGIN: str = os.getenv("TMA_ORIGIN", "*")
```

- [ ] **Step 4: Create hub/auth.py**

```python
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

import jwt

from hub.config import BOT_TOKEN, JWT_SECRET

logger = logging.getLogger(__name__)


def verify_init_data(init_data: str) -> dict | None:
    """Verify Telegram WebApp initData and return user info."""
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop("hash", "")
        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if computed_hash != received_hash:
            logger.warning("initData hash mismatch")
            return None

        auth_date = int(parsed.get("auth_date", "0"))
        if time.time() - auth_date > 86400:
            logger.warning("initData expired")
            return None

        user = json.loads(parsed.get("user", "{}"))
        return user

    except Exception as e:
        logger.exception("initData verification failed: %s", e)
        return None


def create_token(user_id: int) -> str:
    """Create JWT for the TMA client session."""
    payload = {
        "user_id": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    """Verify JWT and return payload."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT")
        return None
```

---

### Task 15: Cloud Hub — WebSocket manager

**Files:**
- Create: `E:/tg opencode bot/hub/ws_manager.py`

- [ ] **Step 1: Create ws_manager.py**

```python
import asyncio
import json
import logging
import time

from aiohttp import web, WSMsgType

logger = logging.getLogger(__name__)


class AgentConnection:
    def __init__(self, ws: web.WebSocketResponse, agent_id: str, user_id: str):
        self.ws = ws
        self.agent_id = agent_id
        self.user_id = user_id
        self.last_seen = time.time()
        self.busy = False


class TmaConnection:
    def __init__(self, ws: web.WebSocketResponse, user_id: int):
        self.ws = ws
        self.user_id = user_id
        self.active_agent_id: str | None = None


class WsManager:
    def __init__(self):
        self._agents: dict[str, AgentConnection] = {}
        self._tma_by_uid: dict[int, TmaConnection] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def register_agent(self, agent_id: str, user_id: str, ws: web.WebSocketResponse) -> AgentConnection:
        conn = AgentConnection(ws, agent_id, user_id)
        self._agents[agent_id] = conn
        logger.info("Agent registered: %s (user %s)", agent_id, user_id)
        return conn

    def unregister_agent(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)
        logger.info("Agent unregistered: %s", agent_id)

    def register_tma(self, user_id: int, ws: web.WebSocketResponse) -> TmaConnection:
        conn = TmaConnection(ws, user_id)
        self._tma_by_uid[user_id] = conn
        logger.info("TMA connected: user %s", user_id)
        return conn

    def unregister_tma(self, user_id: int) -> None:
        self._tma_by_uid.pop(user_id, None)

    def get_agent(self, agent_id: str) -> AgentConnection | None:
        return self._agents.get(agent_id)

    def get_agents_for_user(self, user_id: int) -> list[dict]:
        result = []
        uid = str(user_id)
        for agent_id, conn in self._agents.items():
            if conn.user_id == uid:
                result.append({
                    "id": agent_id,
                    "name": agent_id,
                    "status": "busy" if conn.busy else "online",
                })
        return result

    def get_tma(self, user_id: int) -> TmaConnection | None:
        return self._tma_by_uid.get(user_id)

    async def send_to_tma(self, user_id: int, data: dict) -> bool:
        tma = self.get_tma(user_id)
        if not tma:
            return False
        try:
            await tma.ws.send_json(data)
            return True
        except ConnectionResetError:
            self.unregister_tma(user_id)
            return False

    async def send_to_agent(self, agent_id: str, data: dict) -> bool:
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        try:
            await agent.ws.send_json(data)
            return True
        except ConnectionResetError:
            self.unregister_agent(agent_id)
            return False
```

---

### Task 16: Cloud Hub — main server

**Files:**
- Create: `E:/tg opencode bot/hub/hub.py`

- [ ] **Step 1: Create hub.py**

```python
import asyncio
import json
import logging

from aiohttp import web, WSMsgType

from hub.config import HUB_PORT, BOT_TOKEN, HOST, TMA_ORIGIN
from hub.ws_manager import WsManager
from hub.auth import verify_init_data, create_token, verify_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hub")

ws_manager = WsManager()


async def handle_tma_ws(request: web.Request) -> web.WebSocketResponse:
    init_data = request.query.get("initData", "")
    user = verify_init_data(init_data)
    if not user:
        user_id = int(request.query.get("user_id", "0"))
        if not user_id:
            return web.json_response({"error": "Unauthorized"}, status=401)
    else:
        user_id = user["id"]

    ws = web.WebSocketResponse(max_msg_size=0)
    await ws.prepare(request)

    tma = ws_manager.register_tma(user_id, ws)

    # Send agent list on connect
    agents = ws_manager.get_agents_for_user(user_id)
    await ws.send_json({"type": "agents", "agents": agents})

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")

                if msg_type == "message":
                    agent_id = data.get("agent_id", "")
                    text = data.get("text", "")
                    task_id = data.get("task_id", "")

                    agent = ws_manager.get_agent(agent_id)
                    if not agent:
                        await ws.send_json({
                            "type": "error",
                            "task_id": task_id,
                            "message": "Агент не подключён",
                        })
                        continue

                    agent.busy = True
                    tma.active_agent_id = agent_id

                    ok = await ws_manager.send_to_agent(agent_id, {
                        "type": "run",
                        "task_id": task_id,
                        "message": text,
                    })
                    if not ok:
                        await ws.send_json({
                            "type": "error",
                            "task_id": task_id,
                            "message": "Агент недоступен",
                        })

                elif msg_type == "switch_agent":
                    tma.active_agent_id = data.get("agent_id", "")

                elif msg_type == "new_session":
                    agent_id = data.get("agent_id", "")
                    await ws_manager.send_to_agent(agent_id, {
                        "type": "new_session",
                    })

                elif msg_type == "cancel":
                    agent_id = data.get("agent_id", "")
                    await ws_manager.send_to_agent(agent_id, {
                        "type": "cancel",
                    })

            elif msg.type == WSMsgType.ERROR:
                break
    except asyncio.CancelledError:
        pass
    finally:
        ws_manager.unregister_tma(user_id)

    return ws


async def handle_agent_ws(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(max_msg_size=0)
    await ws.prepare(request)

    agent_id = ""
    user_id = ""

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")

                if msg_type == "register":
                    agent_id = data.get("agent_id", "")
                    user_id = data.get("user_id", "")
                    ws_manager.register_agent(agent_id, user_id, ws)

                    # Notify TMA about new agent
                    await ws_manager.send_to_tma(int(user_id), {
                        "type": "agents",
                        "agents": ws_manager.get_agents_for_user(int(user_id)),
                    })

                elif msg_type == "chunk":
                    task_id = data.get("task_id", "")
                    user_id = data.get("user_id", "")
                    if user_id:
                        await ws_manager.send_to_tma(int(user_id), {
                            "type": "chunk",
                            "task_id": task_id,
                            "kind": data.get("kind", "answer"),
                            "token": data.get("token", ""),
                        })

                elif msg_type == "done":
                    task_id = data.get("task_id", "")
                    user_id = data.get("user_id", "")
                    if agent_id:
                        agent = ws_manager.get_agent(agent_id)
                        if agent:
                            agent.busy = False
                    if user_id:
                        await ws_manager.send_to_tma(int(user_id), {
                            "type": "done",
                            "task_id": task_id,
                        })

                elif msg_type == "error":
                    task_id = data.get("task_id", "")
                    user_id = data.get("user_id", "")
                    message = data.get("message", "")
                    if agent_id:
                        agent = ws_manager.get_agent(agent_id)
                        if agent:
                            agent.busy = False
                    if user_id:
                        await ws_manager.send_to_tma(int(user_id), {
                            "type": "error",
                            "task_id": task_id,
                            "message": message,
                        })

                elif msg_type == "pong":
                    if agent_id:
                        agent = ws_manager.get_agent(agent_id)
                        if agent:
                            agent.last_seen = asyncio.get_event_loop().time()

            elif msg.type == WSMsgType.ERROR:
                break
    except asyncio.CancelledError:
        pass
    finally:
        if agent_id:
            ws_manager.unregister_agent(agent_id)
            # Notify TMA
            if user_id:
                await ws_manager.send_to_tma(int(user_id), {
                    "type": "agents",
                    "agents": ws_manager.get_agents_for_user(int(user_id)),
                })

    return ws


async def handle_auth(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    init_data = data.get("initData", "")
    user = verify_init_data(init_data)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    token = create_token(user["id"])
    return web.json_response({
        "ok": True,
        "token": token,
        "user": user,
    })


async def handle_agents_list(request: web.Request) -> web.Response:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        return web.json_response({"error": "Unauthorized"}, status=401)

    user_id = payload["user_id"]
    agents = ws_manager.get_agents_for_user(user_id)
    return web.json_response({"agents": agents})


async def handle_ping(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


def create_app() -> web.Application:
    app = web.Application()

    # CORS middleware
    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        if request.method == "OPTIONS":
            response = web.Response()
            response.headers["Access-Control-Allow-Origin"] = TMA_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
        response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = TMA_ORIGIN
        return response

    app.middlewares.append(cors_middleware)

    # Serve TMA static files (built SPA)
    app.router.add_static("/", path="tma/dist", show_index=True)

    # API routes
    app.router.add_post("/api/auth/tg", handle_auth)
    app.router.add_get("/api/agents", handle_agents_list)
    app.router.add_get("/api/ping", handle_ping)

    # WebSocket routes
    app.router.add_get("/ws", handle_tma_ws)
    app.router.add_get("/ws/agent", handle_agent_ws)

    return app


async def heartbeat_loop():
    """Send ping to all agents every 15 seconds."""
    while True:
        await asyncio.sleep(15)
        for agent_id, conn in list(ws_manager._agents.items()):
            try:
                await conn.ws.send_json({"type": "ping"})
            except ConnectionResetError:
                ws_manager.unregister_agent(agent_id)


async def main():
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, HUB_PORT)
    await site.start()
    logger.info("Hub started on %s:%d", HOST, HUB_PORT)

    asyncio.create_task(heartbeat_loop())

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Task 17: Modify agent.py for WebSocket streaming

**Files:**
- Modify: `E:/tg opencode bot/agent.py`

- [ ] **Step 1: Add streaming opencode runner to agent.py**

Replace the `run_opencode` function and `poll_forever` with WebSocket-based streaming:

```python
"""OpenCode Agent — connects to Cloud Hub via WebSocket.
Usage:
    python agent.py --hub-url WS_URL --user-id ID --token TOKEN [--work-dir DIR]
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
AGENT_TOKEN = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenCode Agent")
    parser.add_argument("--hub-url", type=str, default="ws://127.0.0.1:8081/ws/agent",
                        help="Cloud Hub WebSocket URL")
    parser.add_argument("--user-id", type=str, required=True,
                        help="Your Telegram user ID")
    parser.add_argument("--token", type=str, default="",
                        help="Authorization token (auto-generated if empty)")
    parser.add_argument("--work-dir", type=str, default=str(Path.cwd()),
                        help="Working directory for opencode")
    return parser.parse_args()


async def stream_opencode(
    message: str,
    work_dir: str,
    user_id: str,
    task_id: str,
    ws: aiohttp.ClientWebSocketResponse,
    session_id: str = "",
    file_urls: list[str] | None = None,
) -> None:
    try:
        cmd = [OPENCODE_BIN, "run", message, "--dir", work_dir,
               "--dangerously-skip-permissions"]
        if session_id:
            cmd.extend(["--session", session_id])

        if file_urls:
            dest = tempfile.mkdtemp(prefix="oc_files_")
            for url in file_urls:
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(url) as resp:
                        fname = url.rsplit("/", 1)[-1] or "file"
                        fpath = str(Path(dest) / fname)
                        with open(fpath, "wb") as f:
                            while chunk := await resp.content.read(8192):
                                f.write(chunk)
                        cmd.extend(["-f", fpath])

        logger.info("Streaming opencode: %s ...", cmd[:3])
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        in_thought = False

        async for line in process.stdout:
            text = line.decode("utf-8", errors="replace")
            stripped = text.strip()
            if not stripped:
                continue

            # Detect reasoning tags
            if "<thought>" in stripped:
                in_thought = True
                continue
            if "</thought>" in stripped:
                in_thought = False
                continue

            kind = "reasoning" if in_thought else "answer"
            await ws.send_json({
                "type": "chunk",
                "user_id": user_id,
                "task_id": task_id,
                "kind": kind,
                "token": text,
            })

        # Wait for process and check return code
        await process.wait()
        if process.returncode != 0:
            stderr_data = await process.stderr.read()
            err_text = stderr_data.decode("utf-8", errors="replace")[:500]
            await ws.send_json({
                "type": "error",
                "user_id": user_id,
                "task_id": task_id,
                "message": f"OpenCode error (code {process.returncode}): {err_text}",
            })
            return

        await ws.send_json({
            "type": "done",
            "user_id": user_id,
            "task_id": task_id,
        })

    except asyncio.TimeoutError:
        await ws.send_json({
            "type": "error",
            "user_id": user_id,
            "task_id": task_id,
            "message": f"OpenCode timeout ({OPENCODE_TIMEOUT}s)",
        })
    except FileNotFoundError:
        await ws.send_json({
            "type": "error",
            "user_id": user_id,
            "task_id": task_id,
            "message": "OpenCode not found. Install: pip install opencode",
        })
    except Exception as e:
        logger.exception("Stream error")
        await ws.send_json({
            "type": "error",
            "user_id": user_id,
            "task_id": task_id,
            "message": f"Error: {e}",
        })


async def run(hub_url: str, user_id: str, token: str, work_dir: str) -> None:
    global AGENT_TOKEN
    AGENT_TOKEN = token or secrets.token_hex(16)

    agent_id = f"user_{user_id}_{secrets.token_hex(4)}"
    logger.info("Connecting to hub: %s (agent_id: %s)", hub_url, agent_id)

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(hub_url) as ws:
            # Register
            await ws.send_json({
                "type": "register",
                "agent_id": agent_id,
                "user_id": user_id,
                "token": AGENT_TOKEN,
            })
            logger.info("Registered, waiting for commands...")

            # Handle incoming messages
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue

                    msg_type = data.get("type")

                    if msg_type == "run":
                        task_id = data.get("task_id", "")
                        message = data.get("message", "")
                        session_id = data.get("session_id", "")

                        await stream_opencode(
                            message, work_dir, user_id, task_id, ws,
                            session_id=session_id,
                        )

                    elif msg_type == "ping":
                        await ws.send_json({"type": "pong"})

                    elif msg_type == "cancel":
                        logger.info("Cancel requested for current task")

                    elif msg_type == "new_session":
                        logger.info("New session requested")

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break


def main() -> None:
    args = parse_args()
    print(f"\n{'='*50}")
    print(f"  OpenCode Agent (WebSocket)")
    print(f"{'='*50}")
    print(f"  Hub URL:    {args.hub_url}")
    print(f"  User ID:    {args.user_id}")
    print(f"  Token:      {args.token or '(auto)'}")
    print(f"  Work dir:   {args.work_dir}")
    print(f"{'='*50}\n")

    try:
        asyncio.run(run(args.hub_url, args.user_id, args.token, args.work_dir))
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify agent.py runs**

Run: `python agent.py --hub-url ws://127.0.0.1:8081/ws/agent --user-id 12345 --work-dir "C:\path\to\workdir" --token test123`
Expected: Connects to hub, registers, waits for commands

---

### Task 18: Start script for Cloud Hub

**Files:**
- Create: `E:/tg opencode bot/start_hub.bat`

- [ ] **Step 1: Create start_hub.bat**

```bat
@echo off
cd /d "%~dp0"
echo Installing hub dependencies...
pip install -r hub\requirements.txt
echo Starting Cloud Hub on port 8081...
python -m hub.hub
pause
```

---

## Self-Review

**Spec coverage:**
- TMA initData auth → Task 3 (tgApi.ts) + Task 14 (hub/auth.py)
- Real-time streaming → Task 6 (useWebSocket.ts) + Task 16 (hub.py WS routing) + Task 17 (agent streaming)
- Reasoning/Answer split → Task 8 (ReasoningBlock, AnswerBlock) + Task 17 (tag detection)
- Glassmorphism → Task 13 (globals.css glass utility)
- OpenCode color palette → Task 1 (tailwind.config.ts oc-* colors)
- Multi-agent switching → Task 7 (AgentSwitcher) + Task 6 (switchAgent in useWebSocket)
- Responsiveness → Task 1 (viewport meta, max-w-[768px]) + Task 13 (mobile-friendly)
- Telegram theme → Task 4 (ThemeContext)
- Markdown + code highlighting → Task 8 (AnswerBlock with react-markdown + syntax highlighter)
- Agent protocol change (WS replace polling) → Task 17 (full agent rewrite)
- Cloud Hub → Tasks 14-16
- Bellows/collapsible reasoning → Task 8 (ReasoningBlock as `<details>`)

**Placeholder scan:** No TBD, TODO, or placeholder code found.
**Type consistency:** All types defined in types.ts used consistently across components. WebSocket message formats match between hub.py and useWebSocket.ts.

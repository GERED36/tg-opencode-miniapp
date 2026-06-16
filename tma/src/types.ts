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

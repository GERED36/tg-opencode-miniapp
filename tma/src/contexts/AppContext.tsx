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

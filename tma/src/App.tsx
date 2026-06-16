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

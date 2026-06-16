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

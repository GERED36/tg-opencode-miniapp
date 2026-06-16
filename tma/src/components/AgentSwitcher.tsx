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

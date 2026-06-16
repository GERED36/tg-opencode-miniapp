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

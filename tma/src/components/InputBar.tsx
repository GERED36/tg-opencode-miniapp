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

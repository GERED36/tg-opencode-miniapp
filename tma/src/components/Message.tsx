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

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

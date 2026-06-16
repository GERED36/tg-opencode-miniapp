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

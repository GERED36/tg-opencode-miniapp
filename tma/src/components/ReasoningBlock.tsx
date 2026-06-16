interface ReasoningBlockProps {
  text: string
}

export default function ReasoningBlock({ text }: ReasoningBlockProps) {
  if (!text) return null

  return (
    <details className="group mb-2">
      <summary className="text-xs text-oc-text-dim cursor-pointer select-none hover:text-oc-text transition-colors py-1">
        <span className="inline-flex items-center gap-1">
          <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          Рассуждения
        </span>
      </summary>
      <div className="mt-1 pl-3 border-l-2 border-oc-border/60">
        <p className="text-sm text-oc-text-dim/80 leading-relaxed whitespace-pre-wrap">{text}</p>
      </div>
    </details>
  )
}

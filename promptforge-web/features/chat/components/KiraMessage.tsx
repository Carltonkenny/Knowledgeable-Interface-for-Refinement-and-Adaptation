// features/chat/components/KiraMessage.tsx
// Kira message with avatar

interface KiraMessageProps {
  message: string
  isError?: boolean
  isStreaming?: boolean
  retryable?: boolean
  onRetry?: () => void
}

export default function KiraMessage({
  message,
  isError,
  isStreaming,
  retryable,
  onRetry,
}: KiraMessageProps) {
  // Parse simple bold markdown (**text**)
  const parseBold = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-text-bright font-semibold">{part.slice(2, -2)}</strong>
      }
      return part
    })
  }

  return (
    <div className={`flex gap-3 mb-4 ${isError ? 'border border-intent/20 bg-intent/5 rounded-xl p-4' : ''}`}>
      {/* Kira Avatar */}
      <div className="w-7 h-7 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center flex-shrink-0">
        <span className="text-kira font-bold font-mono text-sm">K</span>
      </div>

      {/* Message */}
      <div className="flex-1">
        <p className="text-text-default text-sm leading-relaxed">
          {parseBold(message)}
          {isStreaming && <span className="inline-block w-0.5 h-4 bg-kira ml-1 animate-pulse" />}
        </p>

        {/* Retry button */}
        {isError && retryable && (
          <button
            onClick={onRetry}
            className="mt-2 text-xs text-kira hover:underline font-medium"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  )
}

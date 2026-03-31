// features/chat/components/EmptyState.tsx
// First-visit empty state with suggestions

interface EmptyStateProps {
  domain?: string
  onSuggestionClick: (text: string) => void
}

export default function EmptyState({ domain, onSuggestionClick }: EmptyStateProps) {
  // Domain-aware suggestions
  const suggestions = domain
    ? domainSuggestions[(domain || '').toLowerCase()] || defaultSuggestions
    : defaultSuggestions

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6">
      {/* Kira avatar */}
      <div className="w-16 h-16 rounded-xl border border-kira bg-[var(--kira-dim)] flex items-center justify-center mb-6">
        <span className="text-kira font-bold font-mono text-3xl">K</span>
      </div>

      {/* Welcome message */}
      <p className="text-text-default text-base mb-8 max-w-md">
        {domain
          ? `${domain} mode — ready. **Paste a rough idea and I'll engineer it into a precise prompt.**`
          : "Ready when you are. **Paste a rough idea and I'll turn it into a production-grade prompt.**"}
      </p>

      {/* Suggestion cards */}
      <div className="w-full max-w-lg space-y-3">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSuggestionClick(suggestion)}
            className="w-full p-4 rounded-xl border border-border-default bg-layer2 hover:border-kira hover:bg-[var(--kira-glow)] transition-all text-left group"
          >
            <div className="flex items-center justify-between">
              <span className="text-text-default text-sm">{suggestion}</span>
              <span className="text-kira opacity-0 group-hover:opacity-100 transition-opacity">→</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

const defaultSuggestions = [
  "Turn this rough idea into a structured prompt",
  "Make my instructions more specific and actionable",
  "Write a system prompt for a chatbot",
]

const domainSuggestions: Record<string, string[]> = {
  writing: [
    "Write a cold outreach email for a SaaS product",
    "Improve this product launch announcement",
    "Help me write a LinkedIn post about...",
  ],
  code: [
    "Help me write a code review for this PR",
    "Write tests for this function",
    "Help me document this API endpoint",
  ],
  marketing: [
    "Write ad copy for a new feature launch",
    "Create a social media content calendar",
    "Write a case study outline",
  ],
  research: [
    "Summarize the key points in this paper",
    "Write a literature review section on...",
    "Help me structure a research report",
  ],
}

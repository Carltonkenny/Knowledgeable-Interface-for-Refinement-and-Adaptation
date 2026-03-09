// features/profile/components/McpTokenSection.tsx
// MCP token generation (placeholder for Phase 5)

interface McpTokenSectionProps {
  sessionCount: number
  trustLevel: 0 | 1 | 2
}

export default function McpTokenSection({ sessionCount, trustLevel }: McpTokenSectionProps) {
  const trustLabels = {
    0: { label: 'COLD', color: 'text-text-dim' },
    1: { label: 'WARM', color: 'text-domain' },
    2: { label: 'TUNED', color: 'text-success' },
  }

  const { label, color } = trustLabels[trustLevel]

  return (
    <div className="border-t border-border-subtle pt-6">
      <h3 className="font-mono text-[10px] tracking-wider uppercase text-text-dim mb-4">
        MCP Integration
      </h3>

      {/* Trust level badge */}
      <div className="mb-4 p-3 rounded-lg bg-layer2 border border-border-strong">
        <div className="flex items-center gap-2 mb-2">
          <div className={`w-2 h-2 rounded-full ${
            trustLevel === 2 ? 'bg-success' :
            trustLevel === 1 ? 'bg-domain' :
            'bg-text-dim'
          }`} />
          <span className={`font-mono text-[10px] ${color}`}>
            {label} ({sessionCount} sessions)
          </span>
        </div>
        <p className="text-text-dim text-sm">
          {trustLevel === 0 && "Keep using the app, I'll get sharper in MCP too."}
          {trustLevel === 1 && "You're getting warm. More sessions = better MCP integration."}
          {trustLevel === 2 && "Full MCP access available. Generate your token below."}
        </p>
      </div>

      {/* Generate token button */}
      {trustLevel === 2 ? (
        <div>
          <button className="w-full py-2.5 bg-kira text-white rounded-lg font-medium hover:bg-kira/90 transition-colors">
            Generate MCP token
          </button>
          <p className="mt-2 text-[10px] font-mono text-text-dim">
            ⚠️ Copy this now — it won't be shown again
          </p>
        </div>
      ) : (
        <button
          disabled
          className="w-full py-2.5 bg-layer2 text-text-dim rounded-lg font-medium cursor-not-allowed"
        >
          Available at Tuned level
        </button>
      )}

      <p className="mt-4 text-[10px] font-mono text-text-dim">
        Token stored as hash only · Revocable anytime
      </p>
    </div>
  )
}

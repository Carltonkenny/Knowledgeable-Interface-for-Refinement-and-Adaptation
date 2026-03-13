// features/history/components/HistoryCard.tsx
// Single prompt history entry

import type { HistoryItem } from '@/lib/api'

interface HistoryCardProps {
  item: HistoryItem
  onUseAgain: (prompt: string) => void
}

export default function HistoryCard({ item, onUseAgain }: HistoryCardProps) {
  return (
    <div className="p-4 rounded-xl border border-border-default hover:border-border-strong bg-layer2 transition-colors">
      {/* Original prompt */}
      <p className="text-text-dim text-xs italic mb-2 line-clamp-1">
        {item.original_prompt}
      </p>

      {/* Improved prompt */}
      <p className="text-text-default text-sm mb-3 line-clamp-2">
        {item.improved_prompt}
      </p>

      {/* Meta row */}
      <div className="flex items-center justify-between">
        {/* Score pills — with null safety guard */}
        {item.quality_score ? (
          <div className="flex gap-2">
            <span className="bg-[var(--kira-dim)] text-kira font-mono text-[10px] px-1.5 py-0.5 rounded">
              Spec {item.quality_score.specificity ?? 0}
            </span>
            <span className="bg-[var(--kira-dim)] text-kira font-mono text-[10px] px-1.5 py-0.5 rounded">
              Clar {item.quality_score.clarity ?? 0}
            </span>
            <span className="bg-[var(--kira-dim)] text-kira font-mono text-[10px] px-1.5 py-0.5 rounded">
              Act {item.quality_score.actionability ?? 0}
            </span>
          </div>
        ) : (
          <span className="text-text-dim text-[10px]">No score</span>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={() => {
              navigator.clipboard.writeText(item.improved_prompt)
            }}
            className="text-xs text-text-dim hover:text-text-bright"
          >
            Copy
          </button>
          <button
            onClick={() => onUseAgain(item.original_prompt)}
            className="text-xs text-kira hover:underline font-medium"
          >
            Use again →
          </button>
        </div>
      </div>
    </div>
  )
}

// features/chat/components/QualityScores.tsx
// 3 score bars (specificity, clarity, actionability)

import type { QualityScore } from '@/lib/api'

interface QualityScoresProps {
  scores: QualityScore
}

export default function QualityScores({ scores }: QualityScoresProps) {
  // Type guard per RULES.md type safety standards
  if (!scores || typeof scores !== 'object') return null
  if (typeof scores.specificity !== 'number') return null
  if (typeof scores.clarity !== 'number') return null
  if (typeof scores.actionability !== 'number') return null

  const items = [
    { label: 'Specificity', value: scores.specificity ?? 0 },
    { label: 'Clarity', value: scores.clarity ?? 0 },
    { label: 'Actionability', value: scores.actionability ?? 0 },
  ]

  return (
    <div className="space-y-4 mt-4">
      <div className="flex items-center gap-2 group relative">
        <h4 className="text-[10px] font-bold text-text-dim uppercase tracking-widest">
          Prompt Quality
        </h4>
        {/* Tooltip */}
        <div className="w-3 h-3 rounded-full border border-text-dim/50 text-text-dim/50 flex items-center justify-center text-[8px] cursor-help">
          ?
        </div>
        <div className="absolute left-0 bottom-full mb-2 w-48 p-2 bg-layer3 border border-border-strong rounded-md text-[10px] text-text-dim opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
          Measures the quality of the engineered prompt, not your original input.
        </div>
      </div>
      
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-3">
            <span className="font-mono text-[10px] text-text-dim w-24 flex-shrink-0">
              {item.label}
            </span>
            <div className="flex-1 h-[3px] bg-border-default rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-kira transition-all duration-700 ease-out"
                style={{ width: `${(item.value / 5) * 100}%` }}
              />
            </div>
            <span className="font-mono text-[10px] text-text-dim w-6 text-right">
              {item.value}/5
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

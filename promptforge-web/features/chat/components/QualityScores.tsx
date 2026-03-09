// features/chat/components/QualityScores.tsx
// 3 score bars (specificity, clarity, actionability)

import type { QualityScore } from '@/lib/api'

interface QualityScoresProps {
  scores: QualityScore
}

export default function QualityScores({ scores }: QualityScoresProps) {
  const items = [
    { label: 'Specificity', value: scores.specificity },
    { label: 'Clarity', value: scores.clarity },
    { label: 'Actionability', value: scores.actionability },
  ]

  return (
    <div className="space-y-2 mt-4">
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
  )
}

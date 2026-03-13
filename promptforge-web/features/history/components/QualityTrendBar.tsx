// features/history/components/QualityTrendBar.tsx
// Weekly stat sparkline (placeholder)

import type { HistoryItem } from '@/lib/api'

interface QualityTrendBarProps {
  items: HistoryItem[]
}

export default function QualityTrendBar({ items }: QualityTrendBarProps) {
  // Filter items with valid quality_score
  const itemsWithScores = items.filter(
    (item) => item.quality_score && typeof item.quality_score === 'object'
  )

  if (itemsWithScores.length < 5) {
    return null // Not enough data
  }

  // Calculate average specificity trend
  const last12 = itemsWithScores.slice(0, 12)
  const avgSpecificity =
    last12.reduce((sum, item) => sum + (item.quality_score?.specificity ?? 0), 0) / last12.length

  // Simple trend calculation
  const firstHalf = last12.slice(0, 6)
  const secondHalf = last12.slice(6)
  const firstAvg = firstHalf.reduce((sum, item) => sum + (item.quality_score?.specificity ?? 0), 0) / 6
  const secondAvg = secondHalf.reduce((sum, item) => sum + (item.quality_score?.specificity ?? 0), 0) / 6
  const trend = secondAvg - firstAvg

  const trendPercent = Math.round((trend / 5) * 100)
  const trendColor = trend >= 0 ? 'text-context' : 'text-intent'
  const trendArrow = trend >= 0 ? '↑' : '↓'

  return (
    <div className="mb-6">
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-sm text-text-dim">
          Your prompts are
        </span>
        <span className={`font-bold ${trendColor}`}>
          {trendPercent}% more specific
        </span>
        <span className="text-sm text-text-dim">
          than 2 weeks ago {trendArrow}
        </span>
      </div>

      {/* Sparkline */}
      <div className="h-6 flex items-end gap-1">
        {last12.map((item, index) => (
          <div
            key={index}
            className={`flex-1 rounded-t transition-all ${
              trend >= 0 ? 'bg-context' : 'bg-intent'
            }`}
            style={{ height: `${((item.quality_score?.specificity ?? 0) / 5) * 100}%` }}
            title={`Specificity: ${item.quality_score?.specificity ?? 0}/5`}
          />
        ))}
      </div>

      <p className="mt-2 text-[10px] font-mono text-text-dim">
        Best week: {Math.max(...last12.map(i => i.quality_score?.specificity ?? 0)).toFixed(1)}/5 avg
      </p>
    </div>
  )
}

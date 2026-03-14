// features/history/components/HistoryList.tsx
// All sessions, grouped by date


import HistoryCard from './HistoryCard'
import type { HistoryItem } from '@/lib/api'

interface HistoryListProps {
  items: HistoryItem[]
  groupedByDate: Record<string, HistoryItem[]>
  isLoading: boolean
  searchQuery: string
  setSearchQuery: (query: string) => void
  onUseAgain: (prompt: string) => void
}

export default function HistoryList({
  items,
  groupedByDate,
  isLoading,
  searchQuery,
  setSearchQuery,
  onUseAgain,
}: HistoryListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="h-24 bg-layer2 rounded-xl" />
          </div>
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-text-dim">No prompts yet. Head back to the forge.</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">


      {/* Grouped by date */}
      {Object.entries(groupedByDate).map(([date, dateItems]) => (
        <div key={date} className="mb-8">
          <h3 className="font-mono text-[10px] tracking-wider uppercase text-text-dim mb-3">
            {date}
          </h3>
          <div className="space-y-3">
            {dateItems.map((item) => (
              <HistoryCard key={item.id} item={item} onUseAgain={onUseAgain} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

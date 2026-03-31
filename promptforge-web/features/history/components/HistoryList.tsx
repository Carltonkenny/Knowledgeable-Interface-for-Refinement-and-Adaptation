import HistoryCard from './HistoryCard'
import type { HistoryItem } from '@/lib/api'
import { Loader2, ChevronDown } from 'lucide-react'

interface HistoryListProps {
  items: HistoryItem[]
  isLoading: boolean
  isLoadingMore: boolean
  hasMore: boolean
  loadMore: () => void
  onUseAgain: (prompt: string) => void
  selectedIds: string[]
  toggleSelect: (id: string) => void
}

export default function HistoryList({
  items,
  isLoading,
  isLoadingMore,
  hasMore,
  loadMore,
  onUseAgain,
  selectedIds,
  toggleSelect,
}: HistoryListProps) {
  
  // ── Relative Date Grouping Helper ──────────────────────────────────────────
  const groupItems = (items: HistoryItem[]) => {
    const groups: Record<string, HistoryItem[]> = {}
    const today = new Date().toLocaleDateString()
    const yesterday = new Date(Date.now() - 86400000).toLocaleDateString()
    const last7Days = new Date(Date.now() - 604800000)

    items.forEach(item => {
      const itemDate = new Date(item.created_at)
      const itemDateStr = itemDate.toLocaleDateString()
      let groupKey = itemDateStr

      if (itemDateStr === today) groupKey = 'Today'
      else if (itemDateStr === yesterday) groupKey = 'Yesterday'
      else if (itemDate > last7Days) groupKey = 'Previous 7 Days'
      else {
        groupKey = itemDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
      }

      if (!groups[groupKey]) groups[groupKey] = []
      groups[groupKey].push(item)
    })
    return groups
  }

  if (isLoading && items.length === 0) {
    return (
      <div className="space-y-4 max-w-3xl mx-auto px-4 py-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse flex gap-4">
             <div className="w-5 h-5 bg-layer3 rounded-md mt-2" />
             <div className="flex-1 h-32 bg-layer2/50 rounded-2xl border border-border/10" />
          </div>
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-24 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="w-20 h-20 bg-kira/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-kira/10">
           <Loader2 className="w-8 h-8 text-kira/20" />
        </div>
        <h3 className="text-lg font-bold text-text mb-2 font-mono">No prompts found</h3>
        <p className="text-text-dim max-w-xs mx-auto text-sm">Start a new session in the Chat tab to see your history here.</p>
      </div>
    )
  }

  const grouped = groupItems(items)

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-12">
      {Object.entries(grouped).map(([label, dateItems]) => (
        <section key={label} className="animate-in fade-in duration-500">
          <div className="flex items-center gap-4 mb-6">
            <h3 className="font-mono text-[10px] tracking-[0.2em] uppercase text-text-dim whitespace-nowrap">
              {label}
            </h3>
            <div className="h-[1px] w-full bg-gradient-to-r from-border/50 to-transparent" />
          </div>
          
          <div className="space-y-4 px-4">
            {dateItems.map((item) => (
              <HistoryCard 
                key={item.id}
                item={item} 
                onUseAgain={onUseAgain}
                isSelected={selectedIds.includes(item.id)}
                onToggleSelect={toggleSelect}
              />
            ))}
          </div>
        </section>
      ))}

      {/* Pagination Footer */}
      {hasMore && (
        <div className="flex justify-center pt-8 pb-12 border-t border-border/10">
          <button
            onClick={loadMore}
            disabled={isLoadingMore}
            className="flex items-center gap-2 px-8 py-3 rounded-full bg-layer2/50 border border-border hover:border-kira/50 hover:bg-layer3 text-sm font-medium transition-all group active:scale-95 disabled:opacity-50"
          >
            {isLoadingMore ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-kira" />
                <span className="text-text-dim italic font-mono uppercase tracking-wider text-[10px]">Loading more...</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 group-hover:translate-y-0.5 transition-transform text-kira" />
                <span className="font-mono uppercase tracking-widest font-bold">Load More</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}

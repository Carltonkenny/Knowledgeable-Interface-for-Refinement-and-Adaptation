import { Search, Loader2, Trash2, X, CheckSquare } from 'lucide-react'
import { Input } from '@/components/ui'

interface HistorySearchBarProps {
  searchQuery: string
  setSearchQuery: (query: string) => void
  isSearching: boolean
  useRag: boolean
  setUseRag: (val: boolean) => void
  days: number
  setDays: (val: number) => void
  availableDomains: string[]
  domains: string[]
  setDomains: (val: string[]) => void
  minQuality: number
  setMinQuality: (val: number) => void
  dateFrom?: string
  setDateFrom: (val: string | undefined) => void
  dateTo?: string
  setDateTo: (val: string | undefined) => void
  
  // Bulk Actions Props
  selectedIds: string[]
  onClearSelection: () => void
  onBulkDelete: () => void
  onExport?: (format: 'json' | 'csv') => void
  onSelectAll: () => void
}

export default function HistorySearchBar({
  searchQuery,
  setSearchQuery,
  isSearching,
  useRag,
  setUseRag,
  days,
  setDays,
  availableDomains,
  domains,
  setDomains,
  minQuality,
  setMinQuality,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  selectedIds,
  onClearSelection,
  onBulkDelete,
  onExport,
  onSelectAll,
}: HistorySearchBarProps) {
  
  const toggleDomain = (domain: string) => {
    if (domains.includes(domain)) {
      setDomains(domains.filter(d => d !== domain))
    } else {
      setDomains([...domains, domain])
    }
  }

  const isBulkActive = selectedIds.length > 0

  return (
    <div className="space-y-4 mb-8 sticky top-0 z-20 bg-bg/80 backdrop-blur-md pt-4 pb-2">
      
      {/* ── Bulk Management Overlay ────────────────────────────────────────── */}
      {isBulkActive && (
        <div className="absolute inset-x-0 -top-2 bg-gradient-to-r from-kira to-purple-600 p-[1px] rounded-2xl animate-in slide-in-from-top-4 duration-300 shadow-2xl shadow-kira/30 z-30">
          <div className="bg-bg rounded-[15px] px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button 
                onClick={onClearSelection}
                className="p-2 hover:bg-layer2 rounded-full transition-colors text-text-dim hover:text-text"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-text font-mono">{selectedIds.length} Prompts Selected</span>
                <span className="text-[10px] text-kira uppercase tracking-widest font-mono font-bold animate-pulse">Bulk Actions Active</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
               <button 
                onClick={onSelectAll}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-layer2 hover:bg-layer3 border border-border text-xs font-semibold transition-all"
              >
                <CheckSquare className="w-4 h-4 text-kira" />
                Select Page
              </button>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onExport?.('json')}
                  className="px-4 py-2 rounded-xl text-[10px] font-bold text-text-bright hover:bg-white/10 border border-white/5 transition-all"
                >
                  Export JSON
                </button>
                <button
                  onClick={() => onExport?.('csv')}
                  className="px-4 py-2 rounded-xl text-[10px] font-bold text-text-bright hover:bg-white/10 border border-white/5 transition-all"
                >
                  Export CSV
                </button>
                <div className="w-[1px] h-4 bg-white/10 mx-1" />
                <button 
                  onClick={onBulkDelete}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/20 transition-all text-xs font-semibold group"
                >
                  <Trash2 className="w-4 h-4 group-hover:scale-110 transition-transform" />
                  Delete Forever
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Search Input ─────────────────────────────────────────────────── */}
      <div className="relative">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search className="w-5 h-5 text-kira opacity-50" />
        </div>
        <Input
          type="text"
          placeholder="Search your Memory Palace..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-12 py-6 text-lg bg-layer2/50 border border-border focus:border-kira/50 rounded-2xl transition-all shadow-inner-dark"
        />
        {isSearching && (
          <div className="absolute inset-y-0 right-4 flex items-center">
            <Loader2 className="w-5 h-5 text-kira animate-spin" />
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 px-2">
        {/* RAG Toggle */}
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-bold text-text-dim uppercase tracking-widest">Search Mode:</span>
          <div className="flex bg-layer2/50 p-1 rounded-xl border border-border">
            <button
              onClick={() => setUseRag(true)}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-tighter transition-all ${
                useRag 
                ? 'bg-kira text-bg shadow-sm' 
                : 'text-text-dim hover:text-text'
              }`}
            >
              Semantic (AI)
            </button>
            <button
              onClick={() => setUseRag(false)}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-tighter transition-all ${
                !useRag 
                ? 'bg-layer3 text-text shadow-sm' 
                : 'text-text-dim hover:text-text'
              }`}
            >
              Keyword (Exact)
            </button>
          </div>
        </div>

        {/* Analytics Range */}
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-bold text-text-dim uppercase tracking-widest">Time Range:</span>
          <select
            value={days}
            onChange={(e) => {
              const val = Number(e.target.value)
              setDays(val)
              const from = new Date()
              from.setDate(from.getDate() - val)
              setDateFrom(from.toISOString().split('T')[0])
              setDateTo(undefined) // Fix: No upper bound allows searching all the way up to "now" (fixing the 3-hour ago bug)
            }}
            className="bg-layer2/50 border border-border text-text text-xs rounded-xl px-3 py-2 focus:ring-1 focus:ring-kira outline-none cursor-pointer hover:bg-layer2"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={60}>Last 60 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
        </div>
      </div>

    {/* ── Vector Filters ─────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-8 px-2 pt-4 border-t border-border/10">
        {/* Domain Chips */}
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-bold text-text-dim uppercase tracking-widest">Domains:</span>
          <div className="flex flex-wrap gap-2">
            {availableDomains.length === 0 ? (
              <span className="text-[10px] text-text-dim italic">No domains yet</span>
            ) : (
              availableDomains.map(domain => (
                <button
                  key={domain}
                  onClick={() => toggleDomain(domain)}
                  className={`px-3 py-1 rounded-full text-[10px] font-bold border transition-all duration-300 ${
                    domains.includes(domain)
                      ? 'bg-kira/20 border-kira text-kira shadow-sm shadow-kira/10'
                      : 'bg-layer2/30 border-border/50 text-text-dim hover:border-text-dim hover:bg-layer2/50'
                  }`}
                >
                  {domain}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Quality Filter */}
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-bold text-text-dim uppercase tracking-widest">Min Quality:</span>
          <div className="flex gap-1 bg-layer2/50 p-1 rounded-xl border border-border/10">
            {[0, 3, 4, 5].map(q => (
              <button
                key={q}
                onClick={() => setMinQuality(q)}
                className={`w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold transition-all duration-300 ${
                  minQuality === q
                    ? 'bg-kira text-bg shadow-sm'
                    : 'text-text-dim hover:text-text hover:bg-layer3'
                }`}
              >
                {q === 0 ? 'All' : `${q}+`}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

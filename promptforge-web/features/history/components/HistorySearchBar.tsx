// features/history/components/HistorySearchBar.tsx
'use client'

import { Search, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui'

interface HistorySearchBarProps {
  searchQuery: string
  setSearchQuery: (query: string) => void
  isSearching: boolean
  useRag: boolean
  setUseRag: (val: boolean) => void
  days: number
  setDays: (val: number) => void
  domains: string[]
  setDomains: (val: string[]) => void
  minQuality: number
  setMinQuality: (val: number) => void
  dateFrom?: string
  setDateFrom: (val: string | undefined) => void
  dateTo?: string
  setDateTo: (val: string | undefined) => void
}

export default function HistorySearchBar({
  searchQuery,
  setSearchQuery,
  isSearching,
  useRag,
  setUseRag,
  days,
  setDays,
  domains,
  setDomains,
  minQuality,
  setMinQuality,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
}: HistorySearchBarProps) {
  const commonDomains = ['python', 'javascript', 'business', 'creative', 'technical']
  
  const toggleDomain = (domain: string) => {
    if (domains.includes(domain)) {
      setDomains(domains.filter(d => d !== domain))
    } else {
      setDomains([...domains, domain])
    }
  }
  return (
    <div className="space-y-4 mb-8">
      <div className="relative">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search className="w-5 h-5 text-kira border-kira opacity-50" />
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
          <span className="text-sm font-medium text-text-dim">Search Mode:</span>
          <div className="flex bg-layer2/50 p-1 rounded-xl border border-border">
            <button
              onClick={() => setUseRag(true)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                useRag 
                ? 'bg-kira text-bg shadow-sm' 
                : 'text-text-dim hover:text-text'
              }`}
            >
              Semantic (RAG)
            </button>
            <button
              onClick={() => setUseRag(false)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                !useRag 
                ? 'bg-layer3 text-text shadow-sm' 
                : 'text-text-dim hover:text-text'
              }`}
            >
              Keyword (DB)
            </button>
          </div>
        </div>

        {/* Analytics Range */}
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-text-dim">Range:</span>
          <select
            value={days}
            onChange={(e) => {
              const val = Number(e.target.value)
              setDays(val)
              const from = new Date()
              from.setDate(from.getDate() - val)
              setDateFrom(from.toISOString().split('T')[0])
              setDateTo(new Date().toISOString().split('T')[0])
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

      {/* Advanced Filters */}
      <div className="flex flex-wrap items-center gap-6 px-2 pt-2 border-t border-border/50">
        {/* Domain Chips */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-text-dim uppercase tracking-widest">Domains:</span>
          <div className="flex flex-wrap gap-1.5">
            {commonDomains.map(domain => (
              <button
                key={domain}
                onClick={() => toggleDomain(domain)}
                className={`px-2.5 py-1 rounded-full text-[10px] font-bold border transition-all ${
                  domains.includes(domain)
                    ? 'bg-kira/20 border-kira text-kira shadow-sm shadow-kira/10'
                    : 'bg-layer2/30 border-border text-text-dim hover:border-text-dim'
                }`}
              >
                {domain}
              </button>
            ))}
          </div>
        </div>

        {/* Quality Filter */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-text-dim uppercase tracking-widest">Min Quality:</span>
          <div className="flex gap-1 bg-layer2/50 p-1 rounded-lg border border-border">
            {[0, 3, 4, 5].map(q => (
              <button
                key={q}
                onClick={() => setMinQuality(q)}
                className={`w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold transition-all ${
                  minQuality === q
                    ? 'bg-kira text-bg'
                    : 'text-text-dim hover:text-text'
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

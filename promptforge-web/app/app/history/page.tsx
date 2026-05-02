'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ROUTES } from '@/lib/constants'
import { useToken } from '@/hooks/useToken'
import { apiHistoryBulkDelete, apiHistoryRenameSession } from '@/lib/api'
import { logger } from '@/lib/logger'
import HistoryList from '@/features/history/components/HistoryList'
import HistorySearchBar from '@/features/history/components/HistorySearchBar'
import HistoryAnalyticsDashboard from '@/features/history/components/HistoryAnalyticsDashboard'
import Boneyard from '@/components/ui/Boneyard'
import { useHistory } from '@/features/history/hooks/useHistory'
import { useHistoryAnalytics } from '@/features/history/hooks/useHistoryAnalytics'

interface RenameSessionEvent {
  sessionId: string
  title: string
}

// Standard fallback for notifications since sonner is not installed
const toast = {
  success: (msg: string) => alert(`✅ ${msg}`),
  error: (msg: string) => alert(`❌ ${msg}`)
}

export default function HistoryPage() {
  const router = useRouter()
  const token = useToken()
  const [days, setDays] = useState(30)

  const {
    items,
    isLoading: isLoadingHistory,
    isLoadingMore,
    hasMore,
    loadMore,
    isSearching,
    searchQuery,
    setSearchQuery,
    useRag,
    setUseRag,
    domains,
    setDomains,
    minQuality,
    setMinQuality,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    selectedIds,
    toggleSelect,
    selectAll,
    clearSelection
  } = useHistory({ token: token! })

  const {
    analytics,
    isLoading: isLoadingAnalytics
  } = useHistoryAnalytics(token, days)

  // Extract top domains dynamically from live analytics
  const availableDomains = Object.keys(analytics?.domain_distribution || {})
    .sort((a, b) => (analytics?.domain_distribution?.[b]?.count || 0) - (analytics?.domain_distribution?.[a]?.count || 0))
    .slice(0, 8) // Top 8 most active domains

  // ── DATA EXPORT SYSTEM ──────────────────────────────────────────────
  const handleExport = (format: 'json' | 'csv') => {
    const exportData = items.filter(item => 
      selectedIds.length === 0 || selectedIds.includes(item.id)
    )

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `PromptForge_Export_${new Date().toISOString().split('T')[0]}.json`
      a.click()
    } else {
      const headers = ['id', 'session_id', 'raw_prompt', 'improved_prompt', 'domain', 'score_spec', 'score_clar', 'score_act', 'created_at']
      const csvContent = [
        headers.join(','),
        ...exportData.map(item => [
          item.id,
          item.session_id,
          `"${item.raw_prompt.replace(/"/g, '""')}"`,
          `"${item.improved_prompt.replace(/"/g, '""')}"`,
          item.domain,
          item.quality_score?.specificity ?? 0,
          item.quality_score?.clarity ?? 0,
          item.quality_score?.actionability ?? 0,
          item.created_at
        ].join(','))
      ].join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `PromptForge_Export_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
    }
    toast.success(`Exported ${exportData.length} items to ${format.toUpperCase()}`)
  }

  useEffect(() => {
    const handleRename = async (e: Event) => {
      const detail = (e as CustomEvent<RenameSessionEvent>).detail
      const { sessionId, title } = detail
      try {
        await apiHistoryRenameSession(token!, sessionId, title)
        toast.success('Session renamed in Palace index')
        window.location.reload() // Simple sync
      } catch (err) {
        logger.error('Failed to rename session', { err, sessionId })
        toast.error('Failed to update session title')
      }
    }
    window.addEventListener('rename-session', handleRename as EventListener)
    return () => window.removeEventListener('rename-session', handleRename as EventListener)
  }, [token])

  // ── Handlers ───────────────────────────────────────────────────────────
  
  function handleUseAgain(prompt: string) {
    router.push(`/app?prompt=${encodeURIComponent(prompt)}`)
  }

  async function handleBulkDelete() {
    if (!token || selectedIds.length === 0) return
    if (!confirm(`Are you sure you want to permanently delete ${selectedIds.length} prompts? This cannot be undone.`)) return

    try {
      const deletedCount = await apiHistoryBulkDelete(token, selectedIds)
      toast.success(`${deletedCount} prompts deleted successfully.`)
      clearSelection()
      // Note: useHistory hook will naturally re-sync on next load or we could locally filter
      window.location.reload() // Quickest way to re-sync O(1) after massive batch delete
    } catch (err) {
      toast.error('Failed to delete prompts. Please try again.')
    }
  }

  function handleClearSelection() {
    clearSelection()
  }

  // Show loading state while token initializes
  if (!token) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Boneyard variant="kira" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg p-6 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end justify-between mb-8 border-b border-border/10 pb-6">
          <div className="flex flex-col">
            <h1 className="text-4xl font-black font-mono text-text tracking-tighter uppercase italic drop-shadow-md">
              Memory Palace
            </h1>
            <p className="text-[10px] text-text-dim font-mono uppercase tracking-[0.3em] mt-1">
              Automated Archival & Synthesis Engine
            </p>
          </div>
          <div className="flex flex-col items-end gap-3">
             <span className="text-[10px] font-bold text-kira bg-kira/10 px-3 py-1.5 rounded-xl border border-kira/20 uppercase tracking-widest shadow-[0_0_10px_rgba(46,196,182,0.15)] font-mono">
              {items.length} Prompts Logged
            </span>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => handleExport('json')}
                className="text-[9px] font-bold text-text-dim hover:text-text bg-layer2/50 hover:bg-layer3 px-3 py-1 rounded-lg border border-border/50 uppercase tracking-widest transition-all"
              >
                Export JSON
              </button>
              <button 
                onClick={() => handleExport('csv')}
                className="text-[9px] font-bold text-text-dim hover:text-text bg-layer2/50 hover:bg-layer3 px-3 py-1 rounded-lg border border-border/50 uppercase tracking-widest transition-all"
              >
                Export CSV
              </button>
            </div>
          </div>
        </div>
        
        <HistoryAnalyticsDashboard 
          analytics={analytics} 
          isLoading={isLoadingAnalytics} 
          onDomainSelect={(domain) => {
            setDomains(prev => 
              prev.includes(domain) 
                ? prev.filter(d => d !== domain) 
                : [...prev, domain]
            )
          }}
        />
        
        <HistorySearchBar 
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          isSearching={isSearching}
          useRag={useRag}
          setUseRag={setUseRag}
          days={days}
          setDays={setDays}
          availableDomains={availableDomains}
          domains={domains}
          setDomains={setDomains}
          minQuality={minQuality}
          setMinQuality={setMinQuality}
          dateFrom={dateFrom}
          setDateFrom={setDateFrom}
          dateTo={dateTo}
          setDateTo={setDateTo}
          selectedIds={selectedIds}
          onClearSelection={handleClearSelection}
          onBulkDelete={handleBulkDelete}
          onExport={handleExport}
          onSelectAll={selectAll}
        />
        
        <HistoryList
          items={items}
          isLoading={isLoadingHistory}
          isLoadingMore={isLoadingMore}
          hasMore={hasMore}
          loadMore={loadMore}
          onUseAgain={handleUseAgain}
          selectedIds={selectedIds}
          toggleSelect={toggleSelect}
        />
      </div>
    </div>
  )
}

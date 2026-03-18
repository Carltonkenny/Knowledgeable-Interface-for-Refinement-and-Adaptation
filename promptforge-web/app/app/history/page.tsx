// app/app/history/page.tsx
// History page

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ROUTES } from '@/lib/constants'
import { useToken } from '@/hooks/useToken'
import HistoryList from '@/features/history/components/HistoryList'
import HistorySearchBar from '@/features/history/components/HistorySearchBar'
import HistoryAnalyticsDashboard from '@/features/history/components/HistoryAnalyticsDashboard'
import { useHistory } from '@/features/history/hooks/useHistory'
import { useHistoryAnalytics } from '@/features/history/hooks/useHistoryAnalytics'

export default function HistoryPage() {
  const router = useRouter()
  const token = useToken()
  const [days, setDays] = useState(30)

  const {
    items,
    isLoading: isLoadingHistory,
    isSearching,
    groupedByDate,
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
  } = useHistory({ token: token! })

  const {
    analytics,
    isLoading: isLoadingAnalytics
  } = useHistoryAnalytics(token, days)

  // Show loading state while token initializes
  if (!token) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center animate-pulse">
          <span className="text-kira font-bold font-mono text-xl">K</span>
        </div>
      </div>
    )
  }

  function handleUseAgain(prompt: string) {
    router.push(`/app?prompt=${encodeURIComponent(prompt)}`)
  }

  if (!token) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center animate-pulse">
          <span className="text-kira font-bold font-mono text-xl">K</span>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg p-6 md:p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold font-mono text-text mb-8 tracking-tight">
          Memory Palace
        </h1>
        
        <HistoryAnalyticsDashboard 
          analytics={analytics} 
          isLoading={isLoadingAnalytics} 
        />
        
        <HistorySearchBar 
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          isSearching={isSearching}
          useRag={useRag}
          setUseRag={setUseRag}
          days={days}
          setDays={setDays}
          domains={domains}
          setDomains={setDomains}
          minQuality={minQuality}
          setMinQuality={setMinQuality}
          dateFrom={dateFrom}
          setDateFrom={setDateFrom}
          dateTo={dateTo}
          setDateTo={setDateTo}
        />
        
        <HistoryList
          items={items}
          groupedByDate={groupedByDate}
          isLoading={isLoadingHistory}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onUseAgain={handleUseAgain}
        />
      </div>
    </div>
  )
}

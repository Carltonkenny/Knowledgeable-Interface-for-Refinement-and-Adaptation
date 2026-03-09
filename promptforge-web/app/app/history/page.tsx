// app/app/history/page.tsx
// History page

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getAccessToken } from '@/lib/supabase'
import { ROUTES } from '@/lib/constants'
import HistoryList from '@/features/history/components/HistoryList'
import { useHistory } from '@/features/history/hooks/useHistory'

export default function HistoryPage() {
  const [token, setToken] = useState<string | null>(null)
  const router = useRouter()
  
  const {
    items,
    isLoading,
    groupedByDate,
    searchQuery,
    setSearchQuery,
  } = useHistory({ token: token! })

  useEffect(() => {
    async function loadToken() {
      const accessToken = await getAccessToken()
      
      if (!accessToken) {
        router.push(ROUTES.LOGIN)
        return
      }
      
      setToken(accessToken)
    }

    loadToken()
  }, [router])

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
    <div className="min-h-screen bg-bg">
      <HistoryList
        items={items}
        groupedByDate={groupedByDate}
        isLoading={isLoading}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onUseAgain={handleUseAgain}
      />
    </div>
  )
}

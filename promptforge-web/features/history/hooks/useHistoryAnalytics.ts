// features/history/hooks/useHistoryAnalytics.ts
'use client'

import { useState, useEffect } from 'react'
import { apiHistoryAnalytics } from '@/lib/api'
import type { HistoryAnalytics } from '@/lib/api'

export function useHistoryAnalytics(token: string | null, days: number = 30) {
  const [analytics, setAnalytics] = useState<HistoryAnalytics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return

    async function loadAnalytics() {
      try {
        setIsLoading(true)
        const data = await apiHistoryAnalytics(token!, days)
        setAnalytics(data)
      } catch (err) {
        setError('Failed to load analytics')
      } finally {
        setIsLoading(false)
      }
    }

    loadAnalytics()
  }, [token, days])

  return {
    analytics,
    isLoading,
    error,
  }
}

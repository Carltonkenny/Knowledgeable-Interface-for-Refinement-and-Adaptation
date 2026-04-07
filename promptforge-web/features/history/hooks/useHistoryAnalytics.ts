// features/history/hooks/useHistoryAnalytics.ts
'use client'
import { logger } from '@/lib/logger'

import { useState, useEffect } from 'react'
import { apiHistoryAnalytics } from '@/lib/api'
import type { HistoryAnalytics } from '@/lib/api'

export function useHistoryAnalytics(token: string | null, days: number = 30) {
  const [analytics, setAnalytics] = useState<HistoryAnalytics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadAnalytics() {
    if (!token) return
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

  useEffect(() => {
    loadAnalytics()
  }, [token, days])

  useEffect(() => {
    const handleUpdate = () => {
      logger.debug('[history-analytics] Real-time sync triggered by domain update')
      loadAnalytics()
    }
    window.addEventListener('update-domain', handleUpdate)
    return () => window.removeEventListener('update-domain', handleUpdate)
  }, [token, days])

  return {
    analytics,
    isLoading,
    error,
    refresh: loadAnalytics
  }
}

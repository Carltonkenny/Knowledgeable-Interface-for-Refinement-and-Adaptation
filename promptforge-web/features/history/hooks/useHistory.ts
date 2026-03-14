// features/history/hooks/useHistory.ts
// Fetch + group history by date

'use client'

import { useState, useEffect } from 'react'
import { apiHistory, apiHistorySearch } from '@/lib/api'
import type { HistoryItem } from '@/lib/api'

interface UseHistoryProps {
  token: string
}

export function useHistory({ token }: UseHistoryProps) {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [useRag, setUseRag] = useState(true)
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [domains, setDomains] = useState<string[]>([])
  const [minQuality, setMinQuality] = useState(0)
  const [dateFrom, setDateFrom] = useState<string | undefined>()
  const [dateTo, setDateTo] = useState<string | undefined>()

  // Debounce the search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Load history or search results
  useEffect(() => {
    if (!token) return

    async function loadData() {
      try {
        if (debouncedQuery.trim() || domains.length > 0 || minQuality > 0 || dateFrom || dateTo) {
          setIsSearching(true)
          const results = await apiHistorySearch(token, {
            query: debouncedQuery,
            use_rag: useRag,
            domains: domains.length > 0 ? domains : undefined,
            min_quality: minQuality,
            date_from: dateFrom,
            date_to: dateTo,
            limit: 20
          })
          setItems(Array.isArray(results) ? results : [])
        } else {
          // If no filters, load normal history
          if (items.length === 0) setIsLoading(true)
          const history = await apiHistory(token)
          setItems(Array.isArray(history) ? history : [])
        }
      } catch (err) {
        setError('Failed to load history')
        setItems([])
      } finally {
        setIsLoading(false)
        setIsSearching(false)
      }
    }

    loadData()
  }, [token, debouncedQuery, useRag, domains, minQuality, dateFrom, dateTo])

  // Group by date - safe reduce with empty array fallback
  const groupedByDate = (items || []).reduce((acc, item) => {
    const date = new Date(item.created_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })

    if (!acc[date]) {
      acc[date] = []
    }
    acc[date].push(item)
    return acc
  }, {} as Record<string, HistoryItem[]>)

  return {
    items,
    isLoading,
    isSearching,
    error,
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
  }
}

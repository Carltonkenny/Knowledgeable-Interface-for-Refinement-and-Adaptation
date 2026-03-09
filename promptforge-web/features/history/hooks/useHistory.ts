// features/history/hooks/useHistory.ts
// Fetch + group history by date

'use client'

import { useState, useEffect } from 'react'
import { apiHistory } from '@/lib/api'
import type { HistoryItem } from '@/lib/api'

interface UseHistoryProps {
  token: string
}

export function useHistory({ token }: UseHistoryProps) {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    async function loadHistory() {
      try {
        const history = await apiHistory(token)
        setItems(history)
      } catch (err) {
        setError('Failed to load history')
      } finally {
        setIsLoading(false)
      }
    }

    loadHistory()
  }, [token])

  // Group by date
  const groupedByDate = items.reduce((acc, item) => {
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

  // Client-side search
  const filteredItems = items.filter((item) => {
    const query = searchQuery.toLowerCase()
    return (
      item.original_prompt.toLowerCase().includes(query) ||
      item.improved_prompt.toLowerCase().includes(query)
    )
  })

  return {
    items,
    isLoading,
    error,
    groupedByDate,
    searchQuery,
    setSearchQuery,
    filteredItems,
  }
}

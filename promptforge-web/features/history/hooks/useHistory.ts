// features/history/hooks/useHistory.ts
// Fetch + group history by date

'use client'
import { logger } from '@/lib/logger'

import { useState, useEffect } from 'react'
import { apiHistory, apiHistorySearch, apiToggleFavorite, apiUpdatePromptDomain } from '@/lib/api'
import type { HistoryItem } from '@/lib/api'

interface UseHistoryProps {
  token: string
}

export function useHistory({ token }: UseHistoryProps) {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSearching, setIsSearching] = useState(false)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [useRag, setUseRag] = useState(true)
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [domains, setDomains] = useState<string[]>([])
  const [minQuality, setMinQuality] = useState(0)
  const [dateFrom, setDateFrom] = useState<string | undefined>()
  const [dateTo, setDateTo] = useState<string | undefined>()
  
  // Pagination State
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const LIMIT = 20

  // Bulk Management State
  const [selectedIds, setSelectedIds] = useState<string[]>([])

  // Debounce the search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery)
      setOffset(0) // Reset pagination on new search
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0)
  }, [domains, minQuality, dateFrom, dateTo, useRag])

  // Load history or search results
  useEffect(() => {
    if (!token) return

    const controller = new AbortController()

    async function loadData() {
      const isInitial = offset === 0
      try {
        if (isInitial) {
          if (!debouncedQuery.trim() && domains.length === 0) setIsLoading(true)
          else setIsSearching(true)
        } else {
          setIsLoadingMore(true)
        }

        const isFiltered = debouncedQuery.trim() || domains.length > 0 || minQuality > 0 || dateFrom || dateTo
        
        let fetchedItems: HistoryItem[] = []
        
        if (isFiltered) {
          const searchRes = await apiHistorySearch(token, {
            query: debouncedQuery,
            use_rag: useRag,
            domains: domains.length > 0 ? domains : undefined,
            min_quality: minQuality,
            date_from: dateFrom,
            date_to: dateTo,
            limit: LIMIT,
            offset: offset
          })
          fetchedItems = (searchRes as any).results || []
        } else {
          const history = await apiHistory(token, undefined, LIMIT, offset)
          fetchedItems = Array.isArray(history) ? history : []
        }

        if (controller.signal.aborted) return

        setItems(prev => {
          const combined = isInitial ? fetchedItems : [...prev, ...fetchedItems]
          // DEDUPLICATION: Ensure unique keys for React rendering
          const uniqueMap = new Map()
          combined.forEach(item => uniqueMap.set(item.id, item))
          return Array.from(uniqueMap.values())
        })
        
        setHasMore(fetchedItems.length === LIMIT)
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') return
        setError('Failed to load history')
        if (offset === 0) setItems([])
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
          setIsSearching(false)
          setIsLoadingMore(false)
        }
      }
    }

    loadData()
    return () => controller.abort()
  }, [token, debouncedQuery, useRag, domains, minQuality, dateFrom, dateTo, offset])

  const loadMore = () => {
    if (!isLoadingMore && hasMore) {
      setOffset(prev => prev + LIMIT)
    }
  }

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const selectAll = () => {
    if (selectedIds.length === items.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(items.map(i => i.id))
    }
  }

  // Handle Favorite Toggling Globally
  useEffect(() => {
    const handleToggleFavorite = async (e: any) => {
      const { id, is_favorite } = e.detail
      setItems(prev => prev.map(item => item.id === id ? { ...item, is_favorite } : item))
      try {
        await apiToggleFavorite(token, id, is_favorite)
      } catch (err) {
        logger.error('Failed to toggle favorite', { error: err })
        setItems(prev => prev.map(item => item.id === id ? { ...item, is_favorite: !is_favorite } : item))
      }
    }

    const handleUpdateDomain = async (e: any) => {
      const { id, domain } = e.detail
      const originalItem = items.find(i => i.id === id)
      
      setItems(prev => prev.map(item => item.id === id ? { ...item, domain } : item))
      
      try {
        await apiUpdatePromptDomain(token, id, domain)
      } catch (err) {
        logger.error('Failed to update domain', { error: err })
        if (originalItem) {
          setItems(prev => prev.map(item => item.id === id ? { ...item, domain: originalItem.domain } : item))
        }
      }
    }
    
    window.addEventListener('toggle-favorite', handleToggleFavorite)
    window.addEventListener('update-domain', handleUpdateDomain)
    return () => {
      window.removeEventListener('toggle-favorite', handleToggleFavorite)
      window.removeEventListener('update-domain', handleUpdateDomain)
    }
  }, [token, items])

  // Group by date - updated for "Today", "Yesterday" etc later in UI
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
    isLoadingMore,
    hasMore,
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
    loadMore,
    selectedIds,
    toggleSelect,
    selectAll,
    clearSelection: () => setSelectedIds([]),
    setSelectedIds
  }
}

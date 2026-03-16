// features/chat/hooks/useChatSessions.ts
// 'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { 
  apiListSessions, 
  apiCreateSession, 
  apiDeleteSession, 
  apiRestoreSession,
  apiPurgeSession,
  apiListDeletedSessions,
  apiPatchSession,
  type ChatSession 
} from '@/lib/api'
import { logger } from '@/lib/logger'

export function useChatSessions(token: string) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [deletedSessions, setDeletedSessions] = useState<ChatSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRecycleBinLoading, setIsRecycleBinLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const router = useRouter()
  const params = useParams()
  const currentSessionId = params?.sessionId as string | undefined

  // Fetch all active sessions
  const fetchSessions = useCallback(async () => {
    if (!token) {
      logger.warn('Cannot fetch sessions - no auth token', { hasToken: false })
      return
    }
    setIsLoading(true)
    try {
      const data = await apiListSessions(token)
      setSessions(data)
      setError(null)
      logger.debug('Sessions fetched successfully', { count: data.length })
    } catch (err: any) {
      // RULES.md: Error logging must include full context for debugging
      logger.error('Failed to fetch chat sessions', {
        error_type: err instanceof Error ? err.name : (typeof err === 'string' ? 'string' : 'unknown'),
        error_message: err instanceof Error ? err.message : (typeof err === 'string' ? err : String(err)),
        error_status: err?.status || err?.statusCode || 'no status code',
        has_token: !!token,
        token_preview: token ? `${token.substring(0, 20)}...` : 'none',
        session_count: sessions.length,
      })
      setError('Could not load chat history')
    } finally {
      setIsLoading(false)
    }
  }, [token])

  // Fetch deleted sessions (Recycle Bin)
  const fetchDeletedSessions = useCallback(async () => {
    if (!token) {
      logger.warn('Cannot fetch deleted sessions - no auth token', { hasToken: false })
      return
    }
    setIsRecycleBinLoading(true)
    try {
      const data = await apiListDeletedSessions(token)
      setDeletedSessions(data)
      logger.debug('Deleted sessions fetched successfully', { count: data.length })
    } catch (err: any) {
      // RULES.md: Error logging must include full context for debugging
      logger.error('Failed to fetch deleted sessions', {
        error_type: err instanceof Error ? err.name : (typeof err === 'string' ? 'string' : 'unknown'),
        error_message: err instanceof Error ? err.message : (typeof err === 'string' ? err : String(err)),
        error_status: err?.status || err?.statusCode || 'no status code',
        has_token: !!token,
        token_preview: token ? `${token.substring(0, 20)}...` : 'none',
      })
    } finally {
      setIsRecycleBinLoading(false)
    }
  }, [token])

  useEffect(() => {
    fetchSessions()
    fetchDeletedSessions() // Pre-fetch for seamless Recycle Bin
  }, [token])

  // Create new session
  const createNewChat = async () => {
    try {
      const newSession = await apiCreateSession(token)
      setSessions(prev => [newSession, ...prev])
      router.push(`/app/chat/${newSession.id}`)
      return newSession.id
    } catch (err) {
      logger.error('Failed to create new chat', { err })
      setError('Failed to start new chat')
    }
  }

  // Soft Delete session
  const deleteSession = async (sessionId: string) => {
    // 1. Optimistic Update
    const sessionToRemove = sessions.find(s => s.id === sessionId)
    const originalSessions = [...sessions]
    const originalDeleted = [...deletedSessions]
    
    setSessions(prev => prev.filter(s => s.id !== sessionId))
    if (sessionToRemove) {
      setDeletedSessions(prev => [
        { ...sessionToRemove, deleted_at: new Date().toISOString() },
        ...prev
      ])
    }

    try {
      if (currentSessionId === sessionId) {
        router.push('/app')
      }
      
      await apiDeleteSession(token, sessionId)
      logger.info('Session soft-deleted successfully', { sessionId })
    } catch (err) {
      logger.error('Failed to delete session', { err })
      setError('Could not delete session')
      // Rollback on failure
      setSessions(originalSessions)
      setDeletedSessions(originalDeleted)
    }
  }

  // Restore session
  const restoreSession = async (sessionId: string) => {
    // 1. Optimistic Update
    const sessionToRestore = deletedSessions.find(s => s.id === sessionId)
    const originalSessions = [...sessions]
    const originalDeleted = [...deletedSessions]

    if (sessionToRestore) {
      setDeletedSessions(prev => prev.filter(s => s.id !== sessionId))
      // Add back to active sessions (sorting by last_activity)
      setSessions(prev => [
        { ...sessionToRestore, deleted_at: null }, 
        ...prev
      ].sort((a, b) => {
        if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1
        return new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime()
      }))
    }

    try {
      await apiRestoreSession(token, sessionId)
      logger.info('Session restored successfully', { sessionId })
    } catch (err) {
      logger.error('Failed to restore session', { err })
      setError('Could not restore session')
      // Rollback on failure
      setSessions(originalSessions)
      setDeletedSessions(originalDeleted)
    }
  }

  // Permanent Delete
  const permanentlyDeleteSession = async (sessionId: string) => {
    // Optimistic Update
    const originalDeleted = [...deletedSessions]
    setDeletedSessions(prev => prev.filter(s => s.id !== sessionId))

    try {
      await apiPurgeSession(token, sessionId)
      logger.info('Session purged successfully', { sessionId })
    } catch (err) {
      logger.error('Failed to purge session', { err })
      setError('Could not permanently delete session')
      setDeletedSessions(originalDeleted)
    }
  }

  // Update session metadata
  const patchSession = async (sessionId: string, updates: Partial<Pick<ChatSession, 'title' | 'is_pinned' | 'is_favorite'>>) => {
    // 1. Optimistic Update
    const originalSessions = [...sessions]
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        return { ...s, ...updates }
      }
      return s
    }))

    try {
      const updated = await apiPatchSession(token, sessionId, updates)
      // Confirm with real data (unlikely to change but safe)
      setSessions(prev => prev.map(s => s.id === sessionId ? updated : s))
      return updated
    } catch (err) {
      logger.error('Failed to update session', { err })
      setError('Could not update session')
      setSessions(originalSessions)
    }
  }

  const togglePin = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      patchSession(sessionId, { is_pinned: !session.is_pinned })
    }
  }

  const toggleFavorite = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      patchSession(sessionId, { is_favorite: !session.is_favorite })
    }
  }

  // Switch session
  const switchSession = (sessionId: string) => {
    router.push(`/app/chat/${sessionId}`)
  }

  return {
    sessions,
    deletedSessions,
    isLoading,
    isRecycleBinLoading,
    error,
    currentSessionId,
    createNewChat,
    deleteSession,
    restoreSession,
    permanentlyDeleteSession,
    patchSession,
    togglePin,
    toggleFavorite,
    switchSession,
    refreshSessions: fetchSessions,
    refreshDeletedSessions: fetchDeletedSessions
  }
}

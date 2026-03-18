// features/chat/hooks/useKiraStream.ts
// THE critical hook — SSE streaming + state machine
// 'use client' — manages chat state

'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { parseStream } from '@/lib/stream'
import { mapError } from '@/lib/errors'
import { logger } from '@/lib/logger'
import { apiConversation, type ChatResult, ApiError } from '@/lib/api'
import type { ChatMessage } from '../types'
import type { ProcessingStatus } from '../types'

interface UseKiraStreamProps {
  sessionId: string
  token: string
  apiUrl: string
}

interface UseKiraStreamReturn {
  messages: ChatMessage[]
  status: ProcessingStatus
  isStreaming: boolean
  isRateLimited: boolean
  rateLimitSecondsLeft: number
  error: string | null
  clarificationPending: boolean
  clarificationOptions: string[]
  historyLoadError: string | null  // Separate error for history loading
  historyLoading: boolean  // Whether history is currently loading
  send: (message: string, attachment?: File) => void
  retry: () => void
  clearError: () => void
  reloadHistory: () => void  // Explicit history reload function
}

/**
 * Kira stream hook — manages SSE connection and chat state
 */
export function useKiraStream({
  sessionId,
  token,
  apiUrl,
}: UseKiraStreamProps): UseKiraStreamReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<ProcessingStatus>({
    state: 'idle',
    statusText: undefined,
    agentsComplete: new Set(),
    agentsSkipped: new Set(),
  })
  const [isStreaming, setIsStreaming] = useState(false)
  const [isRateLimited, setIsRateLimited] = useState(false)
  const [rateLimitSecondsLeft, setRateLimitSecondsLeft] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [clarificationPending, setClarificationPending] = useState(false)
  const [clarificationOptions, setClarificationOptions] = useState<string[]>([])
  const [historyLoadError, setHistoryLoadError] = useState<string | null>(null)

  // Store last message for retry
  const lastMessageRef = useRef<{ message: string; attachment?: File } | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  // Accumulator for char-by-char SSE kira_message events
  const kiraStreamBufferRef = useRef<string>('')
  
  // ── FIX 1: Conversation Cache ───────────────────────────────────────────────
  // Persists across sessionId changes for this mount
  const conversationCache = useRef<Map<string, ChatMessage[]>>(new Map())
  const [historyLoading, setHistoryLoading] = useState(false)

  // Rate limit countdown
  useEffect(() => {
    if (!isRateLimited) return

    const interval = setInterval(() => {
      setRateLimitSecondsLeft((prev) => {
        if (prev <= 1) {
          setIsRateLimited(false)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [isRateLimited])

  /**
   * ═══ HISTORY RESTORATION (Phase 1.5) ═══
   * Fetches existing messages when sessionId changes.
   */
  useEffect(() => {
    if (!sessionId || !token) return

    // ── FIX 3: Abort previous history fetch ────────────────────────
    abortControllerRef.current?.abort()
    abortControllerRef.current = new AbortController()
    const signal = abortControllerRef.current.signal

    // ── FIX 2: Check cache first (Flash prevention) ───────────────
    const cached = conversationCache.current.get(sessionId)
    if (cached) {
      setMessages(cached)
      setHistoryLoading(false)
      return
    }

    // Do NOT clear messages here — show skeleton overlay in UI instead
    setHistoryLoading(true)

    let retryTimeout: NodeJS.Timeout | null = null
    let retryCount = 0
    const MAX_RETRIES = 3
    const BASE_DELAY = 5000 // 5 seconds base delay for 429

    const loadHistory = async () => {
      setHistoryLoadError(null) // Clear previous error on retry
      try {
        const history = await apiConversation(token, sessionId, signal)
        const mappedMessages: ChatMessage[] = history.map((turn, idx) => {
          if (turn.role === 'user') {
            return {
              id: `hist-u-${idx}`,
              type: 'user',
              content: turn.message,
            }
          }

          if (turn.message_type === 'output') {
            return {
              id: `hist-o-${idx}`,
              type: 'output',
              content: turn.message,
              result: {
                improved_prompt: turn.improved_prompt || '',
                diff: [], // We don't store diffs in DB yet, but we show the result
                quality_score: null,
                kira_message: turn.message,
                memories_applied: turn.memories_applied ?? 0,
                latency_ms: turn.latency_ms ?? 0,
                agents_run: [],
              },
              sessionId
            }
          }

          return {
            id: `hist-k-${idx}`,
            type: 'kira',
            content: turn.message,
          }
        })

        // ── FIX 1: Update cache (Max 10) ───────────────────────────
        conversationCache.current.set(sessionId, mappedMessages)
        if (conversationCache.current.size > 10) {
          const firstKey = conversationCache.current.keys().next().value
          if (firstKey) conversationCache.current.delete(firstKey)
        }

        setMessages(mappedMessages)
        setHistoryLoading(false)
        retryCount = 0 // Reset retry count on success
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          return // Intentional abort (session switch)
        }

        // Handle 429 Rate Limit with exponential backoff
        if (err instanceof ApiError && err.status === 429) {
          retryCount++
          if (retryCount <= MAX_RETRIES) {
            const delay = BASE_DELAY * Math.pow(2, retryCount - 1) // Exponential backoff: 5s, 10s, 20s
            logger.warn(`Rate limited while loading history, retry ${retryCount}/${MAX_RETRIES} in ${delay}ms`, {
              sessionId,
              retryCount,
              delay,
            })
            setIsRateLimited(true)
            setRateLimitSecondsLeft(Math.floor(delay / 1000))
            setError('Rate limit hit. Waiting before retry...')

            retryTimeout = setTimeout(() => {
              loadHistory()
            }, delay)
            return
          } else {
            logger.error('Max retries exceeded for rate limited history load', { sessionId, retryCount })
            setError('Rate limit exceeded. Please try again later.')
            setHistoryLoadError('Rate limit exceeded. Please try again later.')
            setIsRateLimited(true)
            setHistoryLoading(false)
          }
        } else {
          const errorMsg = err instanceof ApiError 
            ? `Failed to load: ${err.message}` 
            : 'Failed to load conversation history'
          logger.error(errorMsg, { err, sessionId })
          setHistoryLoadError('Failed to load conversation — tap to retry')
          setHistoryLoading(false)
        }
      }
    }

    loadHistory()

    // Cleanup timeout on unmount or sessionId change
    return () => {
      if (retryTimeout) clearTimeout(retryTimeout)
    }
  }, [sessionId, token])

  /**
   * Send message to backend via SSE
   */
  const send = useCallback(
    async (message: string, attachment?: File) => {
      if (isStreaming || isRateLimited) return

      // Store for retry
      lastMessageRef.current = { message, attachment }

      // Reset state
      setError(null)
      setClarificationPending(false)
      kiraStreamBufferRef.current = ''

      // Add user message
      const userMessage: ChatMessage = {
        id: crypto.randomUUID?.() ?? Date.now().toString(),
        type: 'user',
        content: message,
      }
      setMessages((prev) => [...prev, userMessage])

      // Set streaming state
      setIsStreaming(true)
      setStatus((prev) => ({ ...prev, state: 'kira_reading' }))

      // Create abort controller for this request
      abortControllerRef.current = new AbortController()

      try {
        // Prepare request body
        const body: Record<string, unknown> = {
          message,
          session_id: sessionId,
        }

        if (attachment) {
          // Convert file to base64
          const base64 = await new Promise<string>((resolve) => {
            const reader = new FileReader()
            reader.onloadend = () => resolve(reader.result as string)
            reader.readAsDataURL(attachment)
          })

          body.input_modality = attachment.type.startsWith('image/') ? 'image' : 'file'
          body.file_base64 = base64
          body.file_type = attachment.type
        }

        // Stream callbacks
        const callbacks = {
          onStatus: (statusText: string) => {
            setStatus((prev) => ({
              ...prev,
              state: 'swarm_running',
              statusText,
            }))
          },
          onKiraMessage: (kiraMessage: string, complete: boolean) => {
            // Backend may stream char-by-char or send full message.
            // If complete=true with empty string, it's a completion signal — use buffer as-is.
            // Otherwise accumulate into buffer for smooth word-by-word display.
            if (complete && kiraMessage === '') {
              // Completion signal — just mark streaming done, keep buffered text
            } else if (kiraMessage.length <= 2) {
              // Char-by-char streaming — accumulate
              kiraStreamBufferRef.current += kiraMessage
            } else {
              // Full message received at once — use directly
              kiraStreamBufferRef.current = kiraMessage
            }

            const displayText = kiraStreamBufferRef.current

            setMessages((prev) => {
              const existingIdx = prev.findIndex((m) => m.type === 'kira' && m.isStreaming !== false)
              if (existingIdx >= 0) {
                return prev.map((m, i) =>
                  i === existingIdx
                    ? { ...m, content: displayText, isStreaming: !complete }
                    : m
                )
              }
              return [
                ...prev,
                {
                  id: crypto.randomUUID?.() ?? Date.now().toString(),
                  type: 'kira',
                  content: displayText,
                  isStreaming: !complete,
                },
              ]
            })
          },
          onResult: (result: ChatResult) => {
            // Log result received per RULES.md structured logging standards
            logger.info('[kira] result received', {
              type: result.type,                    // RULES.md: Structured logging
              has_prompt: !!result.improved_prompt,
              diff_length: Array.isArray(result.diff) ? result.diff.length : 0,
              has_quality: !!result.quality_score,
              memories_applied: result.memories_applied ?? 0,
              latency_ms: result.latency_ms ?? 0,
            })

            // ═══ HANDLE CONVERSATION TYPE (RULES.md: Personality-driven replies) ═══
            if (result.type === 'conversation' && result.reply) {
              setMessages((prev) => [
                ...prev,
                {
                  id: crypto.randomUUID?.() ?? Date.now().toString(),
                  type: 'kira',
                  content: result.reply,
                },
              ])
              
              setStatus((prev) => ({
                ...prev,
                state: 'complete',
                agentsComplete: new Set(),
                isStreaming: false,
              }))
              return  // Early return - don't show output card
            }

            // ═══ HANDLE FOLLOWUP TYPE (RULES.md: Single-LLM refinement) ═══
            if (result.type === 'followup_refined' && result.reply) {
              setMessages((prev) => [
                ...prev,
                {
                  id: crypto.randomUUID?.() ?? Date.now().toString(),
                  type: 'kira',
                  content: result.reply,
                },
              ])
              // Continue to show output card for followup (has improved_prompt)
            }

            // Normalize result shape from backend (handle missing/null fields)
            const safeResult: ChatResult = {
              improved_prompt: result.improved_prompt ?? '',
              diff: Array.isArray(result.diff) ? result.diff : [],
              quality_score: result.quality_score ?? null,
              suggestions: Array.isArray((result as any).suggestions) ? (result as any).suggestions : [],
              kira_message: result.kira_message ?? '',
              memories_applied: result.memories_applied ?? 0,
              latency_ms: result.latency_ms ?? 0,
              agents_run: Array.isArray(result.agents_run) ? result.agents_run : [],
            }
            // Add output card with safe result
            setMessages((prev) => [
              ...prev,
              {
                id: crypto.randomUUID?.() ?? Date.now().toString(),
                type: 'output',
                result: safeResult,
                sessionId,
              },
            ])

            // Add memory/latency chips
            setStatus((prev) => ({
              ...prev,
              state: 'complete',
              agentsComplete: new Set(['intent', 'context', 'domain', 'engineer']),
              isStreaming: false,
            }))
          },
          onDone: () => {
            setIsStreaming(false)
            setStatus((prev) => ({
              ...prev,
              state: 'complete',
              isStreaming: false,
            }))
          },
          onError: (errorMessage: string) => {
            const mappedError = mapError(errorMessage)
            setError(mappedError.userMessage)
            setIsStreaming(false)
          },
        }

        // Start SSE stream
        await parseStream(
          `${apiUrl}/chat/stream`,
          body,
          token,
          callbacks,
          abortControllerRef.current.signal
        )
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          // User navigated away — ignore
          return
        }

        logger.error('Stream failed', { err })
        setError('Something went wrong. Your prompt is safe — try again.')
        setIsStreaming(false)
      } finally {
        // ALWAYS reset streaming state (fixes Enter button stopping after one message)
        setIsStreaming(false)
        setStatus((prev) => ({
          ...prev,
          state: prev.state === 'complete' ? 'complete' : 'idle',
          isStreaming: false,
        }))
      }
    },
    [sessionId, token, apiUrl, isRateLimited]  // Removed isStreaming from deps (causes re-creation)
  )

  /**
   * Retry last failed message
   */
  const retry = useCallback(() => {
    if (lastMessageRef.current) {
      const { message, attachment } = lastMessageRef.current
      send(message, attachment)
    }
  }, [send])

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  /**
   * Reload conversation history (for retry button)
   */
  const reloadHistory = useCallback(() => {
    if (!sessionId || !token) return
    setHistoryLoadError(null)
    
    // Re-trigger the history loading effect
    // We do this by calling the same loadHistory logic
    const loadHistory = async () => {
      try {
        const history = await apiConversation(token, sessionId)
        const mappedMessages: ChatMessage[] = history.map((turn, idx) => {
          if (turn.role === 'user') {
            return {
              id: `hist-u-${idx}`,
              type: 'user',
              content: turn.message,
            }
          }

          if (turn.message_type === 'output') {
            return {
              id: `hist-o-${idx}`,
              type: 'output',
              content: turn.message,
              result: {
                improved_prompt: turn.improved_prompt || '',
                diff: [],
                quality_score: null,
                kira_message: turn.message,
                memories_applied: turn.memories_applied ?? 0,
                latency_ms: turn.latency_ms ?? 0,
                agents_run: [],
              },
              sessionId
            }
          }

          return {
            id: `hist-k-${idx}`,
            type: 'kira',
            content: turn.message,
          }
        })
        setMessages(mappedMessages)
        setHistoryLoadError(null)
        logger.info('[history] reload successful', { sessionId, count: mappedMessages.length })
      } catch (err) {
        logger.error('[history] reload failed', { err, sessionId })
        setHistoryLoadError('Failed to load conversation — tap to retry')
      }
    }
    
    loadHistory()
  }, [sessionId, token])

  return {
    messages,
    status,
    isStreaming,
    isRateLimited,
    rateLimitSecondsLeft,
    error,
    clarificationPending,
    clarificationOptions,
    historyLoadError,
    historyLoading,
    send,
    retry,
    clearError,
    reloadHistory,
  }
}

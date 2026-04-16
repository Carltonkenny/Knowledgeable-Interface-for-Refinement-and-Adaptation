// lib/stream.ts
// SSE parser for /chat/stream. This is the only place that knows about SSE event shapes.
// No component ever parses SSE directly.

import type { ChatResult } from './api'
import type { StreamCallbacks } from './types'

// ── SSE Event Types (must match backend exactly) ───────────────────────────

export type StreamEventType =
  | 'status'
  | 'kira_message'
  | 'classification'
  | 'result'
  | 'done'
  | 'error'
  | 'agent_update'

export interface StatusEvent {
  type: 'status'
  data: { message: string }
}

export interface KiraMessageEvent {
  type: 'kira_message'
  data: { message: string; complete: boolean }
}

export interface AgentUpdateEvent {
  type: 'agent_update'
  data: {
    agent: 'orchestrator' | 'intent' | 'context' | 'domain' | 'engineer'
    state: 'running' | 'complete' | 'skipped'
    latency_ms: number
    data?: any | null
    skip_reason?: string
    memories_applied?: number
  }
}

export interface ResultEvent {
  type: 'result'
  data: ChatResult
}

export interface ErrorEvent {
  type: 'error'
  data: { message: string; code?: string }
}

export type TypedStreamEvent =
  | StatusEvent
  | KiraMessageEvent
  | AgentUpdateEvent
  | ResultEvent
  | ErrorEvent
  | { type: 'classification'; data: unknown }
  | { type: 'done'; data: unknown }

// ── Parser ─────────────────────────────────────────────────────────────────

export async function parseStream(
  url: string,
  body: unknown,
  token: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  // Real SSE stream
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!res.ok) {
    callbacks.onError?.(`Request failed: ${res.status}`)
    return
  }

  if (!res.body) {
    callbacks.onError?.('No response body')
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''

    for (const block of blocks) {
      const lines = block.split('\n')
      let dataStr = ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          dataStr += line.slice(6)
        }
      }
      
      const raw = dataStr.trim()
      if (!raw || raw === '[DONE]') continue

      try {
        const event: TypedStreamEvent = JSON.parse(raw)
        switch (event.type) {
          case 'status':
            callbacks.onStatus?.((event.data as StatusEvent['data']).message)
            break
          case 'agent_update':
            callbacks.onAgentUpdate?.((event.data as AgentUpdateEvent['data']))
            break
          case 'kira_message':
            const km = event.data as KiraMessageEvent['data']
            callbacks.onKiraMessage?.(km.message, km.complete)
            break
          case 'result':
            callbacks.onResult?.(event.data as ChatResult)
            break
          case 'error':
            callbacks.onError?.((event.data as ErrorEvent['data']).message)
            break
          case 'done':
            callbacks.onDone?.()
            break
        }
      } catch (err) {
        // Malformed JSON from stream — surface error instead of silent catch
        const raw = dataStr.trim();
        if (typeof window !== 'undefined') {
          // Only log in browser context
          console.warn('[stream] SSE parse failed', { raw });
        }
        callbacks.onError?.('Stream parse error');
      }
    }
  }
}

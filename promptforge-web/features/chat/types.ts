// features/chat/types.ts
// Chat-specific types
// Import shared types from lib/types.ts — do not redeclare

import type { ChatMessage as BaseChatMessage, ProcessingStatus as BaseProcessingStatus } from '@/lib/types'
import type { ChatResult } from '@/lib/api'

export interface ChatSession {
  id: string
  user_id: string
  title: string
  created_at: string
  last_activity: string
}

// Chat-specific message extensions
export interface ChatMessage {
  id: string
  type: 'user' | 'status' | 'kira' | 'output' | 'error'
  content?: string
  result?: ChatResult  // for output type only
  isError?: boolean
  isStreaming?: boolean
  retryable?: boolean
  sessionId?: string
  memoryCitations?: MemoryCitation[]  // NEW: citations from memory system
}

// Agent update from backend streaming
export interface AgentUpdate {
  agent: 'orchestrator' | 'intent' | 'context' | 'domain' | 'engineer'
  state: 'running' | 'complete' | 'skipped'
  latency_ms: number
  data?: any | null
  skip_reason?: string
  memories_applied?: number
}

// Memory citation from backend (for expandable citation panel)
export interface MemoryCitation {
  id: string
  content: string      // Truncated preview (~120 chars)
  domain: string       // e.g., "python", "creative_writing"
  quality_score: number // 0-1 overall quality
  created_at: string   // ISO timestamp
}

// Chat-specific processing status
export interface ProcessingStatus {
  state: 'idle' | 'kira_reading' | 'swarm_running' | 'complete' | 'error' | 'rate_limited' | 'clarification'
  statusText?: string
  statusLogs: string[]
  startTime?: number
  agentsComplete: Set<string>
  agentsSkipped: Set<string>
  agentUpdates?: AgentUpdate[]
}

// Chat local state
export interface ChatState {
  messages: ChatMessage[]
  isStreaming: boolean
  isRateLimited: boolean
  rateLimitSecondsLeft: number
  error: string | null
  clarificationPending: boolean
  clarificationOptions: string[]
}

// Input bar state
export interface InputBarState {
  input: string
  attachment: File | null
  isRecording: boolean
}

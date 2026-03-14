// features/chat/types.ts
// Chat-specific types
// Import shared types from lib/types.ts — do not redeclare

import type { ChatMessage as BaseChatMessage, ProcessingStatus as BaseProcessingStatus } from '@/lib/types'
import type { ChatResult } from '@/lib/api'

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
}

// Chat-specific processing status
export interface ProcessingStatus {
  state: 'idle' | 'kira_reading' | 'swarm_running' | 'complete' | 'error' | 'rate_limited' | 'clarification'
  statusText?: string
  agentsComplete: Set<string>
  agentsSkipped: Set<string>
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

// ── Processing & State ─────────────────────────────────────────────────────
export type PersonaDotState  = 'cold' | 'warm' | 'tuned'
export type ProcessingState  = 'idle' | 'kira_reading' | 'swarm_running' | 'complete' | 'error' | 'rate_limited' | 'clarification'
export type InputModality    = 'text' | 'voice' | 'image' | 'file'
export type TrustLevel       = 0 | 1 | 2

// ── UI Variants ────────────────────────────────────────────────────────────
export type ChipVariant      = 'kira' | 'intent' | 'context' | 'domain' | 'engineer' | 'memory' | 'mcp' | 'teal' | 'success' | 'done'
export type MessageType      = 'user' | 'status' | 'kira' | 'output' | 'error'
export type ButtonVariant    = 'primary' | 'ghost' | 'kira' | 'danger' | 'paid' | 'waitlist'

// ── Onboarding ─────────────────────────────────────────────────────────────
export type OnboardingQuestionType = 'grid' | 'list' | 'chips'

// ── API Result Types (defined here so types.ts is self-contained) ─────────
export interface DiffItem {
  type: 'add' | 'remove' | 'keep'
  text: string
}

export interface QualityScore {
  specificity:    number  // 1-5
  clarity:        number  // 1-5
  actionability:  number  // 1-5
}

export interface ChatResult {
  improved_prompt: string
  diff: DiffItem[]
  quality_score: QualityScore
  kira_message: string
  memories_applied: number
  latency_ms: number
  agents_run: string[]
  // For conversation/followup responses
  type?: string
  reply?: string
}

// ── Chat Messages (used by useKiraStream + MessageList + all message components) ──
export interface ChatMessage {
  id: string
  type: MessageType
  content?: string           // for user, kira, error, status types
  result?: ChatResult        // for output type only
  isError?: boolean
  isStreaming?: boolean
  retryable?: boolean
}

// ── Processing Status (used by useKiraStream + StatusChips) ───────────────
export interface ProcessingStatus {
  state: ProcessingState
  statusText?: string        // latest status event message
  agentsComplete: Set<string>
  agentsSkipped: Set<string>
}

// ── Profile (used by profile feature + useProfile hook) ───────────────────
export interface UserProfileData {
  primary_use: string
  audience: string
  ai_frustration: string
  frustration_detail?: string
  session_count: number
  created_at: string
}

// ── Stream Callbacks (used by parseStream in lib/stream.ts) ───────────────
export interface StreamCallbacks {
  onStatus?:      (message: string) => void
  onAgentUpdate?: (update: {
    agent: 'orchestrator' | 'intent' | 'context' | 'domain' | 'engineer'
    state: 'running' | 'complete' | 'skipped'
    latency_ms: number
    data?: any | null
    skip_reason?: string
    memories_applied?: number
  }) => void
  onKiraMessage?: (message: string, complete: boolean) => void
  onResult?:      (result: import('./api').ChatResult) => void
  onError?:       (message: string) => void
  onDone?:        () => void
}

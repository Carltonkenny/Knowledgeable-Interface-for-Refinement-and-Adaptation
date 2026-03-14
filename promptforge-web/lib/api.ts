// lib/api.ts
// ALL backend calls go through here. No component, hook, or feature file
// ever calls fetch() directly. This is non-negotiable.

import { ENV } from './env'
import { MOCK_CHAT_RESULT, MOCK_HISTORY } from './mocks'

const API_BASE = process.env.NEXT_PUBLIC_API_URL!
const DEMO_API_BASE = process.env.NEXT_PUBLIC_DEMO_API_URL!

// ── Types ──────────────────────────────────────────────────────────────────

export interface ChatRequest {
  message: string
  session_id: string
  input_modality?: 'text' | 'voice' | 'image' | 'file'
  file_base64?: string
  file_type?: string
}

export interface ChatResult {
  improved_prompt: string
  diff: DiffItem[]
  quality_score: QualityScore | null
  kira_message: string
  memories_applied: number
  latency_ms: number
  agents_run: string[]
  version_id?: string
  version_number?: number
  // For conversation/followup responses (RULES.md: Type-safe response shape)
  type?: string
  reply?: string
}

export interface DiffItem {
  type: 'add' | 'remove' | 'keep'
  text: string
}

export interface QualityScore {
  specificity: number  // 1-5
  clarity: number  // 1-5
  actionability: number  // 1-5
}

export interface HistoryItem {
  id: string
  raw_prompt: string
  improved_prompt: string
  quality_score: any // Updated in migration 018 to JSONB
  domain_analysis: any // Added in migration 018
  created_at: string
  session_id: string
  version_id?: string
  version_number?: number
}

export interface SearchQuery {
  query: string
  use_rag?: boolean
  domains?: string[]
  min_quality?: number
  date_from?: string
  date_to?: string
  limit?: number
}

export interface HistoryAnalytics {
  total_prompts: number
  avg_quality: number
  unique_domains: number
  hours_saved: number
  quality_trend: Array<{ date: string; avg_quality: number; prompt_count: number }>
  domain_distribution: Record<string, number>
  session_activity: Array<{ date: string; count: number }>
}

export interface HistorySession {
  session_id: string
  title: string
  prompt_count: number
  avg_quality: number
  domain: string
  prompts: HistoryItem[]
  created_at: string
  last_activity: string
}

export interface UserProfile {
  primary_use: string
  audience: string
  ai_frustration: string
  frustration_detail?: string
}

export interface ChatSession {
  id: string
  user_id: string
  title: string
  is_pinned: boolean
  is_favorite: boolean
  deleted_at: string | null
  created_at: string
  last_activity: string
}

export interface ConversationTurn {
  role: 'user' | 'assistant'
  message: string
  message_type: 'chat' | 'output' | 'status'
  improved_prompt?: string
}

// ── Phase 4: Profile Types ──────────────────────────────────────────────────
export interface UserProfile {
  username?: string
}

export interface DomainStat {
  domain: string
  confidence: number
  interaction_count: number
  last_active: string
}

export interface MemoryPreview {
  id: string
  content: string
  category: string
  created_at: string
}

export interface QualityTrendPoint {
  index: number
  score: number
  date: string
}

export interface UsageStats {
  total_prompts_engineered: number
  active_chat_sessions: number
  average_quality_score: number
  member_since: string
}

export interface ExportData {
  export_date: string
  user_id: string
  profile: any
  requests: any[]
  sessions: any[]
  conversations: any[]
}

// ── Internal helpers ───────────────────────────────────────────────────────

async function authHeaders(token?: string): Promise<HeadersInit> {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token ?? ''}`,
  }
}

// ── Endpoints ──────────────────────────────────────────────────────────────

export async function apiHealth(): Promise<boolean> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 100))
    return true
  }
  try {
    const res = await fetch(`${API_BASE}/health`, { method: 'GET' })
    return res.ok
  } catch {
    return false
  }
}

export async function apiChat(
  req: ChatRequest,
  token: string
): Promise<ChatResult> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 1200))
    return MOCK_CHAT_RESULT
  }
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: await authHeaders(token),
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiHistory(
  token: string,
  sessionId?: string
): Promise<HistoryItem[]> {
  const url = sessionId
    ? `${API_BASE}/history?session_id=${sessionId}`
    : `${API_BASE}/history`
  const res = await fetch(url, { headers: await authHeaders(token) })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  const data = await res.json()
  // Backend returns {count, history} - extract the history array
  return data.history || data || []
}

export async function apiHistorySearch(
  token: string,
  req: SearchQuery
): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/history/search`, {
    method: 'POST',
    headers: await authHeaders(token),
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  const data = await res.json()
  return data.results || []
}

export async function apiHistoryAnalytics(
  token: string,
  days: number = 30
): Promise<HistoryAnalytics> {
  const res = await fetch(`${API_BASE}/history/analytics?days=${days}`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiHistorySessions(
  token: string,
  limit: number = 20
): Promise<HistorySession[]> {
  const res = await fetch(`${API_BASE}/history/sessions?limit=${limit}`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  const data = await res.json()
  return data.sessions || []
}

// ═══ Version Control API Functions (Phase 3) ═══════════════

export interface VersionData {
  id: string
  version_id: string
  version_number: number
  change_summary: string
  created_at: string
  is_production: boolean
  raw_prompt: string
  improved_prompt: string
}

export async function apiCreateVersion(
  token: string,
  req: {
    raw_prompt: string
    improved_prompt: string
    change_summary: string
    session_id: string
  }
): Promise<{ version_id: string; version_number: number; id: string }> {
  const res = await fetch(`${API_BASE}/history/version`, {
    method: 'POST',
    headers: await authHeaders(token),
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiGetVersionHistory(
  token: string,
  versionId: string
): Promise<{ versions: VersionData[]; total: number; current_version: number }> {
  const res = await fetch(`${API_BASE}/history/version/${versionId}`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiRollbackVersion(
  token: string,
  versionId: string,
  targetVersionNumber: number
): Promise<{ success: boolean; rolled_back_to: number }> {
  const res = await fetch(
    `${API_BASE}/history/version/${versionId}/rollback?target_version_number=${targetVersionNumber}`,
    {
      method: 'POST',
      headers: await authHeaders(token),
    }
  )
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiCompareVersions(
  token: string,
  versionId: string,
  v1: number,
  v2: number
): Promise<{ version_1: VersionData; version_2: VersionData; diff: any }> {
  const res = await fetch(
    `${API_BASE}/history/compare?version_id=${versionId}&v1=${v1}&v2=${v2}`,
    {
      headers: await authHeaders(token),
    }
  )
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiConversation(
  token: string,
  sessionId: string
): Promise<ConversationTurn[]> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 300))
    return []
  }
  const res = await fetch(
    `${API_BASE}/conversation?session_id=${sessionId}`,
    { headers: await authHeaders(token) }
  )
  if (!res.ok) throw new ApiError(res.status, await res.text())
  const data = await res.json()
  // Backend returns {count, conversation}
  return data.conversation || []
}

export async function apiTranscribe(
  audioBlob: Blob,
  token: string
): Promise<{ transcript: string }> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 500))
    return { transcript: 'This is a mock transcript for development.' }
  }
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.webm')
  const res = await fetch(`${API_BASE}/transcribe`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: form,
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiSaveProfile(
  profile: UserProfile,
  token: string
): Promise<void> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 200))
    return
  }
  const res = await fetch(`${API_BASE}/user/profile`, {
    method: 'POST',
    headers: await authHeaders(token),
    body: JSON.stringify(profile),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
}

export async function apiRefine(
  prompt: string,
  token: string
): Promise<ChatResult> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 1000))
    return MOCK_CHAT_RESULT
  }
  const res = await fetch(`${API_BASE}/refine`, {
    method: 'POST',
    headers: await authHeaders(token),
    body: JSON.stringify({ prompt }),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiListSessions(token: string): Promise<ChatSession[]> {
  if (ENV.USE_MOCKS) return []
  const res = await fetch(`${API_BASE}/sessions`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiCreateSession(token: string): Promise<ChatSession> {
  if (ENV.USE_MOCKS) throw new Error('Mocks not implemented for session creation')
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiDeleteSession(token: string, sessionId: string): Promise<void> {
  if (ENV.USE_MOCKS) return
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
}

export async function apiPatchSession(
  token: string,
  sessionId: string,
  updates: Partial<Pick<ChatSession, 'title' | 'is_pinned' | 'is_favorite'>>
): Promise<ChatSession> {
  if (ENV.USE_MOCKS) throw new Error('Mocks not implemented')
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: await authHeaders(token),
    body: JSON.stringify(updates),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiRestoreSession(token: string, sessionId: string): Promise<void> {
  if (ENV.USE_MOCKS) return
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/restore`, {
    method: 'POST',
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
}

export async function apiPurgeSession(token: string, sessionId: string): Promise<void> {
  if (ENV.USE_MOCKS) return
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/purge`, {
    method: 'DELETE',
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
}

export async function apiListDeletedSessions(token: string): Promise<ChatSession[]> {
  if (ENV.USE_MOCKS) return []
  const res = await fetch(`${API_BASE}/sessions/deleted`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

// Demo endpoint — uses demo account, no auth token required from user
export async function apiDemoChat(
  message: string
): Promise<ChatResult> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 1200))
    return MOCK_CHAT_RESULT
  }
  const res = await fetch(`${DEMO_API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: 'demo-session',
      demo: true,
    }),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

// ── Phase 4: Profile ─────────────────────────────────────────────────────────

export async function apiUpdateUsername(token: string, username: string): Promise<{ status: string, username: string }> {
  if (ENV.USE_MOCKS) return { status: 'success', username }
  const res = await fetch(`${API_BASE}/user/username`, {
    method: 'PATCH',
    headers: await authHeaders(token),
    body: JSON.stringify({ username }),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiGetDomains(token: string): Promise<{ domains: DomainStat[] }> {
  if (ENV.USE_MOCKS) return { domains: [] }
  const res = await fetch(`${API_BASE}/user/domains`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiGetMemories(token: string): Promise<{ memories: MemoryPreview[] }> {
  if (ENV.USE_MOCKS) return { memories: [] }
  const res = await fetch(`${API_BASE}/user/memories`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiGetQualityTrend(token: string): Promise<{ trend: QualityTrendPoint[] }> {
  if (ENV.USE_MOCKS) return { trend: [] }
  const res = await fetch(`${API_BASE}/user/quality-trend`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiGetStats(token: string): Promise<UsageStats> {
  if (ENV.USE_MOCKS) return { total_prompts_engineered: 0, active_chat_sessions: 0, average_quality_score: 0, member_since: '' }
  const res = await fetch(`${API_BASE}/user/stats`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiDeleteAccount(token: string): Promise<{ status: string, message: string }> {
  if (ENV.USE_MOCKS) return { status: 'success', message: 'MOCK' }
  const res = await fetch(`${API_BASE}/user/account`, {
    method: 'DELETE',
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiExportData(token: string): Promise<ExportData> {
  if (ENV.USE_MOCKS) throw new Error('Mocks not implemented')
  const res = await fetch(`${API_BASE}/user/export-data`, {
    headers: await authHeaders(token),
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

// ── Error class ────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

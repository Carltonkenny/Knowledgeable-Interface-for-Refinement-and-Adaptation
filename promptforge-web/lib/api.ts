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
  quality_score: QualityScore
  kira_message: string
  memories_applied: number
  latency_ms: number
  agents_run: string[]
}

export interface DiffItem {
  type: 'add' | 'remove' | 'keep'
  text: string
}

export interface QualityScore {
  specificity:    number  // 1-5
  clarity:        number  // 1-5
  actionability:  number  // 1-5
}

export interface HistoryItem {
  id: string
  original_prompt: string
  improved_prompt: string
  quality_score: QualityScore
  created_at: string
  session_id: string
}

export interface UserProfile {
  primary_use: string
  audience: string
  ai_frustration: string
  frustration_detail?: string
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
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 400))
    return MOCK_HISTORY
  }
  const url = sessionId
    ? `${API_BASE}/history?session_id=${sessionId}`
    : `${API_BASE}/history`
  const res = await fetch(url, { headers: await authHeaders(token) })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function apiConversation(
  token: string,
  sessionId: string
): Promise<unknown[]> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 300))
    return []
  }
  const res = await fetch(
    `${API_BASE}/conversation?session_id=${sessionId}`,
    { headers: await authHeaders(token) }
  )
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
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

// ── Error class ────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

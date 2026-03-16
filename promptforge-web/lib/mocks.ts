// lib/mocks.ts
// Mock data for development and agent self-verification.
// Controlled by NEXT_PUBLIC_USE_MOCKS=true via lib/env.ts

import type { ChatResult, HistoryItem } from './api'
import type { ProcessingStatus } from './types'

// ── Mock API results ───────────────────────────────────────────────────────

export const MOCK_CHAT_RESULT: ChatResult = {
  improved_prompt: "Write a professional email to [client name] regarding [project name]. Tone: confident and clear. Include: what was accomplished, what it means for the timeline, and a clear next step. Length: under 200 words.",
  diff: [
    { type: 'keep',   text: 'Write a ' },
    { type: 'add',    text: 'professional ' },
    { type: 'keep',   text: 'email to ' },
    { type: 'remove', text: 'my client' },
    { type: 'add',    text: '[client name]' },
    { type: 'keep',   text: ' regarding ' },
    { type: 'remove', text: 'the project' },
    { type: 'add',    text: '[project name]' },
    { type: 'add',    text: '. Tone: confident and clear. Include: what was accomplished, what it means for the timeline, and a clear next step. Length: under 200 words.' },
  ],
  quality_score: { specificity: 4, clarity: 5, actionability: 3 },
  kira_message: "On it. Treating this as client comms. Here's your engineered prompt ↓",
  memories_applied: 2,
  latency_ms: 3400,
  agents_run: [],
}

export const MOCK_HISTORY: HistoryItem[] = [
  {
    id: 'mock-hist-1',
    raw_prompt: 'help me write an email to my client',
    improved_prompt: MOCK_CHAT_RESULT.improved_prompt,
    quality_score: MOCK_CHAT_RESULT.quality_score,
    domain_analysis: null,
    created_at: new Date().toISOString(),
    session_id: 'mock-session-1',
  },
  {
    id: 'mock-hist-2',
    raw_prompt: 'write a linkedin post',
    improved_prompt: 'Write a LinkedIn post for a B2B SaaS audience about [topic]. Tone: direct and insight-driven. Format: one hook line, 3 key points, one CTA. Under 200 words.',
    quality_score: { specificity: 5, clarity: 4, actionability: 5 },
    domain_analysis: null,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    session_id: 'mock-session-1',
  },
]

// ── Mock SSE sequence (used by stream.ts when USE_MOCKS=true) ──────────────
// Simulates the full SSE event stream with realistic timing.

export const MOCK_SSE_SEQUENCE = [
  { delay: 200,  event: { type: 'status',       data: { message: 'Analyzing intent...' } } },
  { delay: 600,  event: { type: 'status',       data: { message: 'Engineering prompt...' } } },
  { delay: 900,  event: { type: 'kira_message', data: { message: 'On it.', complete: false } } },
  { delay: 1200, event: { type: 'kira_message', data: { message: "On it. Treating this as client comms. Here's your engineered prompt ↓", complete: true } } },
  { delay: 1400, event: { type: 'result',       data: MOCK_CHAT_RESULT } },
  { delay: 1500, event: { type: 'done',         data: {} } },
] as const

// ── Mock profile ───────────────────────────────────────────────────────────

export const MOCK_PROFILE = {
  primary_use: 'Marketing',
  audience: 'External customers or clients',
  ai_frustration: 'Too generic, Wrong tone',
  session_count: 7,
  created_at: new Date(Date.now() - 7 * 86400000).toISOString(),
}

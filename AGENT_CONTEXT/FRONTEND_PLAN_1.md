# FRONTEND PLAN 1 — Foundation + Design System
### PromptForge v2.0 · Next.js 14 · Tailwind · Supabase Auth JS
---

## 1. CONTEXT

### What exists before this plan
- Backend: FastAPI on Railway or Koyeb (Docker container), fully deployed. 7 endpoints, JWT auth, Supabase, Redis, SSE streaming.
- Supabase project: `cckznjkzsfypssgecyya` — auth, RLS, all 8 tables ready.
- No frontend repo exists yet.

### What this plan builds
Everything else imports from here. No feature code. No pages. Only the shared infrastructure layer that Plans 2, 3, and 4 depend on.

### What this plan must NOT touch
- `promptforge/` backend directory — zero changes
- Any Supabase migration files
- Backend `.env` file

### Assumptions
- Node 18+ installed
- `promptforge-web/` is a sibling directory to `promptforge/` in the monorepo root
- `create-next-app` has been run with: App Router, TypeScript, Tailwind, no src/ directory, no default turbopack
- `.env.local` exists at `promptforge-web/.env.local` with:
  ```
  NEXT_PUBLIC_SUPABASE_URL=https://cckznjkzsfypssgecyya.supabase.co
  NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon key>
  NEXT_PUBLIC_API_URL=https://<your-backend>.up.railway.app
  NEXT_PUBLIC_DEMO_API_URL=https://<your-backend>.up.railway.app
  NEXT_PUBLIC_USE_MOCKS=false
  ```

---

## 2. FILES TO CREATE

```
promptforge-web/
├── styles/
│   └── globals.css              ← ALL design tokens + base reset. Source of truth.
├── lib/
│   ├── types.ts                 ← [NEW] ALL shared types. Single source of truth.
│   ├── mocks.ts                 ← [NEW] Mock data for development. Agent self-verification.
│   ├── env.ts                   ← [NEW] Env validation on startup. Fails loudly if vars missing.
│   ├── logger.ts                ← [NEW] Frontend error logging wrapper. All errors go through here.
│   ├── constants.ts             ← App-wide constants (routes, limits, messages)
│   ├── supabase.ts              ← Supabase browser client (singleton)
│   ├── api.ts                   ← ALL backend calls. No component ever calls fetch() directly.
│   ├── stream.ts                ← SSE parser + event type definitions
│   └── errors.ts                ← Error mapping. All errors pass through here before UI.
├── components/
│   └── ui/
│       ├── Button.tsx           ← All button variants
│       ├── Input.tsx            ← All input variants
│       ├── Chip.tsx             ← Status chips (agent, memory, latency)
│       └── index.ts             ← Barrel export
├── tailwind.config.ts           ← Extend Tailwind with design tokens
└── verify.sh                    ← [NEW] Automated checks. Agent runs after every step.
```

---

## 3. FILE SPECIFICATIONS

### `styles/globals.css`

This is the single source of truth for ALL design tokens. Tailwind config reads from here. No component ever hardcodes a color hex.

```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Satoshi:wght@300;400;500;700&display=swap');

:root {
  /* ── SURFACES ── */
  --bg:      #070809;
  --layer-1: #0d0f12;
  --layer-2: #131519;
  --layer-3: #181b21;
  --layer-4: #1c2028;

  /* ── BORDERS ── */
  --border-subtle:  #141720;
  --border-default: #1c1f26;
  --border-strong:  #252830;
  --border-bright:  #2d3340;

  /* ── TEXT ── */
  --text-bright:  #f8fafc;
  --text-default: #cbd5e1;
  --text-dim:     #475569;
  --text-muted:   #2d3340;

  /* ── BRAND — KIRA (indigo) ── */
  --kira:      #6366f1;
  --kira-dim:  rgba(99,102,241,0.15);
  --kira-glow: rgba(99,102,241,0.08);
  --kira-glow-strong: rgba(99,102,241,0.25);

  /* ── AGENT COLORS — each has ONE job ── */
  /* Intent agent · Error states · Diff removals */
  --intent:     #f43f5e;
  --intent-dim: rgba(244,63,94,0.12);

  /* Context agent · Diff additions · Positive stats */
  --context:     #10b981;
  --context-dim: rgba(16,185,129,0.12);

  /* Domain agent · Warm dot (session 10-30) · Rate limit */
  --domain:     #f59e0b;
  --domain-dim: rgba(245,158,11,0.12);

  /* Prompt Engineer chip · Push Further · Premium signals */
  --engineer:     #8b5cf6;
  --engineer-dim: rgba(139,92,246,0.12);

  /* Profile data · Stats · Sparklines */
  --profile:     #38bdf8;
  --profile-dim: rgba(56,189,248,0.12);

  /* Memory signals only · "2 memories applied" */
  --memory:     #ec4899;
  --memory-dim: rgba(236,72,153,0.12);

  /* MCP surface only · Token section · Trust indicators */
  --mcp:     #fb923c;
  --mcp-dim: rgba(251,146,60,0.12);

  /* Latency/time displays only */
  --teal:     #14b8a6;
  --teal-dim: rgba(20,184,166,0.10);

  /* Success · Tuned dot (30+ sessions) · Completion */
  --success:     #22c55e;
  --success-dim: rgba(34,197,94,0.10);

  /* Coming soon badges · Waitlist signals */
  --coming:     #f59e0b;
  --coming-dim: rgba(245,158,11,0.12);

  /* ── TYPOGRAPHY ── */
  --font-mono:    'JetBrains Mono', monospace;
  --font-display: 'Satoshi', sans-serif;

  /* ── PERSONA DOTS ── */
  --dot-cold:  #475569;  /* Session 0-9: grey */
  --dot-warm:  #f59e0b;  /* Session 10-29: amber */
  --dot-tuned: #22c55e;  /* Session 30+: green */

  /* ── OUTPUT TEXT — brightest thing on screen ── */
  --output-text: #f8fafc;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
  background-color: var(--bg);
  color: var(--text-default);
  font-family: var(--font-display);
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Reveal animation — IntersectionObserver will add .visible */
.reveal {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.reveal.visible {
  opacity: 1;
  transform: none;
}
/* Staggered reveals */
.reveal-delay-1 { transition-delay: 0.1s; }
.reveal-delay-2 { transition-delay: 0.2s; }
.reveal-delay-3 { transition-delay: 0.3s; }
.reveal-delay-4 { transition-delay: 0.4s; }

@media (prefers-reduced-motion: reduce) {
  .reveal, .reveal-delay-1, .reveal-delay-2, .reveal-delay-3, .reveal-delay-4 {
    opacity: 1;
    transform: none;
    transition: none;
  }
}

/* Gradient text utility */
.gradient-text {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Persona dot pulse */
@keyframes dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* Chip dot pulse (active agents) */
@keyframes chip-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Live indicator */
@keyframes live-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-bright); }
```

---

### `lib/types.ts`

**Single source of truth for ALL types shared across more than one file. Every boundary-crossing type lives here. Component-local types stay in their component file. Import from here, never redeclare.**

```typescript
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

// ── Chat Messages (used by useKiraStream + MessageList + all message components) ──
// Note: ChatResult is imported from ./api — types.ts depends on api.ts, not vice versa.
export interface ChatMessage {
  id: string
  type: MessageType
  content?: string           // for user, kira, error, status types
  result?: import('./api').ChatResult  // for output type only — api.ts does NOT import types.ts
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
```

---

### `lib/logger.ts`

**Centralised frontend error logging. Every caught error goes through here. Swap internals once when you add Sentry — no component changes needed.**

```typescript
// lib/logger.ts

type LogContext = Record<string, unknown>

export const logger = {
  error(message: string, context?: LogContext, error?: unknown) {
    console.error('[PromptForge]', message, context ?? '', error ?? '')
    // Production hook — add Sentry here when ready, nothing else changes
    if (process.env.NODE_ENV === 'production') {
      // Future: Sentry.captureException(error, { extra: { message, ...context } })
    }
  },

  warn(message: string, context?: LogContext) {
    console.warn('[PromptForge]', message, context ?? '')
  },

  info(message: string, context?: LogContext) {
    if (process.env.NODE_ENV === 'development') {
      console.info('[PromptForge]', message, context ?? '')
    }
  },
}
```

**Rules for using logger:**
- Use `logger.error()` everywhere a catch block exists — never raw `console.error()`
- Use `logger.warn()` for non-fatal issues (e.g. profile save failed but navigation continues)
- NEVER log user prompt content — privacy rule
- NEVER log JWT tokens, session IDs, or API keys
- Does NOT show anything to users — that is `lib/errors.ts` + Kira's voice messages

---

### `lib/env.ts`

**Validates all required environment variables on startup. Fails loudly with a clear message rather than cryptic undefined errors later.**

```typescript
// lib/env.ts
// Called in app/layout.tsx — runs once on server startup.
// Agent self-check: if this file throws, env is misconfigured.

const REQUIRED_VARS = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_DEMO_API_URL',
] as const

export function validateEnv(): void {
  const missing: string[] = []
  for (const key of REQUIRED_VARS) {
    if (!process.env[key]) missing.push(key)
  }
  if (missing.length > 0) {
    throw new Error(
      `[PromptForge] Missing required environment variables:\n${missing.map(k => `  - ${k}`).join('\n')}\n\nCheck promptforge-web/.env.local`
    )
  }
}

// Typed env access — never use process.env directly in components
export const ENV = {
  SUPABASE_URL:    process.env.NEXT_PUBLIC_SUPABASE_URL!,
  SUPABASE_ANON:   process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  API_URL:         process.env.NEXT_PUBLIC_API_URL!,
  DEMO_API_URL:    process.env.NEXT_PUBLIC_DEMO_API_URL!,
  USE_MOCKS:       process.env.NEXT_PUBLIC_USE_MOCKS === 'true',
} as const
```

---

### `lib/mocks.ts`

**Mock data for development and agent self-verification. Enables the full UI to run without a live backend. Controlled by `NEXT_PUBLIC_USE_MOCKS=true`.**

**When to use:** Agent sets `NEXT_PUBLIC_USE_MOCKS=true` during Plan 4 development to verify UI without credentials. You set it back to `false` before real verification.

```typescript
import type { ChatResult, HistoryItem } from './api'
import type { ChatMessage, ProcessingStatus } from './types'

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
    original_prompt: 'help me write an email to my client',
    improved_prompt: MOCK_CHAT_RESULT.improved_prompt,
    quality_score: MOCK_CHAT_RESULT.quality_score,
    created_at: new Date().toISOString(),
    session_id: 'mock-session-1',
  },
  {
    id: 'mock-hist-2',
    original_prompt: 'write a linkedin post',
    improved_prompt: 'Write a LinkedIn post for a B2B SaaS audience about [topic]. Tone: direct and insight-driven. Format: one hook line, 3 key points, one CTA. Under 200 words.',
    quality_score: { specificity: 5, clarity: 4, actionability: 5 },
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
```

**Wire mocks into `lib/api.ts`** — add this block at the top of `api.ts` after the imports:

```typescript
import { ENV } from './env'
import { MOCK_CHAT_RESULT, MOCK_HISTORY, MOCK_SSE_SEQUENCE } from './mocks'

// Inside apiChat():
if (ENV.USE_MOCKS) {
  await new Promise(r => setTimeout(r, 1200))
  return MOCK_CHAT_RESULT
}

// Inside apiHistory():
if (ENV.USE_MOCKS) {
  await new Promise(r => setTimeout(r, 400))
  return MOCK_HISTORY
}
```

**Wire mocks into `lib/stream.ts`** — add mock stream path to `parseStream()`:

```typescript
import { ENV } from './env'
import { MOCK_SSE_SEQUENCE } from './mocks'

// At the top of parseStream(), before the real fetch:
if (ENV.USE_MOCKS) {
  for (const { delay, event } of MOCK_SSE_SEQUENCE) {
    await new Promise(r => setTimeout(r, delay))
    if (signal?.aborted) return
    switch (event.type) {
      case 'status':       callbacks.onStatus?.(event.data.message); break
      case 'kira_message': callbacks.onKiraMessage?.(event.data.message, event.data.complete); break
      case 'result':       callbacks.onResult?.(event.data as ChatResult); break
      case 'done':         callbacks.onDone?.(); break
    }
  }
  return
}
// real fetch follows below
```

---

### `verify.sh`

**Automated verification script. Agent runs this after every build step. You run this before merging each plan. A clean run = green light.**

```bash
#!/bin/bash
# promptforge-web/verify.sh
# Usage: bash verify.sh
# Run from promptforge-web/ directory.
# Exit 0 = all checks passed. Exit 1 = something is wrong.

set -e
cd "$(dirname "$0")"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PromptForge Frontend — Verify"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. TypeScript ──────────────────────────────────────────────────────────
echo "[ 1/5 ] TypeScript..."
npx tsc --noEmit
echo "  ✅ TypeScript clean"
echo ""

# ── 2. Build ───────────────────────────────────────────────────────────────
echo "[ 2/5 ] Build..."
npm run build > /tmp/pf_build.log 2>&1 || {
  echo "  ❌ Build failed. Last 20 lines:"
  tail -20 /tmp/pf_build.log
  exit 1
}
echo "  ✅ Build passes"
echo ""

# ── 3. Security scan — forbidden strings in source ────────────────────────
echo "[ 3/5 ] Security scan..."
FORBIDDEN=("intent agent" "context agent" "domain agent" "prompt_engineer" "GPT-4o" "gpt-4o-mini" "langmem" "LangGraph" "fly.dev" "cckznjkzsfypssgecyya" "openai.com")
FAIL=0
for term in "${FORBIDDEN[@]}"; do
  FOUND=$(grep -r "$term" app/ features/ --include="*.tsx" --include="*.ts" -l 2>/dev/null | grep -v "\.test\." || true)
  if [ -n "$FOUND" ]; then
    echo "  ❌ SECURITY: '$term' found in:"
    echo "$FOUND" | sed 's/^/     /'
    FAIL=1
  fi
done
if [ $FAIL -eq 1 ]; then exit 1; fi
echo "  ✅ Security scan clean"
echo ""

# ── 4. No rogue fetch() outside lib/ ──────────────────────────────────────
echo "[ 4/5 ] Architecture check (no rogue fetch)..."
ROGUE=$(grep -r "fetch(" app/ features/ components/ --include="*.tsx" --include="*.ts" -l 2>/dev/null | grep -v "route\.ts" || true)
if [ -n "$ROGUE" ]; then
  echo "  ❌ fetch() found outside lib/api.ts or lib/stream.ts in:"
  echo "$ROGUE" | sed 's/^/     /'
  exit 1
fi
echo "  ✅ No rogue fetch() calls"
echo ""

# ── 5. No 'use client' in app/(marketing)/ ────────────────────────────────
echo "[ 5/5 ] Server component check..."
if [ -d "app/(marketing)" ]; then
  CLIENT=$(grep -r "'use client'" "app/(marketing)/" --include="*.tsx" --include="*.ts" -l 2>/dev/null || true)
  if [ -n "$CLIENT" ]; then
    echo "  ❌ 'use client' found in app/(marketing)/:"
    echo "$CLIENT" | sed 's/^/     /'
    exit 1
  fi
fi
echo "  ✅ Server components clean"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ALL CHECKS PASSED ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
```

Make executable after creation: `chmod +x verify.sh`

---

### `tailwind.config.ts`

Extends Tailwind with CSS variable references. Never hardcode colors in className strings.

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './features/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg:       'var(--bg)',
        layer1:   'var(--layer-1)',
        layer2:   'var(--layer-2)',
        layer3:   'var(--layer-3)',
        layer4:   'var(--layer-4)',
        kira:     'var(--kira)',
        intent:   'var(--intent)',
        context:  'var(--context)',
        domain:   'var(--domain)',
        engineer: 'var(--engineer)',
        profile:  'var(--profile)',
        memory:   'var(--memory)',
        mcp:      'var(--mcp)',
        teal:     'var(--teal)',
        success:  'var(--success)',
        'text-bright':  'var(--text-bright)',
        'text-default': 'var(--text-default)',
        'text-dim':     'var(--text-dim)',
        'text-muted':   'var(--text-muted)',
        'border-subtle':  'var(--border-subtle)',
        'border-default': 'var(--border-default)',
        'border-strong':  'var(--border-strong)',
        'border-bright':  'var(--border-bright)',
      },
      fontFamily: {
        mono:    ['JetBrains Mono', 'monospace'],
        display: ['Satoshi', 'sans-serif'],
      },
      boxShadow: {
        'kira':       '0 0 16px rgba(99,102,241,0.25)',
        'kira-strong':'0 0 20px rgba(99,102,241,0.4), 0 2px 8px rgba(0,0,0,0.4)',
        'memory':     '0 0 12px rgba(236,72,153,0.3)',
        'tuned':      '0 0 8px rgba(34,197,94,0.6), 0 0 20px rgba(34,197,94,0.2)',
        'card':       '0 8px 32px rgba(99,102,241,0.08), 0 2px 8px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
}

export default config
```

---

### `lib/constants.ts`

```typescript
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  ONBOARDING: '/onboarding',
  APP: '/app',
  HISTORY: '/app/history',
  PROFILE: '/app/profile',
} as const

export const API_ROUTES = {
  HEALTH:      '/health',
  CHAT:        '/chat',
  CHAT_STREAM: '/chat/stream',
  REFINE:      '/refine',
  TRANSCRIBE:  '/transcribe',
  HISTORY:     '/history',
  CONVERSATION:'/conversation',
  PROFILE_SAVE:'/user/profile',
} as const

export const LIMITS = {
  PROMPT_MIN:        5,
  PROMPT_MAX:        2000,
  FILE_MAX_BYTES:    2 * 1024 * 1024,  // 2MB
  IMAGE_MAX_BYTES:   5 * 1024 * 1024,  // 5MB
  DEMO_MAX_USES:     3,
  DEMO_STORAGE_KEY:  'pf_demo_uses',
  SESSION_STORAGE_KEY: 'pf_session_id',
} as const

export const PERSONA_DOT_THRESHOLDS = {
  COLD:  0,   // grey  — session 0-9
  WARM:  10,  // amber — session 10-29
  TUNED: 30,  // green — session 30+
} as const

export const KIRA_ERROR_MESSAGES = {
  NETWORK:     "Something broke on my end. Your prompt is safe — try again.",
  RATE_LIMIT:  "You're moving fast. Give me 30 seconds to catch up.",
  AUTH:        "Session expired. Sign back in and we'll pick up where we left off.",
  VALIDATION:  "That's too short for me to work with. Give me a bit more context.",
  SERVER:      "Backend's having a moment. Your prompt is safe — try again.",
  UNKNOWN:     "Something went wrong. Your prompt is safe — try again.",
} as const

export const ONBOARDING_QUESTIONS = [
  {
    id: 'primary_use',
    question: 'What do you mostly use AI for?',
    type: 'grid' as const,
    options: [
      { label: 'Writing',   icon: '✍️' },
      { label: 'Code',      icon: '💻' },
      { label: 'Marketing', icon: '📣' },
      { label: 'Research',  icon: '🔬' },
      { label: 'Product',   icon: '🗺️' },
      { label: 'Other',     icon: '✦' },
    ],
  },
  {
    id: 'audience',
    question: 'Who do you usually write for?',
    type: 'list' as const,
    options: [
      { label: 'Just me / internal teams' },
      { label: 'External customers or clients' },
      { label: 'Both — depends on the day' },
    ],
  },
  {
    id: 'ai_frustration',
    question: "What does AI keep getting wrong for you?",
    type: 'chips' as const,
    options: [
      { label: 'Too generic' },
      { label: 'Wrong tone' },
      { label: 'Misses context' },
      { label: 'Too long' },
      { label: 'Too formal' },
      { label: 'Off-brand' },
    ],
    hasTextFallback: true,
    textPlaceholder: "Or describe it in your own words...",
  },
] as const
```

---

### `lib/supabase.ts`

```typescript
import { createBrowserClient } from '@supabase/ssr'

let client: ReturnType<typeof createBrowserClient> | null = null

export function getSupabaseClient() {
  if (!client) {
    client = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  }
  return client
}

export async function getSession() {
  const supabase = getSupabaseClient()
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

export async function getAccessToken(): Promise<string | null> {
  const session = await getSession()
  return session?.access_token ?? null
}

export async function signOut() {
  const supabase = getSupabaseClient()
  await supabase.auth.signOut()
}
```

---

### `lib/api.ts`

**Every backend call goes through here. No component, hook, or feature file ever calls `fetch()` directly. This is non-negotiable.**

```typescript
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
  return res.json()
}

export async function apiConversation(
  token: string,
  sessionId: string
): Promise<unknown[]> {
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
```

---

### `lib/stream.ts`

**SSE parser for `/chat/stream`. This is the only place that knows about SSE event shapes. No component ever parses SSE directly.**

```typescript
import type { ChatResult, DiffItem, QualityScore } from './api'

// ── SSE Event Types (must match backend exactly) ───────────────────────────

export type StreamEventType =
  | 'status'
  | 'kira_message'
  | 'classification'
  | 'result'
  | 'done'
  | 'error'

export interface StreamEvent {
  type: StreamEventType
  data: unknown
}

export interface StatusEvent {
  type: 'status'
  data: { message: string }
}

export interface KiraMessageEvent {
  type: 'kira_message'
  data: { message: string; complete: boolean }
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
  | ResultEvent
  | ErrorEvent
  | { type: 'classification'; data: unknown }
  | { type: 'done'; data: unknown }

// ── Callbacks ──────────────────────────────────────────────────────────────

export interface StreamCallbacks {
  onStatus?:      (message: string) => void
  onKiraMessage?: (message: string, complete: boolean) => void
  onResult?:      (result: ChatResult) => void
  onError?:       (message: string) => void
  onDone?:        () => void
}

// ── Parser ─────────────────────────────────────────────────────────────────

export async function parseStream(
  url: string,
  body: unknown,
  token: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
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
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const raw = line.slice(6).trim()
      if (!raw || raw === '[DONE]') continue

      try {
        const event: TypedStreamEvent = JSON.parse(raw)
        switch (event.type) {
          case 'status':
            callbacks.onStatus?.((event.data as StatusEvent['data']).message)
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
      } catch {
        // Malformed JSON from stream — skip silently
      }
    }
  }
}
```

---

### `lib/errors.ts`

**All errors pass through here. No component ever displays a raw error string.**

```typescript
import { ApiError } from './api'
import { KIRA_ERROR_MESSAGES } from './constants'

export type KiraErrorType =
  | 'network'
  | 'rate_limit'
  | 'auth'
  | 'validation'
  | 'server'
  | 'unknown'

export interface KiraError {
  type: KiraErrorType
  userMessage: string  // What Kira says in the UI — never a raw error
  retryable: boolean
}

export function mapError(err: unknown): KiraError {
  if (err instanceof ApiError) {
    if (err.status === 401 || err.status === 403) {
      return { type: 'auth', userMessage: KIRA_ERROR_MESSAGES.AUTH, retryable: false }
    }
    if (err.status === 422) {
      return { type: 'validation', userMessage: KIRA_ERROR_MESSAGES.VALIDATION, retryable: false }
    }
    if (err.status === 429) {
      return { type: 'rate_limit', userMessage: KIRA_ERROR_MESSAGES.RATE_LIMIT, retryable: true }
    }
    if (err.status >= 500) {
      return { type: 'server', userMessage: KIRA_ERROR_MESSAGES.SERVER, retryable: true }
    }
  }
  if (err instanceof TypeError && err.message === 'Failed to fetch') {
    return { type: 'network', userMessage: KIRA_ERROR_MESSAGES.NETWORK, retryable: true }
  }
  return { type: 'unknown', userMessage: KIRA_ERROR_MESSAGES.UNKNOWN, retryable: true }
}

// ── These strings must NEVER reach the UI ─────────────────────────────────
export const FORBIDDEN_ERROR_STRINGS = [
  'jwt',
  'token',
  'supabase',
  'fly.io',
  'postgres',
  'gpt-4',
  'openai',
  'langmem',
  'langraph',
  'agent',
  'node_modules',
  'stack trace',
]

export function sanitizeError(message: string): string {
  const lower = message.toLowerCase()
  if (FORBIDDEN_ERROR_STRINGS.some(s => lower.includes(s))) {
    return KIRA_ERROR_MESSAGES.UNKNOWN
  }
  return message
}
```

---

### `components/ui/Button.tsx`

```typescript
'use client'

import { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'ghost' | 'kira' | 'danger' | 'paid' | 'waitlist'
type Size    = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
}

const variantStyles: Record<Variant, string> = {
  primary:  'bg-kira border border-kira text-white font-semibold hover:opacity-90',
  ghost:    'bg-transparent border border-border-strong text-text-default hover:border-border-bright',
  kira:     'bg-[var(--kira-dim)] border border-kira text-kira hover:bg-[var(--kira-glow-strong)]',
  danger:   'bg-[var(--intent-dim)] border border-intent text-intent hover:opacity-90',
  paid:     'bg-[var(--engineer-dim)] border border-engineer text-engineer font-mono text-[10px] tracking-wider',
  waitlist: 'bg-[var(--coming-dim)] border border-[var(--coming)] text-[var(--coming)] font-semibold hover:opacity-90',
}

const sizeStyles: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs rounded-md',
  md: 'px-4 py-2 text-sm rounded-lg',
  lg: 'px-6 py-3 text-sm rounded-xl',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center gap-2
        font-display cursor-pointer
        transition-all duration-150
        disabled:opacity-40 disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
    >
      {loading ? (
        <span className="inline-block w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : null}
      {children}
    </button>
  )
}
```

---

### `components/ui/Input.tsx`

```typescript
'use client'

import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="font-mono text-[10px] tracking-widest text-text-dim uppercase">
          {label}
        </label>
      )}
      <input
        ref={ref}
        {...props}
        className={`
          w-full px-3.5 py-2.5
          bg-layer2 border rounded-lg
          text-sm font-display text-text-default
          placeholder:text-text-dim
          outline-none
          transition-colors duration-150
          ${error
            ? 'border-intent focus:border-intent'
            : 'border-border-strong focus:border-kira'
          }
          disabled:opacity-40
          ${className}
        `}
      />
      {error && (
        <span className="font-mono text-[10px] text-intent">{error}</span>
      )}
    </div>
  )
)
Input.displayName = 'Input'

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className = '', ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="font-mono text-[10px] tracking-widest text-text-dim uppercase">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        {...props}
        className={`
          w-full px-3.5 py-2.5
          bg-layer2 border rounded-lg
          text-sm font-display text-text-default
          placeholder:text-text-dim
          outline-none resize-none
          transition-colors duration-150
          ${error
            ? 'border-intent focus:border-intent'
            : 'border-border-strong focus:border-kira'
          }
          disabled:opacity-40
          ${className}
        `}
      />
      {error && (
        <span className="font-mono text-[10px] text-intent">{error}</span>
      )}
    </div>
  )
)
Textarea.displayName = 'Textarea'
```

---

### `components/ui/Chip.tsx`

```typescript
'use client'

type ChipVariant = 'kira' | 'intent' | 'context' | 'domain' | 'engineer' | 'memory' | 'mcp' | 'teal' | 'success' | 'done'

interface ChipProps {
  variant: ChipVariant
  label: string
  active?: boolean   // true = dot pulses
  skipped?: boolean  // true = 40% opacity
}

const styles: Record<ChipVariant, { bg: string; border: string; text: string; dot: string }> = {
  kira:     { bg: 'var(--kira-dim)',     border: 'var(--kira)',     text: 'var(--kira)',     dot: 'var(--kira)' },
  intent:   { bg: 'var(--intent-dim)',   border: 'var(--intent)',   text: 'var(--intent)',   dot: 'var(--intent)' },
  context:  { bg: 'var(--context-dim)',  border: 'var(--context)',  text: 'var(--context)',  dot: 'var(--context)' },
  domain:   { bg: 'var(--domain-dim)',   border: 'var(--domain)',   text: 'var(--domain)',   dot: 'var(--domain)' },
  engineer: { bg: 'var(--engineer-dim)', border: 'var(--engineer)', text: 'var(--engineer)', dot: 'var(--engineer)' },
  memory:   { bg: 'var(--memory-dim)',   border: 'var(--memory)',   text: 'var(--memory)',   dot: 'var(--memory)' },
  mcp:      { bg: 'var(--mcp-dim)',      border: 'var(--mcp)',      text: 'var(--mcp)',      dot: 'var(--mcp)' },
  teal:     { bg: 'var(--teal-dim)',     border: 'var(--teal)',     text: 'var(--teal)',     dot: 'var(--teal)' },
  success:  { bg: 'var(--success-dim)',  border: 'var(--success)',  text: 'var(--success)',  dot: 'var(--success)' },
  done:     { bg: 'rgba(34,197,94,0.08)',border: 'var(--success)',  text: 'var(--success)',  dot: 'var(--success)' },
}

export function Chip({ variant, label, active = false, skipped = false }: ChipProps) {
  const s = styles[variant]
  return (
    <div
      style={{ background: s.bg, borderColor: s.border, color: s.text, opacity: skipped ? 0.4 : 1 }}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border font-mono text-[10px] font-medium tracking-wide"
    >
      <span
        style={{
          background: s.dot,
          animation: active ? 'chip-pulse 1.2s infinite' : 'none',
        }}
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
      />
      {label}
    </div>
  )
}
```

---

### `components/ui/index.ts`

```typescript
export { Button } from './Button'
export { Input, Textarea } from './Input'
export { Chip } from './Chip'
```

---

## 4. HOOK CONTRACTS

No hooks in Plan 1. Plan 1 is infrastructure only.

---

## 5. API INTEGRATION

No direct API calls in Plan 1. `lib/api.ts` defines the contracts. Plans 2-4 use them.

---

## 6. DESIGN RULES

- **Fonts load from Google Fonts** in `globals.css` `@import`. Do not use `next/font` — it conflicts with the CSS variable system.
- **Color semantic discipline**: Each color token has one job. See constants. Never use `--intent` for a success state. Never use `--kira` for decorative purposes.
- **Text hierarchy**: `--text-bright` (#f8fafc) for output text only. `--text-default` for body. `--text-dim` for labels and metadata.
- **Border discipline**: `--border-default` for cards. `--border-strong` for inputs. `--border-bright` for active/focused. Never skip a level.
- **Font mono usage**: `font-mono` for — quality scores, chips, labels, latency displays, code/output, monospaced data. Everything else: `font-display`.
- **No inline styles except CSS variables** — e.g. `style={{ color: 'var(--kira)' }}` is acceptable when Tailwind class doesn't exist. Never `style={{ color: '#6366f1' }}`.

---

## 7. VERIFICATION CHECKLIST

Before Plan 2 starts, verify ALL of the following:

```bash
# Run from promptforge-web/
bash verify.sh
# Expected: ALL CHECKS PASSED ✅

# TypeScript specifically
npx tsc --noEmit
# Expected: 0 errors, 0 warnings
```

**Manual checks:**
- [ ] `import { Button } from '@/components/ui'` resolves in a test file
- [ ] `import { apiChat } from '@/lib/api'` resolves
- [ ] `import { parseStream } from '@/lib/stream'` resolves
- [ ] `import { mapError } from '@/lib/errors'` resolves
- [ ] `import { ROUTES, LIMITS } from '@/lib/constants'` resolves
- [ ] `import { getSupabaseClient } from '@/lib/supabase'` resolves
- [ ] `import { logger } from '@/lib/logger'` resolves
- [ ] `import type { ChatMessage, ProcessingStatus } from '@/lib/types'` resolves
- [ ] `import { MOCK_CHAT_RESULT } from '@/lib/mocks'` resolves
- [ ] `import { ENV, validateEnv } from '@/lib/env'` resolves
- [ ] No `any` types in `lib/api.ts` or `lib/stream.ts`
- [ ] `DEMO_MAX_USES` is 3 in constants
- [ ] `KIRA_ERROR_MESSAGES` has no raw technical strings (no "JWT", no "Supabase")
- [ ] Button renders all 6 variants without TypeScript error
- [ ] Chip renders all 10 variants without TypeScript error
- [ ] `NEXT_PUBLIC_USE_MOCKS=true` in `.env.local` → `ENV.USE_MOCKS` is `true`
- [ ] `NEXT_PUBLIC_USE_MOCKS=false` in `.env.local` → `ENV.USE_MOCKS` is `false`

---

## 8. HANDOFF TO PLAN 2

Plan 2 depends on these exact exports:

```typescript
// From lib/types.ts  ← NEW
import type { ChatMessage, ProcessingStatus, PersonaDotState } from '@/lib/types'

// From lib/mocks.ts  ← NEW
import { MOCK_CHAT_RESULT } from '@/lib/mocks'

// From lib/env.ts  ← NEW
import { ENV } from '@/lib/env'

// From lib/constants.ts
import { ROUTES, LIMITS, ONBOARDING_QUESTIONS } from '@/lib/constants'

// From lib/api.ts
import { apiDemoChat, ApiError } from '@/lib/api'
import type { ChatResult, DiffItem, QualityScore } from '@/lib/api'

// From lib/errors.ts
import { mapError } from '@/lib/errors'

// From components/ui
import { Button } from '@/components/ui'

// From styles/globals.css (imported in layout.tsx)
// .reveal, .reveal-delay-*, .gradient-text classes available globally
```

**State Plan 2 inherits:**
- No authenticated user needed
- No Supabase session needed
- `LIMITS.DEMO_MAX_USES` = 3
- `LIMITS.DEMO_STORAGE_KEY` = `'pf_demo_uses'`
- `ENV.USE_MOCKS` controls mock mode throughout the entire app

---

*Plan 1 complete. Verify checklist passes before starting Plan 2.*
# PROMPTFORGE FRONTEND — AGENT RULES FILE
### Read this entire file before writing a single line of code.
### This is not optional. Every error listed here has caused real broken builds.

---

## SECTION 0 — WHAT THIS PROJECT IS

PromptForge is a multi-agent AI prompt engineering system. The backend is **already built and deployed** on Railway or Koyeb (Docker container). You are building only the frontend (`promptforge-web/`).

**The product:** User types a vague prompt → 4-agent backend swarm runs → Kira (the AI orchestrator) engineers a better prompt → user sees the improved version with diff, quality scores, and Kira's message.

**The moat:** Kira builds a profile of each user. More sessions = richer profile = smarter responses. Users can't take this profile to another tool. That's the entire business logic.

**Your job:** Build the UI that makes this pipeline visible, fast-feeling, and trustworthy — without ever leaking internal implementation details to the user.

---

## SECTION 1 — PROJECT STRUCTURE. DO NOT DEVIATE.

```
monorepo root/
├── promptforge/          ← BACKEND. NEVER TOUCH THIS DIRECTORY.
└── promptforge-web/      ← FRONTEND. This is where you work.
    ├── app/
    │   ├── layout.tsx                  ← Root layout, imports globals.css
    │   ├── (marketing)/                ← SERVER COMPONENTS ONLY
    │   │   └── page.tsx                ← Landing page
    │   ├── (auth)/                     ← Login, Signup
    │   │   ├── layout.tsx
    │   │   ├── login/page.tsx
    │   │   └── signup/page.tsx
    │   ├── auth/callback/route.ts      ← OAuth callback handler
    │   ├── onboarding/page.tsx         ← 3-question onboarding
    │   └── app/                        ← Auth-gated. All chat/history/profile.
    │       ├── layout.tsx
    │       ├── page.tsx                ← Chat
    │       ├── history/page.tsx
    │       └── profile/page.tsx
    ├── features/                       ← VERTICAL SLICES. One folder per product area.
    │   ├── landing/                    ← components/ + hooks/
    │   ├── onboarding/                 ← components/ + hooks/ + types.ts
    │   ├── chat/                       ← components/ + hooks/ + types.ts
    │   ├── history/                    ← components/ + hooks/
    │   └── profile/                    ← components/ + hooks/
    ├── lib/                            ← SHARED INFRASTRUCTURE ONLY
    │   ├── api.ts                      ← ALL backend calls. THE ONLY PLACE.
    │   ├── stream.ts                   ← SSE parser. THE ONLY PLACE.
    │   ├── supabase.ts                 ← Supabase client singleton.
    │   ├── auth.ts                     ← Auth helpers.
    │   ├── errors.ts                   ← Error mapping. THE ONLY PLACE.
    │   └── constants.ts                ← Routes, limits, messages.
    ├── components/ui/                  ← TRULY SHARED primitives only.
    │   ├── Button.tsx
    │   ├── Input.tsx
    │   ├── Chip.tsx
    │   └── index.ts
    ├── styles/
    │   └── globals.css                 ← ALL design tokens. Source of truth.
    └── tailwind.config.ts
```

**FILE CREATION RULES — NON-NEGOTIABLE:**
1. `app/(marketing)/` → server components only. No `'use client'`. Ever.
2. `features/` files → always start with `'use client'`.
3. `lib/` files → no `'use client'`. Pure TypeScript.
4. `components/ui/` → `'use client'` since they contain interaction.
5. No file outside `lib/api.ts` ever calls `fetch()` directly.
6. No file outside `lib/stream.ts` ever parses SSE.
7. No file outside `lib/errors.ts` ever formats an error for the UI.

---

## SECTION 2 — THE BACKEND CONTRACT

You are connecting to a live FastAPI backend. These are the exact specs. Do not guess.

### Base URL
```
NEXT_PUBLIC_API_URL=https://<your-backend>.up.railway.app
```
All requests go to this URL. It's in `.env.local`. Access via `process.env.NEXT_PUBLIC_API_URL`.

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | None | Liveness check |
| POST | /chat | JWT | Conversational, with memory, full JSON result |
| POST | /chat/stream | JWT | SSE version of /chat. USE THIS for the app. |
| POST | /refine | JWT | Single-shot, no memory |
| POST | /transcribe | JWT | Audio blob → Whisper → transcript |
| GET | /history | JWT | User's prompt history |
| GET | /conversation | JWT | Full chat history for a session |
| POST | /user/profile | JWT | Save onboarding profile |

**AUTH RULE:** Every request except `/health` requires:
```
Authorization: Bearer <supabase_jwt>
```
Get the JWT from `getAccessToken()` in `lib/supabase.ts`. Never hardcode it. Never store it in localStorage. Supabase Auth JS manages it.

### Chat Request Shape
```typescript
{
  message: string          // 5-2000 chars (enforced by backend Pydantic)
  session_id: string       // UUID. Per-tab. From sessionStorage.
  input_modality?: 'text' | 'voice' | 'image' | 'file'
  file_base64?: string     // for image/file modalities
  file_type?: string       // mime type
}
```

### Chat Response Shape (from /chat and SSE result event)
```typescript
{
  improved_prompt: string
  diff: Array<{ type: 'add' | 'remove' | 'keep', text: string }>
  quality_score: { specificity: number, clarity: number, actionability: number }  // 1-5
  kira_message: string
  memories_applied: number
  latency_ms: number
  agents_run: string[]
}
```

### SSE Event Stream (from /chat/stream)
Events come in this order. Each line is `data: <json>`.

```
data: {"type": "status", "data": {"message": "Analyzing intent..."}}
data: {"type": "kira_message", "data": {"message": "On it...", "complete": false}}
data: {"type": "kira_message", "data": {"message": "On it. Here's your engineered prompt ↓", "complete": true}}
data: {"type": "result", "data": { ...ChatResult... }}
data: {"type": "done", "data": {}}
```

On error:
```
data: {"type": "error", "data": {"message": "...", "code": "..."}}
```

**SSE PARSING RULE:** Parse line by line. Split on `\n`. Only process lines starting with `data: `. Strip the `data: ` prefix. Parse remaining as JSON. Skip `[DONE]` and empty lines. Never assume event ordering is guaranteed.

### Session ID Rules
- Generate with `crypto.randomUUID()` on first message
- Store in `sessionStorage` (not localStorage — new session per browser tab)
- Same session_id must be sent on every message in the same tab
- Backend verifies ownership via RLS: `auth.uid() = user_id`
- NEVER expose session_id in the UI

---

## SECTION 3 — NEXT.JS ERRORS THIS PROJECT WILL HIT. READ ALL OF THEM.

These are not hypothetical. These are the exact errors that occur when building a Next.js 14 App Router project with this architecture.

---

### ERROR 1: "You're importing a component that needs useState/useEffect. It only works in Client Components."

**When it happens:** You add any hook, event handler, or browser API to a file in `app/(marketing)/`.

**Why:** `app/(marketing)/` is the marketing routes group. Next.js App Router defaults all files in `app/` to Server Components. Server Components cannot use React state, effects, or browser APIs.

**The fix:**
- `app/(marketing)/page.tsx` stays a server component. It imports section components.
- Section components that need interactivity (`LiveDemoWidget`, `KiraVoiceSection`, `LandingNav`) go in `features/landing/components/` and start with `'use client'`.
- Server page imports client components — that's fine. Client components cannot import server components.

**Rule:** If a file is in `app/(marketing)/`, it has zero `'use client'`, zero hooks, zero `useState`, zero event handlers. Period.

---

### ERROR 2: "Hydration failed because the initial UI does not match what was rendered on the server."

**When it happens:** You render different content on server vs client. Most common causes in this project:

1. **Reading `localStorage` or `sessionStorage` during render:**
   ```typescript
   // WRONG — crashes on server, value undefined, causes mismatch
   const uses = localStorage.getItem('pf_demo_uses')
   
   // RIGHT — read in useEffect only
   const [uses, setUses] = useState(0)
   useEffect(() => {
     setUses(parseInt(localStorage.getItem('pf_demo_uses') ?? '0'))
   }, [])
   ```

2. **Using `Date.now()` or `Math.random()` in render:**
   ```typescript
   // WRONG
   const id = Math.random().toString()
   
   // RIGHT — use useId() or generate in useEffect
   const id = useId()
   ```

3. **Conditional rendering based on `window` existence:**
   ```typescript
   // WRONG
   if (window.innerWidth > 768) return <Desktop />
   
   // RIGHT — use CSS, not JS, for responsive layout
   ```

**Rule:** Never access `localStorage`, `sessionStorage`, `window`, `document`, or `navigator` during the render phase. Only in `useEffect`.

---

### ERROR 3: "useEffect runs twice in development" (React StrictMode)

**When it happens:** Every single `useEffect` in development. Next.js 14 runs StrictMode by default. Effects mount, unmount, and mount again.

**Why this destroys SSE:** If you open an SSE connection in `useEffect` without cleanup, you get TWO connections. Two connections = duplicate messages = broken UI state.

**The fix — use this exact pattern for every SSE connection:**
```typescript
useEffect(() => {
  const controller = new AbortController()
  
  parseStream(url, body, token, callbacks, controller.signal)
  
  return () => {
    controller.abort()  // cleanup kills the connection on unmount
  }
}, [])  // dependency array based on what triggers a new stream
```

**DO NOT** remove StrictMode from `next.config.js` to fix this. That hides the bug in development and it will explode in production.

**Same pattern for any `fetch()` in `useEffect`:**
```typescript
useEffect(() => {
  const controller = new AbortController()
  fetch(url, { signal: controller.signal })
    .then(...)
    .catch(err => {
      if (err.name === 'AbortError') return  // ignore abort errors
      // handle real errors
    })
  return () => controller.abort()
}, [])
```

---

### ERROR 4: "Cannot read properties of undefined (reading 'xxx')" on SSE result

**When it happens:** SSE events arrive out of order, or a `result` event arrives before the component has set up its state properly.

**Why:** SSE is a stream. Events can be delayed, batched, or arrive in unexpected order depending on network conditions.

**The fix:**
```typescript
case 'result':
  // WRONG — assumes data shape is correct
  setResult(event.data)
  
  // RIGHT — validate before using
  const result = event.data as ChatResult
  if (!result?.improved_prompt) return  // guard against malformed events
  setResult(result)
```

**Rule:** Every SSE event handler must guard against undefined/malformed data. Treat all SSE data as `unknown` until validated.

---

### ERROR 5: "Module not found: Can't resolve '@/lib/api'" or similar

**When it happens:** Missing `tsconfig.json` path alias, or running `tsc` before the path is configured.

**The fix — `tsconfig.json` must have:**
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

`create-next-app` adds this automatically. If you see this error, check `tsconfig.json` first.

---

### ERROR 6: Tailwind classes not applying (purge/content issue)

**When it happens:** You add Tailwind classes in a file that's not in the `content` array of `tailwind.config.ts`.

**Symptom:** Classes work in `app/` but not in `features/`.

**The fix — `tailwind.config.ts` content must include:**
```typescript
content: [
  './app/**/*.{js,ts,jsx,tsx,mdx}',
  './features/**/*.{js,ts,jsx,tsx,mdx}',
  './components/**/*.{js,ts,jsx,tsx,mdx}',
]
```

**CSS variable classes not working:** Tailwind doesn't know about CSS variable values like `bg-[var(--kira-dim)]`. Use the bracket notation `bg-[var(--kira-dim)]` — this is JIT syntax and works. Do not try to make Tailwind generate these — they're arbitrary values.

---

### ERROR 7: Supabase `getSession()` returns null on first load

**When it happens:** Component mounts, calls `getSession()`, gets null, redirects to login — even though the user IS logged in.

**Why:** Supabase Auth JS loads the session asynchronously from storage. On first render, the session hasn't loaded yet.

**The fix:**
```typescript
// WRONG — session hasn't loaded yet
const session = await getSession()
if (!session) router.push('/login')

// RIGHT — wait for onAuthStateChange before redirecting
const supabase = getSupabaseClient()
const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_OUT') router.push('/login')
  if (event === 'SIGNED_IN' && session) setSession(session)
})

// Or use the loading state pattern:
const [loading, setLoading] = useState(true)
useEffect(() => {
  getSession().then(session => {
    if (!session) router.push('/login')
    setLoading(false)
  })
}, [])
if (loading) return <KiraLoadingState />  // never return null — causes layout shift
```

---

### ERROR 8: Google OAuth redirect goes to wrong URL

**When it happens:** Google OAuth callback lands on a 404 or the wrong page.

**Why:** Supabase needs to know where to redirect after Google auth. The callback URL must be registered in both Supabase AND Google Cloud Console.

**The fix:**
1. In `lib/auth.ts`, the OAuth call must specify redirectTo:
   ```typescript
   await supabase.auth.signInWithOAuth({
     provider: 'google',
     options: {
       redirectTo: `${window.location.origin}/auth/callback`
     }
   })
   ```
2. `app/auth/callback/route.ts` must exist and exchange the code:
   ```typescript
   // GET /auth/callback
   const { searchParams } = new URL(request.url)
   const code = searchParams.get('code')
   if (code) {
     await supabase.auth.exchangeCodeForSession(code)
   }
   return NextResponse.redirect(new URL('/onboarding', request.url))
   ```
3. In Supabase dashboard: Authentication → URL Configuration → add `http://localhost:3000/auth/callback`
4. In Google Cloud Console: OAuth → Authorized redirect URIs → add `https://<supabase-project>.supabase.co/auth/v1/callback`

---

### ERROR 9: "CORS error" when calling backend

**When it happens:** Browser blocks requests to `https://<your-backend>.up.railway.app` from `http://localhost:3000`.

**Why:** The backend has CORS locked to the production frontend domain. In development you're on localhost.

**The fix:**
- In `promptforge/api.py`, the CORS origins list must include `http://localhost:3000` for development:
  ```python
  # This is a BACKEND change — add to CLAUDE.md's allowed origins
  allow_origins=["https://your-vercel-domain.vercel.app", "http://localhost:3000"]
  ```
- This is the ONE time you need to touch the backend for frontend development. Log it and do it once.
- In production, Vercel domain replaces localhost. Use environment variables.

---

### ERROR 10: "window is not defined" during build

**When it happens:** You use `window`, `document`, `localStorage`, or `navigator` outside of a `useEffect` or event handler — even in a `'use client'` file.

**Why:** Next.js pre-renders all pages on the server during `npm run build`. Even `'use client'` components are pre-rendered. Browser APIs don't exist on the server.

**The fix:**
```typescript
// WRONG — crashes at build time
const stored = localStorage.getItem('key')

// RIGHT
useEffect(() => {
  const stored = localStorage.getItem('key')
}, [])

// WRONG — crashes at build time
if (window.innerWidth > 768) ...

// RIGHT — use typeof guard
if (typeof window !== 'undefined' && window.innerWidth > 768) ...
```

**In hooks:** Always guard browser APIs:
```typescript
export function useScrollReveal() {
  useEffect(() => {
    if (typeof window === 'undefined') return
    // safe to use browser APIs here
  }, [])
}
```

---

### ERROR 11: TypeScript error "Property does not exist on type 'never'"

**When it happens:** SSE event data typed as `unknown` and you access properties without narrowing.

**The fix:**
```typescript
// WRONG
const message = event.data.message  // error: 'message' does not exist on 'unknown'

// RIGHT — cast after type check
if (event.type === 'kira_message') {
  const data = event.data as { message: string; complete: boolean }
  setKiraMessage(data.message)
}
```

---

### ERROR 12: Input clears on error (breaks user experience)

**When it happens:** `useKiraStream` clears the input value after a failed API call.

**Why this is wrong:** If Kira's backend fails, the user's prompt disappears. They have to retype everything. This is infuriating.

**The rule:** Input is ONLY cleared on successful submission. Never on error. In `useInputBar`:
```typescript
const handleSubmit = () => {
  if (!input.trim() || input.length < LIMITS.PROMPT_MIN) return
  onSubmit(input, attachment)
  setInput('')           // clear AFTER calling onSubmit (optimistic)
  setAttachment(null)
}

// In useKiraStream, if the API call fails:
// DO NOT call setInput('') — the input is owned by useInputBar
// The error is added to messages[] — input stays as-is
```

---

### ERROR 13: Infinite re-render loop in useEffect

**When it happens:** You put an object or array in the dependency array that's recreated on every render.

```typescript
// WRONG — creates new object on every render, triggers infinite loop
useEffect(() => {
  fetchData(options)
}, [options])  // 'options' is { page: 1, limit: 10 } created inline

// RIGHT — use primitive values or useMemo
useEffect(() => {
  fetchData({ page, limit })
}, [page, limit])  // primitives are stable
```

**Common in this project:** Passing the entire `profile` object as a dependency. Use `profile?.id` or specific fields instead.

---

### ERROR 14: Supabase RLS "row-level security violation" (403 error)

**When it happens:** Frontend sends a valid JWT but Supabase rejects the query.

**Why:** Every Supabase table has RLS policies: `auth.uid() = user_id`. If `user_id` in the row doesn't match the JWT's `auth.uid()`, Supabase returns 403.

**What this means for frontend:**
- You cannot query other users' data — that's intentional
- You cannot insert rows without setting `user_id` to the authenticated user's ID
- The JWT in the `Authorization` header tells the backend who the user is
- Frontend never sends `user_id` explicitly — it's derived from the JWT server-side

**If you see 403:** The JWT is either expired, wrong, or the row's `user_id` doesn't match. Check `getAccessToken()` returns a fresh token.

---

## SECTION 4 — SECURITY RULES. NEVER VIOLATE THESE.

These are not design preferences. Leaking this information destroys user trust and potentially the product.

### NEVER RENDER IN THE UI:
```
Agent names:       "intent", "context", "domain", "prompt_engineer"
Model names:       "GPT-4o", "GPT-4o-mini", "gpt-4o", "gpt-4o-mini"
Internal routes:   Backend URL (Railway/Koyeb), Supabase project ID (cckznjkzsfypssgecyya)
Session IDs:       UUIDs, session tokens
Error internals:   Stack traces, Pydantic errors, JWT errors, Postgres errors
LangGraph:         "LangGraph", "LangMem", "StateGraph", "node"
Keys:              Any API key, any JWT, any hash
```

### CHIP LABELS — USE THESE EXACT STRINGS:
These are the only labels that appear in the status chips UI. They describe what's happening without leaking implementation:

```
Kira chip:      "Reading context"
Intent chip:    "Analyzing intent"
Context chip:   "Context"     (skipped = show as skipped, label unchanged)
Domain chip:    "Domain"      (skipped = show as skipped)
Engineer chip:  "Crafting prompt"
Memory chip:    "N memories applied"   (N = memories_applied from API result)
Latency chip:   "3.4s"                 (latency_ms / 1000, one decimal)
Done state:     all chips show as complete
```

### ERROR MESSAGES — USE ONLY THESE:
All errors pass through `lib/errors.ts`. These are the only strings users ever see:
```
Network fail:   "Something broke on my end. Your prompt is safe — try again."
Rate limit:     "You're moving fast. Give me 30 seconds to catch up."
Auth expired:   "Session expired. Sign back in and we'll pick up where we left off."
Too short:      "That's too short for me to work with. Give me a bit more context."
Server error:   "Backend's having a moment. Your prompt is safe — try again."
Unknown:        "Something went wrong. Your prompt is safe — try again."
```

Kira owns all errors. Every error message is written as if Kira is speaking. Never display HTTP status codes, error class names, or stack traces.

---

## SECTION 5 — DESIGN SYSTEM. USE TOKENS, NOT HEX CODES.

Every color in the UI comes from a CSS variable. Never hardcode a hex value in a component.

### Color tokens and their SINGLE job:

```css
--kira:      #6366f1   → Kira's avatar, Kira's messages, focused input borders, primary CTAs
--intent:    #f43f5e   → Intent chip ONLY. Error borders. Diff removals.
--context:   #10b981   → Context chip ONLY. Diff additions. Positive stats.
--domain:    #f59e0b   → Domain chip ONLY. Warm persona dot. Rate limit UI.
--engineer:  #8b5cf6   → Engineer chip ONLY. Push Further button (Phase 5).
--profile:   #38bdf8   → Profile data display ONLY. Stats. Sparklines.
--memory:    #ec4899   → Memory badges ONLY. "2 memories applied."
--mcp:       #fb923c   → MCP section ONLY. Token generation. Trust levels.
--teal:      #14b8a6   → Latency displays ONLY. "3.4s" values.
--success:   #22c55e   → Success states. Tuned persona dot (session 30+).
--domain:    #f59e0b   → Coming soon badges. Waitlist signals.
```

**Persona dot states:**
```css
--dot-cold:  #475569   → Sessions 0-9:  grey, no glow
--dot-warm:  #f59e0b   → Sessions 10-29: amber, glow 6px domain
--dot-tuned: #22c55e   → Sessions 30+:  green, glow shadow-tuned
```

**Output text rule:** The engineered prompt (the product's output) uses `--output-text: #f8fafc`. This is the brightest text on screen. It signals "this is what you came here for."

### Typography — two fonts, strict usage:

```
JetBrains Mono → quality scores, chips, labels, latency, metadata, eyebrows, monospace data
Satoshi        → everything else: Kira messages, body text, headings, buttons
```

In Tailwind: `font-mono` = JetBrains Mono, `font-display` = Satoshi.

**Never use system fonts. Never use Inter. Never use Arial.**

---

## SECTION 6 — PLAN EXECUTION CONTRACT

There are 4 plans. Each is a complete, independently verifiable unit. **Do not start Plan N+1 until Plan N's verification checklist passes.**

### Plan 1 — Foundation + Design System
**What you build:** `styles/globals.css`, `lib/*`, `components/ui/*`, `tailwind.config.ts`
**What you must NOT build:** any pages, any features, any routes
**Verification gate:** `npx tsc --noEmit` returns 0 errors. All imports resolve. No `any` types in `lib/api.ts` or `lib/stream.ts`.
**Plans that depend on this:** 2, 3, 4 (everything)

### Plan 2 — Landing Page
**What you build:** `app/(marketing)/`, `features/landing/`
**What you must NOT build:** auth, app routes, onboarding
**Verification gate:** `npm run build` passes. Live demo works 3x, then shows gate. Fallback result shows when API is unreachable. Pro card shows "COMING SOON". No agent names visible in rendered HTML.
**Plans that depend on this:** standalone (can ship before Plans 3+4)

### Plan 3 — Auth + Onboarding
**What you build:** `app/(auth)/`, `app/onboarding/`, `features/onboarding/`, `lib/auth.ts`
**What you must NOT build:** any chat UI, any app routes
**Verification gate:** Test user exists in Supabase `user_profiles` table after completing the flow. Unauthenticated access to `/onboarding` redirects to `/login`. Google OAuth button functional.
**Plans that depend on this:** Plan 4 (needs real test user with JWT)

### Plan 4 — Core App
**What you build:** `app/app/`, `features/chat/`, `features/history/`, `features/profile/`
**What you must NOT build:** Push Further feature (Phase 5), Chrome Extension (Phase 5)
**Verification gate:** Full chat flow works end-to-end with real backend. Quality bars animate. Diff toggle works. 0 agent/model names in rendered UI. All error states show Kira's message. Mobile responsive.

---

## SECTION 7 — LIVE DEMO GATE CONTRACT

The landing page has a live demo widget. Anonymous users get 3 uses, then see a signup gate.

### Implementation contract:
```typescript
// Storage key: 'pf_demo_uses' in localStorage
// Max uses: LIMITS.DEMO_MAX_USES = 3

// On each successful demo result:
localStorage.setItem('pf_demo_uses', String(uses + 1))

// Gate condition:
const isGated = uses >= LIMITS.DEMO_MAX_USES

// Gate UI must show:
// 1. Kira avatar
// 2. "You've seen what I can do."
// 3. "Sign up to keep going — it's free."
// 4. Button: "Create free account →" → ROUTES.SIGNUP
// 5. Button: "Sign in" → ROUTES.LOGIN
```

### Demo backend rules:
- Demo uses a demo account JWT pre-configured on the backend
- Demo account is rate-limited to 50 req/hour server-side (separate from per-user limits)
- If demo backend returns 429: show FALLBACK_RESULT (not an error state)
- If demo backend is unreachable: show FALLBACK_RESULT (not an error state)
- FALLBACK_RESULT is hardcoded in `LiveDemoWidget.tsx` — makes demo resilient to backend downtime

### What demo must NOT show:
- Push Further button
- "N memories applied" badge (demo has 0 memories)
- Pro features
- Refine button (leads to signup instead)

---

## SECTION 8 — PRICING SECTION CONTRACT

This is the current state of monetization. Do not change it.

```
FREE tier:
  - Everything is free. Unlimited. No hidden limits.
  - Button: "Start free" → ROUTES.SIGNUP (instant access, no waitlist)
  - Note: "No credit card. Genuinely useful."

PRO tier (coming soon):
  - Not launched yet. Waitlist only.
  - Corner badge: "COMING SOON" (amber color: --coming)
  - Price shown: $20/month (dimmed, not active)
  - Button: "Join Pro waitlist →" (amber/waitlist variant)
  - Small text below button: "Free forever until Pro launches."
  - Waitlist URL: placeholder "#waitlist" until Tally/Typeform URL is provided

PRO features to list:
  • Everything in Free
  • Prompt history library
  • MCP (Cursor / Claude Desktop)
  • Push Further variants ✦
  • Full profile depth
  • Priority queue
```

**Critical:** Do not imply free features are limited. They aren't. The free tier is genuinely unlimited.

---

## SECTION 9 — SSE STREAMING CONTRACT

The `/chat/stream` endpoint is the core of the product experience. Get this right.

### Streaming UX sequence (in order):
```
1. User submits message
2. Input disabled immediately
3. StatusChips appear: [Kira chip: active]
4. kira_message arrives (streaming):
   - Kira message component appears instantly
   - Text streams in character by character (or word by word)
   - Blinking cursor "|" visible while streaming
5. kira_message complete=true:
   - Cursor disappears
   - 200ms pause
6. result arrives:
   - StatusChips update to "done" state
   - Memory badge appears if memories_applied > 0
   - Latency chip appears
   - OutputCard slides in (not fades — translate from below)
   - Quality bars animate from 0 to final width
7. done event:
   - Input re-enabled
   - Persona dot checked (update if session count threshold crossed)
```

### What to do with status events:
Status events contain messages like `"Analyzing intent..."`, `"Engineering prompt..."`. Display these in the StatusChips area as plain text below the chips — not as separate UI elements. Replace the previous status message, don't stack them.

### The 200ms gap rule:
After `kira_message` completes and before `OutputCard` appears, wait 200ms. This prevents jarring layout jumps and makes the sequence feel choreographed. Use `setTimeout(200)` triggered by `complete: true`.

---

## SECTION 10 — ONBOARDING CONTRACT

Three questions. One per screen. Seeds the user profile.

```
Question 1: "What do you mostly use AI for?"
  Type: grid (2 columns)
  Options: Writing, Code, Marketing, Research, Product, Other
  Maps to: user_profiles.primary_use

Question 2: "Who do you usually write for?"
  Type: list (single column)
  Options: "Just me / internal teams", "External customers or clients", "Both — depends on the day"
  Maps to: user_profiles.audience

Question 3: "What does AI keep getting wrong for you?"
  Type: chips (multi-select)
  Options: Too generic, Wrong tone, Misses context, Too long, Too formal, Off-brand
  Plus: free text input fallback
  Maps to: user_profiles.ai_frustration (comma-separated) + user_profiles.frustration_detail
```

### Onboarding rules:
- One question per screen (Typeform-style — not a long form)
- Progress: 3 dots at top, current dot glows (shadow-kira)
- Skip button: top-right, always visible, goes directly to `/app` without saving
- Profile save failure is NON-FATAL — still navigate to `/app`, log error silently
- After completing: check if profile exists before showing onboarding again (redirect to /app if already done)
- Kira avatar visible on every onboarding screen

---

## SECTION 11 — SCROLL REVEAL CONTRACT

Landing page only. IntersectionObserver-based. No scroll event listeners.

```typescript
// The complete implementation — do not deviate:
export function useScrollReveal() {
  useEffect(() => {
    if (typeof window === 'undefined') return  // SSR guard

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const elements = document.querySelectorAll<HTMLElement>('.reveal')

    if (prefersReduced) {
      elements.forEach(el => el.classList.add('visible'))
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
            observer.unobserve(entry.target)  // fire once, then stop watching
          }
        })
      },
      { threshold: 0.15 }
    )

    elements.forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])
}
```

Apply to sections:
- Hero: NO reveal (above fold, must be visible immediately)
- LiveDemoWidget: NO reveal (above fold)
- KiraVoice cards: YES, staggered (.reveal-delay-1, -2, -3)
- HowItWorks steps: YES, staggered
- MoatSection card: YES
- PricingSection cards: YES

---

## SECTION 12 — QUICK REFERENCE CHECKLIST

Run through this before submitting any plan:

```
STRUCTURE
[ ] No 'use client' in app/(marketing)/
[ ] All features/ files start with 'use client'
[ ] No fetch() outside lib/api.ts
[ ] No SSE parsing outside lib/stream.ts
[ ] No error formatting outside lib/errors.ts

SECURITY
[ ] No agent names in rendered UI (intent/context/domain/prompt_engineer)
[ ] No model names in rendered UI (GPT-4o/GPT-4o-mini)
[ ] No session IDs in rendered UI
[ ] No raw API errors shown to user
[ ] No backend URL (Railway/Koyeb domain) in rendered content
[ ] No Supabase project ID in rendered content

NEXT.JS CORRECTNESS
[ ] No localStorage/sessionStorage access during render
[ ] No window/document access during render
[ ] All useEffect SSE connections use AbortController
[ ] AbortController cleanup in useEffect return
[ ] Session check shows loading state before redirecting (no flash)

DESIGN
[ ] All colors use CSS variables, no hex codes
[ ] Output text uses --output-text
[ ] Latency uses --teal + font-mono
[ ] Memory badges use --memory
[ ] Agent chips use correct semantic colors

API
[ ] All requests include Authorization: Bearer <jwt>
[ ] session_id comes from sessionStorage (not localStorage, not hardcoded)
[ ] File uploads validated: 2MB docs, 5MB images, no executables
[ ] Input validated: 5-2000 chars before sending

TYPESCRIPT
[ ] npx tsc --noEmit returns 0 errors
[ ] No 'any' types in lib/api.ts or lib/stream.ts
[ ] SSE event data validated before property access
```

---

## SECTION 13 — THINGS THAT ARE EXPLICITLY NOT IN SCOPE

Do not build these. They are Phase 5. They do not belong in Plans 1-4.

- **Push Further button** — `POST /chat/push-further` endpoint doesn't exist yet
- **Chrome Extension** — separate repo, separate plan
- **CLI Tool** — separate repo, separate plan
- **Performance Evaluator** — dropped from spec
- **Background prompt evolution** — dropped from spec
- **MCP token generation UI** — profile page shows the section but token generation is a stub button for now
- **Paying users / Stripe** — Pro tier is waitlist only, no payment processing
- **Dark/light mode toggle** — dark mode only, no toggle

---

---

## SECTION 14 — FRONTEND ERROR LOGGING

### The Problem
Without frontend error logging, production failures are invisible. A user hits a broken state, closes the tab, and you never know it happened. `console.error()` only helps if someone has DevTools open.

### The Strategy — Three Layers

**Layer 1: Console (always present, costs nothing)**
Every caught error gets `console.error()` with context. Even if nothing else is set up, this gives you something to work with when you have DevTools open.

```typescript
// Pattern used everywhere errors are caught:
console.error('[PromptForge]', context, error)
// e.g. console.error('[PromptForge] useKiraStream send()', err)
// e.g. console.error('[PromptForge] profile save failed', err)
```

**Layer 2: `lib/logger.ts` — lightweight wrapper (build in Plan 1)**

```typescript
// lib/logger.ts
// Centralises all frontend error reporting.
// Swap the internals here when you add a real service — components never change.

type LogContext = Record<string, unknown>

export const logger = {
  error(message: string, context?: LogContext, error?: unknown) {
    // Always log to console
    console.error('[PromptForge]', message, context ?? '', error ?? '')

    // In production: send to error service
    // Currently: console only. When you add Sentry, add it here.
    if (process.env.NODE_ENV === 'production') {
      // Future: Sentry.captureException(error, { extra: { message, ...context } })
      // For now: nothing extra — console is enough for beta
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

**Add `lib/logger.ts` to Plan 1's FILES TO CREATE list.**

**Layer 3: React Error Boundary — catches unhandled render errors (build in Plan 4)**

```typescript
// components/ErrorBoundary.tsx
'use client'

import { Component, ReactNode } from 'react'
import { logger } from '@/lib/logger'

interface Props { children: ReactNode; fallback?: ReactNode }
interface State { hasError: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    logger.error('React render error', { componentStack: info.componentStack }, error)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="flex items-center justify-center h-full p-8">
          <div className="text-center">
            <p className="text-text-dim text-sm font-display">
              Something went wrong. Refresh to continue.
            </p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
```

Wrap `<ChatContainer />` in `app/app/page.tsx`:
```typescript
<ErrorBoundary fallback={<div className="p-8 text-text-dim">Reload to continue.</div>}>
  <ChatContainer />
</ErrorBoundary>
```

### Where `logger` Is Used

Every place an error is caught silently, replace `console.error()` with `logger.error()`:

```typescript
// useKiraStream — on stream error
logger.error('useKiraStream stream error', { sessionId }, err)

// useHistory — on fetch error
logger.error('useHistory fetch failed', { userId }, err)

// useProfile — on profile fetch error
logger.error('useProfile fetch failed', {}, err)

// useOnboarding — profile save failure (non-fatal, still navigate)
logger.warn('Profile save failed — navigating anyway', { step: currentStep })

// auth callback — on OAuth error
logger.error('Auth callback error', { code }, err)
```

### What logger Does NOT Do

- Does NOT show errors to users — that is `lib/errors.ts` + Kira's voice
- Does NOT log user prompt content — privacy rule, never log user data
- Does NOT log JWT tokens or session IDs
- Does NOT block execution — always fire-and-forget

### Future: Adding Sentry (when you have real users)

When beta has 50+ users, add Sentry in one place:

```bash
npm install @sentry/nextjs
npx @sentry/wizard@latest -i nextjs
```

Then update `lib/logger.ts` production block only — every component that already calls `logger.error()` gets Sentry automatically with zero changes elsewhere.

### Quick Reference Checklist Addition

Add to Section 12 checklist:
```
LOGGING
[ ] All caught errors use logger.error() not raw console.error()
[ ] No user prompt content in log messages
[ ] No JWT tokens or session IDs in log messages
[ ] ErrorBoundary wraps ChatContainer in app/app/page.tsx
```

---

*This rules file + the 4 Plan files + WORKFLOW.md are the complete specification for the PromptForge frontend.*
*Read this file. Read the relevant Plan file. Build only what the Plan specifies. Verify before moving on.*
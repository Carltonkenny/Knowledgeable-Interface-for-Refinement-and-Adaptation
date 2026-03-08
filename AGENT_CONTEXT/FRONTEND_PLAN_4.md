# FRONTEND PLAN 4 — Core App
### PromptForge v2.0 · app/app/ · features/chat/ · features/history/ · features/profile/
---

## 1. CONTEXT

### What's already built (from Plans 1, 2, 3)
- Design tokens, all `lib/*`, `components/ui/*` (Plan 1)
- Full landing page (Plan 2)
- Auth pages, onboarding, verified test user with seeded profile (Plan 3)
- `apiChat()`, `apiHistory()`, `apiTranscribe()`, `parseStream()`, `mapError()` all ready

### What this plan builds
The actual product: everything behind `/app`. Chat interface with SSE streaming, the Kira message, output card with diff and quality scores, history page, and profile page.

### What this plan must NOT touch
- `promptforge/` backend directory
- `lib/*`, `components/ui/*`, `styles/globals.css` — read only
- `features/landing/`, `features/onboarding/` — read only
- `app/(auth)/`, `app/(marketing)/` — read only

### Assumptions
- Test user from Plan 3 is available with valid session
- Backend is live on Railway or Koyeb (Docker container)
- `POST /chat/stream` returns SSE with event types: `status`, `kira_message`, `result`, `done`, `error`
- `GET /history` returns `HistoryItem[]` for authenticated user
- Session ID: generate UUID on first visit, store in `sessionStorage` (not localStorage — new session per tab)

---

## 2. FILES TO CREATE

```
promptforge-web/
├── app/
│   └── app/
│       ├── layout.tsx                        ← Auth-gated layout with app nav
│       ├── page.tsx                          ← Chat page
│       ├── history/
│       │   └── page.tsx                      ← History page
│       └── profile/
│           └── page.tsx                      ← Profile page
├── features/
│   ├── chat/
│   │   ├── types.ts                          ← All chat-specific types
│   │   ├── components/
│   │   │   ├── ChatContainer.tsx             ← Root chat component, owns all state
│   │   │   ├── MessageList.tsx               ← Scrollable list of messages + output cards
│   │   │   ├── UserMessage.tsx               ← User bubble
│   │   │   ├── KiraMessage.tsx               ← Kira message with avatar
│   │   │   ├── StatusChips.tsx               ← Processing chips row
│   │   │   ├── OutputCard.tsx                ← Engineered prompt card
│   │   │   ├── DiffView.tsx                  ← Diff display (toggled)
│   │   │   ├── QualityScores.tsx             ← 3 score bars
│   │   │   ├── InputBar.tsx                  ← Message input with persona dot
│   │   │   ├── AttachmentPill.tsx            ← File attachment pill above input
│   │   │   ├── ClarificationChips.tsx        ← Quick-reply chips for Kira's questions
│   │   │   └── EmptyState.tsx                ← First-visit empty state with suggestions
│   │   └── hooks/
│   │       ├── useKiraStream.ts              ← THE critical hook. SSE + state machine.
│   │       ├── useSessionId.ts               ← Session ID management
│   │       ├── useInputBar.ts                ← Input, attachment, voice state
│   │       └── useVoiceInput.ts              ← MediaRecorder → /transcribe
│   ├── history/
│   │   ├── components/
│   │   │   ├── HistoryList.tsx               ← All sessions, grouped by date
│   │   │   ├── HistoryCard.tsx               ← Single prompt history entry
│   │   │   └── QualityTrendBar.tsx           ← Weekly stat sparkline
│   │   └── hooks/
│   │       └── useHistory.ts                 ← Fetch + group history
│   └── profile/
│       ├── components/
│       │   ├── ProfileStats.tsx              ← What Kira knows + quality trend
│       │   ├── QualitySparkline.tsx          ← 30-day quality chart
│       │   └── McpTokenSection.tsx           ← MCP token generation
│       └── hooks/
│           └── useProfile.ts                 ← Profile data + session count
```

---

## 3. COMPONENT CONTRACTS

---

### `app/app/layout.tsx`

`'use client'` — needs session check and nav state.

**On mount:**
1. `getSession()` — if null, redirect to ROUTES.LOGIN
2. Render immediately if session exists (no flash)

**Renders:**
- App nav (top bar):
  - Left: Logo mark + "PromptForge"
  - Center nav links: "Chat" (→ /app), "History" (→ /app/history), "Profile" (→ /app/profile)
  - Active link: `text-text-bright bg-layer2 rounded-md`
  - Right: avatar circle (first letter of email), sign out on click
- `{children}` below nav
- Full viewport height: `h-screen flex flex-col`

**Must NOT render:** agent names, model names, session IDs

---

### `features/chat/components/ChatContainer.tsx`

`'use client'` — the root of all chat state.

**Props:** none

**State ownership:** ChatContainer owns ALL chat state. Nothing is lifted higher. Children receive only what they need.

**Renders:**
```
<div className="flex flex-col h-full">
  <MessageList messages={messages} isStreaming={isStreaming} />
  {clarificationPending && (
    <ClarificationChips chips={clarificationOptions} onSelect={handleClarification} />
  )}
  {attachment && <AttachmentPill file={attachment} onRemove={clearAttachment} />}
  <InputBar
    value={input}
    onChange={setInput}
    onSubmit={handleSubmit}
    onAttach={handleAttach}
    onVoice={handleVoice}
    disabled={isStreaming || isRateLimited}
    personaDotColor={personaDotColor}
    placeholder={clarificationPending ? "Answer Kira..." : "Type your prompt..."}
  />
</div>
```

**Uses:** `useKiraStream`, `useSessionId`, `useInputBar`, `useVoiceInput`

**Must NOT render:** agent names, model names, raw errors, session IDs, Supabase field names

---

### `features/chat/components/MessageList.tsx`

`'use client'`

**Props:**
```typescript
interface MessageListProps {
  messages: ChatMessage[]
  isStreaming: boolean
}
```

**Renders:**
- Scrollable container with auto-scroll to bottom on new message
- Auto-scroll: `useEffect` with `scrollIntoView({ behavior: 'smooth' })` on `messages` change
- If `messages.length === 0`: `<EmptyState />`
- For each message:
  - type='user': `<UserMessage>`
  - type='status': `<StatusChips>`
  - type='kira': `<KiraMessage>`
  - type='output': `<OutputCard>`
  - type='error': `<KiraMessage>` with `isError=true`

**React StrictMode fix — critical:**
```typescript
// Auto-scroll ref pattern — must use this exact pattern:
const bottomRef = useRef<HTMLDivElement>(null)
useEffect(() => {
  bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
}, [messages])
// <div ref={bottomRef} /> at the bottom of the list
```

---

### `features/chat/components/EmptyState.tsx`

`'use client'`

**Props:** `{ domain?: string; onSuggestionClick: (text: string) => void }`

**Renders:**
- Kira message: `"[domain] — got it. I've got your profile ready. **Show me what you're working on.**"`
  - If no domain: `"I've got your profile ready. Show me what you're working on."`
- 3 suggestion cards below Kira's message:
  - Cards are domain-aware if profile has `primary_use`
  - Each card: full-width, `border-border-default bg-layer2 hover:border-kira hover:bg-[var(--kira-glow)]`, right arrow `text-kira`
  - Click: populate input bar AND submit (don't wait for user to hit enter)
- Domain-specific suggestions (examples):
  ```
  Writing/Marketing: 
    "Write a cold outreach email for a SaaS product"
    "Improve this product launch announcement"
    "Help me write a LinkedIn post about..."
  
  Code:
    "Help me write a code review for this PR"
    "Write tests for this function"
    "Help me document this API endpoint"
  
  Research:
    "Summarize the key points in this paper"
    "Write a literature review section on..."
    "Help me structure a research report"
  
  Fallback (no domain):
    "Help me write an email to my client"
    "Make this paragraph more specific"
    "Write a brief for my team"
  ```

---

### `features/chat/components/StatusChips.tsx`

`'use client'`

**Props:**
```typescript
interface StatusChipsProps {
  status: ProcessingStatus   // from useKiraStream
}
```

**Renders:** Row of `<Chip>` components showing current processing state.

**Chip labels (human-readable — never agent variable names):**
```
kira chip:     "Reading context"  active=true during kira step
intent chip:   "Analyzing intent" active when running, skipped when skipped
context chip:  "Context"         active when running, skipped when skipped
domain chip:   "Domain"          active when running, skipped when skipped
engineer chip: "Crafting prompt"  active=true when engineer running
memory chip:   "N memories"      shown after result, uses memory variant
latency chip:  "3.4s"            shown after result, uses teal variant
```

**State progression:**
```
KIRA_READING:  [Kira: active]
SWARM_RUNNING: [Kira: done] [intent: active/skipped] [context: active/skipped] [domain: active/skipped] [engineer: active]
COMPLETE:      [done: all done] [memory: "N memories"] [teal: "3.4s"]
```

**Must NOT render:** "intent agent", "context agent", "domain agent", "prompt engineer" — only human-readable labels above

---

### `features/chat/components/KiraMessage.tsx`

`'use client'`

**Props:**
```typescript
interface KiraMessageProps {
  message: string
  isError?: boolean
  isStreaming?: boolean
  retryable?: boolean
  onRetry?: () => void
}
```

**Renders:**
- Kira avatar: 28px, `rounded-lg bg-[var(--kira-dim)] border border-kira text-kira font-mono font-bold` letter "K"
- Message text: `text-[13px] text-text-default leading-relaxed`
- Bold text (from `**text**` markdown): `text-text-bright font-semibold` — parse simple bold only
- isError=true: container has `border border-intent/20 bg-intent/5 rounded-xl p-3.5`
- isError=true + retryable: show "Try again" button below message
- isStreaming=true: show blinking cursor `|` after last character

**Must NOT render:** raw error messages from API, technical error details

---

### `features/chat/components/OutputCard.tsx`

`'use client'` — owns diff toggle state.

**Props:**
```typescript
interface OutputCardProps {
  result: ChatResult
  onCopy: () => void
  onRefine: (message: string) => void
  isCopied: boolean    // true for 2 seconds after copy
}
```

**Renders:**

**Card header:**
- Label: "Engineered prompt" (font-mono text-[9px] tracking-wider uppercase text-text-dim)
- Memory badge: if `memories_applied > 0`: `text-memory font-mono text-[10px]` "● N memories"
- Latency: `text-teal font-mono text-[10px]` e.g. "3.4s"

**Card body:**
- Output text: `text-[--output-text] text-[13px] leading-relaxed`
- Annotation chips (always visible):
  - Count additions as "ann-add" chips in context color
  - Count removals as "ann-remove" chips in intent color
  - e.g. "+ Added structure", "+ Added length constraint", "− Removed vagueness"
  - Derive from `result.diff` items (count add/remove types, label generically)

**Diff section (toggle):**
- Toggle: "Show diff" + toggle track, OFF by default
- When on: render `<DiffView diff={result.diff} />`

**Quality scores:**
- `<QualityScores scores={result.quality_score} />`
- Always visible (not behind toggle)

**Actions row:**
- `Button variant="ghost" size="sm"` "Copied!" (2s) or "Copy" → calls onCopy
- `Button variant="kira" size="sm"` "Refine →" → opens pre-filled input "make it [...]"
- Push Further: NOT shown (Phase 5)

**Gradient border on complete:**
```typescript
// Applied via inline style when result exists
style={{
  border: '1px solid transparent',
  backgroundClip: 'padding-box',
  position: 'relative',
}}
// ::before pseudo — not possible in React inline styles
// Instead: wrap in a div with gradient border trick:
// outer div: bg-gradient-to-br from-kira/60 via-engineer/40 to-memory/30 p-px rounded-[11px]
// inner div: bg-layer1 rounded-[10px] (the actual card)
```

---

### `features/chat/components/DiffView.tsx`

`'use client'`

**Props:** `{ diff: DiffItem[] }`

**Renders:**
- Each diff item inline (not separate lines):
  - type='add': `<span className="bg-context/15 text-[#6ee7b7] rounded px-0.5">text</span>`
  - type='remove': `<span className="line-through text-text-dim opacity-60">text</span>`
  - type='keep': `<span className="text-text-default">text</span>`

---

### `features/chat/components/QualityScores.tsx`

`'use client'`

**Props:** `{ scores: QualityScore }`

**Renders:** 3 rows (specificity, clarity, actionability):
- Label: `font-mono text-[10px] text-text-dim w-24 flex-shrink-0`
- Bar track: `flex-1 h-[3px] bg-border-default rounded-full overflow-hidden`
- Bar fill: `h-full rounded-full bg-kira` width = `${(score/5) * 100}%`
- Value: `font-mono text-[10px] text-text-dim w-6 text-right` e.g. "4/5"

Bar fill animates on mount: start 0%, animate to final width via CSS transition `duration-700 ease-out`

---

### `features/chat/components/InputBar.tsx`

`'use client'`

**Props:**
```typescript
interface InputBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  onAttach: (file: File) => void
  onVoice: () => void
  disabled: boolean
  personaDotColor: 'cold' | 'warm' | 'tuned'
  placeholder: string
  isRecording?: boolean
}
```

**Renders:**
- Container: `flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border bg-layer2 transition-colors`
  - Focused: `border-kira`
  - Default: `border-border-strong`
- Persona dot: `w-2 h-2 rounded-full flex-shrink-0`
  - cold → `bg-[var(--dot-cold)]`
  - warm → `bg-[var(--dot-warm)] shadow-[0_0_6px_var(--domain)]`
  - tuned → `bg-[var(--dot-tuned)] shadow-tuned`
  - Hover tooltip: "Kira doesn't know you yet" / "Kira is learning your patterns" / "Kira knows your work deeply"
- Input: `flex-1 bg-transparent border-none outline-none text-[13px] font-display text-text-default placeholder:text-text-dim`
- Enter key submits (if not shift+enter)
- Textarea auto-resizes (max 5 lines)
- Paperclip icon: opens file input (accept: `.pdf,.docx,.txt`, 2MB limit)
  - Hidden `<input type="file">` ref, click on icon triggers it
- Mic icon: starts/stops recording, `text-intent border-intent` when `isRecording=true`
- Send button: `bg-kira border-kira text-white` rounded, → on click onSubmit, disabled when input empty or disabled=true
- Send button hover: `shadow-kira-strong`

**File validation (in component, before calling onAttach):**
- Size: max 2MB for documents, 5MB for images
- Type: `.pdf`, `.docx`, `.txt` only (no executables, no xlsx)
- On violation: show inline error below input (Kira-voiced: "That file's too large. Keep it under 2MB.")

---

### `features/chat/components/AttachmentPill.tsx`

`'use client'`

**Props:** `{ file: File; onRemove: () => void }`

**Renders:**
- `flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-layer1 border border-border-strong`
- File icon (type-specific: 📄 for pdf/docx/txt)
- Filename (truncated to 24 chars with ellipsis): `text-[11px] text-text-default font-display`
- Remove button: `text-text-dim hover:text-intent text-[12px]` "×"

---

### `features/chat/components/ClarificationChips.tsx`

`'use client'`

**Props:** `{ chips: string[]; onSelect: (value: string) => void }`

**Renders:**
- Horizontal scrollable row of chips
- Each chip: `px-3 py-1.5 rounded-full border border-[var(--kira-dim)] bg-[var(--kira-glow)] text-[12px] text-kira cursor-pointer`
- Hover: `bg-[var(--kira-dim)]`
- Click: onSelect(chip text), chips disappear (clarification answered)

---

### `features/history/components/HistoryList.tsx`

`'use client'`

**Props:** `{ items: HistoryItem[]; isLoading: boolean }`

**Renders:**
- Search input (client-side filter, no API call): `Input` from `@/components/ui`
- Quality trend bar: `<QualityTrendBar items={items} />`
- Items grouped by date:
  - Group label: "Today", "Yesterday", "March 5", etc. — `font-mono text-[10px] tracking-wider uppercase text-text-dim`
  - Group contains: `<HistoryCard>` for each item
- isLoading: 3 skeleton cards (pulsing gray rectangles)
- Empty: Kira message "No prompts yet. Head back to the forge."

---

### `features/history/components/HistoryCard.tsx`

`'use client'`

**Props:** `{ item: HistoryItem; onUseAgain: (prompt: string) => void }`

**Renders:**
- Original prompt: `text-[12px] text-text-dim italic` truncated to 1 line
- Improved prompt: `text-[13px] text-text-default` truncated to 2 lines (`-webkit-line-clamp: 2`)
- Meta row:
  - Score pills: 3 pills for specificity, clarity, actionability
    - `bg-[var(--kira-dim)] text-kira font-mono text-[10px] px-1.5 py-0.5 rounded`
    - "Spec 4", "Clar 5", "Act 3"
  - Right: "Copy" button + "Use again →" button (kira variant)
- Hover: `border-border-strong` from `border-border-default`

---

### `features/history/components/QualityTrendBar.tsx`

`'use client'`

**Props:** `{ items: HistoryItem[] }`

**Renders:**
- If < 5 items: nothing (not enough data)
- If >= 5 items:
  - Trend text: "Your prompts are **X% more specific** than 30 days ago." (`text-context` on the % number)
  - Sparkline: last 12 items as bar chart, `bg-kira` bars, `flex items-end gap-1 h-6`
  - Best week note: `font-mono text-[10px] text-text-dim`

---

### `features/profile/components/ProfileStats.tsx`

`'use client'`

**Props:** `{ profile: UserProfileData; sessionCount: number }`

**Renders:**
- Label: "What Kira knows" (font-mono)
- Rows:
  - "Your main areas" → `profile.primary_use` (text-bright)
  - "Your tone" → derived from profile or "Learning..." if not established
  - "Kira's confidence" → derived from session count:
    - 0-9: "Still learning" (text-dim)
    - 10-29: "Getting warm" (text-domain)
    - 30+: "High — rarely needs more" (text-success)
  - "Memories" → `N from your sessions` (text-bright)

**Must NOT render:** technical profile field names, raw database values, session IDs

---

### `features/profile/components/McpTokenSection.tsx`

`'use client'`

**Props:** `{ sessionCount: number; trustLevel: 0 | 1 | 2 }`

**Renders:**
- Trust level badge:
  - Level 0: grey dot + "COLD — Keep using the app, I'll get sharper in MCP too."
  - Level 1: amber dot + `trust-warm` badge "WARM (N sessions)"
  - Level 2: green dot + `trust-tuned` badge "TUNED (N sessions)"
- Generate token button: `Button variant="kira"` full-width "Generate MCP token — valid 365 days"
  - On click: calls `POST /mcp/token` → shows token in a copyable mono text box
  - Shows "⚠️ Copy this now — it won't be shown again" in domain color
- Note: `font-mono text-[10px] text-text-dim` "Token stored as hash only · Revocable anytime"

---

## 4. HOOK CONTRACTS

### `features/chat/hooks/useKiraStream.ts`

**This is the most critical hook in the entire frontend. Read carefully.**

```typescript
// 'use client'
// Input: { sessionId: string; token: string }
// Return: {
//   messages: ChatMessage[]        // full message history for current session
//   status: ProcessingStatus       // current chip state
//   isStreaming: boolean
//   isRateLimited: boolean
//   rateLimitSecondsLeft: number   // countdown for rate limit UI
//   error: KiraError | null
//   clarificationPending: boolean
//   clarificationOptions: string[]
//   send: (message: string, attachment?: File) => void
//   retry: () => void              // retry last failed message
//   clearError: () => void
// }

// CRITICAL: React StrictMode fires effects twice.
// Use AbortController — do NOT remove StrictMode to fix this.
// Pattern:
useEffect(() => {
  const controller = new AbortController()
  // pass controller.signal to parseStream
  return () => controller.abort()
}, [])

// State machine:
// IDLE → KIRA_READING → SWARM_RUNNING → COMPLETE
//      ↘ CLARIFICATION (if kira returns clarification_needed)
//      ↘ RATE_LIMITED (if 429)
//      ↘ ERROR (if any error)

// Message types:
type ChatMessage = {
  id: string           // uuid
  type: 'user' | 'status' | 'kira' | 'output' | 'error'
  content?: string
  result?: ChatResult  // for type='output'
  isError?: boolean
  isStreaming?: boolean
}

// SSE event handling (in order):
// 'status'       → append/update status message in messages[]
// 'kira_message' → append kira message, set isStreaming until complete=true
// 'result'       → append output card message, set status=COMPLETE
// 'error'        → mapError() → append error kira message
// 'done'         → set isStreaming=false

// Input is preserved on error — never clear it
// Last message sent stored in ref for retry

// Rate limit handling:
// On 429 → set isRateLimited=true, start 30s countdown
// After countdown → set isRateLimited=false automatically

// Clarification handling:
// On kira_message with clarification_needed flag (detect from message content or classification event)
// → set clarificationPending=true
// → extract chips from kira's message (parse "Is this X, Y, or Z?" into chips)
// On clarification chip select:
// → send the chip text as next message
// → set clarificationPending=false

// Side effects allowed: fetch (via parseStream), sessionStorage read/write
// Must NOT: call parseStream inside a render, store token in localStorage
```

---

### `features/chat/hooks/useSessionId.ts`

```typescript
// Input: none
// Return: { sessionId: string }
// Generates UUID on first call, stores in sessionStorage
// Same tab = same session, new tab = new session
// Must use crypto.randomUUID() if available, fallback to manual UUID
```

---

### `features/chat/hooks/useInputBar.ts`

```typescript
// Input: { onSubmit: (message: string, attachment?: File) => void }
// Return: {
//   input: string
//   setInput: (val: string) => void
//   attachment: File | null
//   setAttachment: (file: File | null) => void
//   handleSubmit: () => void      // validates, calls onSubmit, clears input
//   handleKeyDown: (e: KeyboardEvent) => void
// }
// Validation before submit:
//   - trim whitespace
//   - min length LIMITS.PROMPT_MIN (5 chars)
//   - if fails: don't call onSubmit, don't show error (just don't submit)
// Input NOT cleared on error (useKiraStream rule)
// Input cleared on successful submit
```

---

### `features/chat/hooks/useVoiceInput.ts`

```typescript
// Input: { onTranscript: (text: string) => void; token: string }
// Return: {
//   isRecording: boolean
//   startRecording: () => void
//   stopRecording: () => void    // auto-calls apiTranscribe, then onTranscript
//   error: string | null
// }
// Uses MediaRecorder API
// On stop: creates Blob, calls apiTranscribe(blob, token), calls onTranscript(result.transcript)
// Error: "Microphone access denied." or "Transcription failed. Try typing instead."
// Cleanup: stops MediaRecorder on unmount
// Must check: typeof navigator.mediaDevices !== 'undefined' (SSR safe)
```

---

### `features/history/hooks/useHistory.ts`

```typescript
// Input: { token: string }
// Return: {
//   items: HistoryItem[]
//   isLoading: boolean
//   error: string | null
//   groupedByDate: Record<string, HistoryItem[]>  // { "Today": [...], "Yesterday": [...] }
//   searchQuery: string
//   setSearchQuery: (q: string) => void
//   filteredItems: HistoryItem[]  // client-side filter of items
// }
// Calls apiHistory() on mount
// Groups by date using Intl.DateTimeFormat
// Search: filters on original_prompt + improved_prompt (case-insensitive, no API call)
```

---

### `features/profile/hooks/useProfile.ts`

```typescript
// Input: { token: string }
// Return: {
//   profile: UserProfileData | null
//   sessionCount: number
//   trustLevel: 0 | 1 | 2
//   personaDotColor: 'cold' | 'warm' | 'tuned'
//   isLoading: boolean
// }
// trustLevel derived from sessionCount using PERSONA_DOT_THRESHOLDS
// personaDotColor: cold (0-9) / warm (10-29) / tuned (30+)
// profile fetched from Supabase directly (not backend API)
```

---

## 5. API INTEGRATION

### Chat streaming — `parseStream()`

```typescript
// Called by: useKiraStream.send()
// Endpoint: POST /chat/stream
// Request: ChatRequest { message, session_id, input_modality?, file_base64? }
// Auth: JWT token from getAccessToken()
// Events handled: status, kira_message, result, done, error
// AbortController signal passed to parseStream
// On abort: no error shown (user navigated away)
```

### History — `apiHistory()`

```typescript
// Called by: useHistory on mount
// Endpoint: GET /history
// Auth: JWT token
// Response: HistoryItem[]
// Error: shown as Kira message in history page, not modal or alert
```

### Transcribe — `apiTranscribe()`

```typescript
// Called by: useVoiceInput.stopRecording()
// Endpoint: POST /transcribe
// Body: FormData with audio blob
// Auth: JWT token
// Response: { transcript: string }
// On success: populate input bar with transcript (user reviews before sending)
// On error: Kira-voiced message, don't block input
```

---

## 6a. BUILD ORDER — AGENT FOLLOWS THIS SEQUENCE EXACTLY

Plan 4 is the largest and most complex plan. 15+ files. Build one file at a time. `npx tsc --noEmit` after every single file. Do not batch. Do not skip steps.

```
STEP 4.1 — features/chat/types.ts
  Build: ChatMessage, ProcessingStatus, all chat-local types
  Import from: lib/types.ts (do not redeclare shared types)
  Verify: tsc clean. No imports from features/ (types file is pure).

STEP 4.2 — features/chat/hooks/useSessionId.ts
  Build: UUID generation, sessionStorage read/write
  Verify: tsc clean. typeof window guard present. No render-phase storage access.

STEP 4.3 — features/chat/hooks/useInputBar.ts
  Build: input value, attachment state, submit handler, validation
  Verify: tsc clean. Input NOT cleared on error path. Only cleared after onSubmit call.

STEP 4.4 — features/chat/hooks/useVoiceInput.ts
  Build: MediaRecorder, blob creation, apiTranscribe call
  Verify: tsc clean. typeof navigator guard present.

STEP 4.5 — features/chat/hooks/useKiraStream.ts  ← MOST CRITICAL
  Build: state machine, SSE via parseStream, AbortController cleanup
  Rules that MUST be present:
    - AbortController created inside useEffect
    - controller.abort() called in useEffect cleanup
    - State machine: idle → kira_reading → swarm_running → complete/error/rate_limited
    - Rate limit countdown: 30s timer, clears when done
    - Input NOT cleared on error
    - Last sent message stored in ref for retry
  Verify: tsc clean. Manually confirm AbortController pattern is present.
  This step takes longest. Do not rush.

STEP 4.6 — features/chat/components/UserMessage.tsx
  Build: user bubble component
  Verify: tsc clean.

STEP 4.7 — features/chat/components/KiraMessage.tsx
  Build: avatar + message, streaming cursor, error variant, retry button
  Verify: tsc clean. No raw error strings in renders.

STEP 4.8 — features/chat/components/StatusChips.tsx
  Build: chip row from ProcessingStatus, human-readable labels only
  LABELS CHECK — these exact strings and no others:
    "Reading context" | "Analyzing intent" | "Context" | "Domain" | "Crafting prompt"
    "N memories applied" | "3.4s" (latency format)
  Verify: tsc clean. grep source for "intent agent" "GPT" "prompt_engineer" — must be 0 results.

STEP 4.9 — features/chat/components/DiffView.tsx + QualityScores.tsx
  Build: diff inline renderer + score bars with animation
  Verify: tsc clean. Bar animation uses CSS transition not JS interval.

STEP 4.10 — features/chat/components/OutputCard.tsx
  Build: full output card with gradient border, diff toggle (off by default), actions
  Verify: tsc clean. Diff toggle is OFF by default. No Push Further button.

STEP 4.11 — features/chat/components/AttachmentPill.tsx + ClarificationChips.tsx
  Build: attachment pill with remove, clarification chip row
  Verify: tsc clean.

STEP 4.12 — features/chat/components/EmptyState.tsx
  Build: domain-aware suggestions, click submits automatically
  Verify: tsc clean. Suggestions vary by profile.primary_use.

STEP 4.13 — features/chat/components/InputBar.tsx
  Build: full input bar with dot, file picker, mic, send
  Verify: tsc clean. Persona dot states match PersonaDotState type.

STEP 4.14 — features/chat/components/MessageList.tsx
  Build: scrollable list, auto-scroll ref, routes message types to components
  Verify: tsc clean. bottomRef scrollIntoView pattern present.

STEP 4.15 — features/chat/components/ChatContainer.tsx
  Build: assembles all hooks and components, owns all state
  Verify: tsc clean. No prop drilling beyond 2 levels.

STEP 4.16 — app/app/layout.tsx
  Build: auth gate, app nav, session check with loading state
  Verify: npm run dev → /app redirects to /login when no session. No flash.

STEP 4.17 — app/app/page.tsx
  Build: chat page, renders ChatContainer
  Verify: With NEXT_PUBLIC_USE_MOCKS=true → full mock chat flow works.
  This is the first full end-to-end test of the chat UI.
  Do not proceed until mock mode works completely.

STEP 4.18 — features/history/hooks/useHistory.ts + components/
  Build: fetch, group by date, client-side search
  Verify: tsc clean. With USE_MOCKS=true → MOCK_HISTORY displays grouped.

STEP 4.19 — app/app/history/page.tsx
  Build: history page
  Verify: tsc clean.

STEP 4.20 — features/profile/hooks/useProfile.ts + components/
  Build: profile stats, sparkline, MCP section
  Verify: tsc clean.

STEP 4.21 — app/app/profile/page.tsx
  Build: profile page
  Verify: tsc clean.

STEP 4.22 — bash verify.sh
  Expected: ALL CHECKS PASSED ✅

STEP 4.23 — Set NEXT_PUBLIC_USE_MOCKS=false, test against real backend
  This is YOUR step (human). Agent cannot do this.
```

---

## 6b. DESIGN RULES — PLAN 4 SPECIFIC

### App nav
- `h-12 px-5 border-b border-border-subtle bg-layer1`
- Logo: smaller than landing, `text-[14px]` weight 700
- Nav links: `text-[12px] px-2.5 py-1.5 rounded-md transition-colors`

### Chat area
- Padding: `px-5 py-4`
- Max width: `max-w-2xl mx-auto` (centered, readable width)
- User messages: `self-end max-w-[72%] bg-layer2 border border-border-strong rounded-xl rounded-br-sm px-3.5 py-2.5`
- Message gap: `gap-4`

### Output card gradient border
```typescript
// Wrapper div:
className="p-px rounded-[11px] bg-gradient-to-br from-kira/50 via-engineer/30 to-memory/20"
// Inner div:
className="bg-layer1 rounded-[10px]"
```

### Persona dot tooltip
- Use CSS `title` attribute on the dot element
- No custom tooltip component needed for now

### Latency display
- Always `font-mono text-[10px] text-teal`
- Format: "3.4s" (one decimal place, always seconds)
- Derived: `(latency_ms / 1000).toFixed(1) + 's'`

### Quality bar animation
- `transition-[width] duration-700 ease-out`
- Start at 0 on mount, CSS transition handles the reveal

### Empty state suggestions
- `gap-2 flex flex-col` 
- Cards: `flex items-center justify-between px-4 py-3 rounded-xl border border-border-default bg-layer2`
- Arrow: `text-kira` →

### History sparkline
```typescript
// Simple bars — no chart library needed
// items.slice(-12).map(item => avg score) → bar heights as percentages
// bars: flex-1 rounded-sm bg-kira opacity-50 hover:opacity-100
```

---

## 7. VERIFICATION CHECKLIST

**Phase A — Mock verification (agent runs this, no backend needed):**
```bash
# Set in .env.local first:
# NEXT_PUBLIC_USE_MOCKS=true

bash verify.sh
# Expected: ALL CHECKS PASSED ✅
```

Then manually in browser with `npm run dev`:
- [ ] `/app` loads, auth gate redirects to `/login` if no session
- [ ] After login (Plan 3 test user): `/app` loads with empty state
- [ ] Type a message, submit → mock chips animate in sequence
- [ ] Mock Kira message appears, streams with cursor
- [ ] Mock output card appears 200ms after Kira message
- [ ] Quality bars animate from 0 to final value
- [ ] Diff toggle is OFF by default, turns ON when clicked
- [ ] Copy button works, shows "Copied!" for 2 seconds
- [ ] `/app/history` shows MOCK_HISTORY grouped by date
- [ ] `/app/profile` shows MOCK_PROFILE data
- [ ] No agent names in DOM (DevTools → Elements → search "intent agent", "GPT")

**Phase B — Real backend verification (human runs this):**
```bash
# Set in .env.local:
# NEXT_PUBLIC_USE_MOCKS=false
```

- [ ] Full chat flow with real backend SSE
- [ ] Quality bars reflect real scores
- [ ] Memory badge shows when memories_applied > 0
- [ ] Latency shows in teal font-mono
- [ ] History shows real prompts from session
- [ ] Error state: break API URL → Kira's voice message appears, input preserved
- [ ] Rate limit: submit rapidly → rate limit message with countdown
- [ ] Attachment: add .txt file → pill shows, sends with message
- [ ] Security scan: grep rendered DOM for forbidden strings → 0 results

**Chat — empty state:**
- [ ] `/app` loads without flash of unauthenticated content
- [ ] Kira's greeting shows domain from onboarding answers
- [ ] 3 domain-specific suggestions appear
- [ ] Clicking suggestion populates input AND submits
- [ ] Persona dot is grey (new user, 0 sessions)

**Chat — sending a message:**
- [ ] Type "help me write an email to my client" → hit Enter
- [ ] Processing chips appear with human-readable labels (NOT "intent agent")
- [ ] Kira's message appears (streaming, cursor visible)
- [ ] Output card appears after Kira message (200ms gap)
- [ ] Output text is bright (`--output-text`)
- [ ] Quality score bars animate in from 0
- [ ] Latency shows in teal font-mono
- [ ] Copy button copies to clipboard
- [ ] Copy button shows "Copied!" for 2 seconds
- [ ] Diff toggle is off by default
- [ ] Diff toggle shows colored inline diff when turned on

**Chat — error states:**
- [ ] Break NEXT_PUBLIC_API_URL → Kira says error in her voice
- [ ] Input is preserved after error
- [ ] "Try again" button visible on retryable errors
- [ ] No raw error strings visible

**Chat — attachments:**
- [ ] Click paperclip → file picker opens
- [ ] Select a .txt file → attachment pill appears above input bar
- [ ] Pill shows filename truncated + × remove button
- [ ] × removes pill
- [ ] File > 2MB → inline error below input bar

**Chat — clarification:**
- [ ] Send ambiguous message "help me write something"
- [ ] If Kira responds with a question: clarification chips appear below chat
- [ ] Clicking a chip sends it as a message and clears chips
- [ ] Input placeholder changes to "Answer Kira..."

**History page:**
- [ ] `/app/history` loads with real history data
- [ ] Prompts grouped by date
- [ ] Search filters by typing
- [ ] "Copy" copies improved prompt
- [ ] "Use again →" navigates to /app with prompt pre-filled

**Profile page:**
- [ ] `/app/profile` shows real profile data
- [ ] Stats show onboarding answers (domain, audience)
- [ ] Session count visible
- [ ] MCP section shows correct trust level
- [ ] Token generation button visible

**Security — verify these explicitly:**
- [ ] Open DevTools → Network tab → no requests to non-whitelisted domains
- [ ] No agent names anywhere in rendered UI text (grep in DevTools Elements)
- [ ] No model names (GPT-4o) anywhere in rendered UI text
- [ ] No session IDs visible anywhere in rendered UI text
- [ ] No raw Supabase errors visible on auth failure
- [ ] No backend URL (Railway/Koyeb domain) visible anywhere in rendered UI text
- [ ] No Supabase project ID visible in rendered content

---

## 8. HANDOFF — PLAN 4 IS FINAL

No Plan 5 agent spec exists yet. After Plan 4 ships:

**What's ready for Phase 5 (future):**
- `/chat/stream` can add new SSE event types without frontend changes if `parseStream` handles unknowns gracefully
- `OutputCard` has a slot for "Push Further ✦" button (currently not rendered, easy to add)
- `useKiraStream` state machine can add `PUSH_FURTHER` state
- `McpTokenSection` already handles all 3 trust levels
- Chrome Extension and CLI (Phase 5) use the same backend API — `lib/api.ts` is already complete

**What needs backend work before Phase 5:**
- `POST /chat/push-further` endpoint
- Demo account rate limiting (50 req/hour cap)
- Migration 013 (`migrations/013_add_mcp_tokens.sql`) must be run

---

*Plan 4 complete. All 4 plans are ready. Build in order: Plan 1 → verify → Plan 2 → verify → Plan 3 → verify → Plan 4.*
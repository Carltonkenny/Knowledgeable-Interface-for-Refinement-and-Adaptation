# FRONTEND PLAN 3 — Auth + Onboarding
### PromptForge v2.0 · app/(auth)/ · app/onboarding/ · features/onboarding/
---

## 1. CONTEXT

### What's already built (from Plans 1 + 2)
- All design tokens, `lib/*`, `components/ui/*` (Plan 1)
- Full landing page, `useDemoGate`, `useScrollReveal` (Plan 2)
- `apiSaveProfile()`, `getSupabaseClient()`, `getSession()`, `getAccessToken()` ready

### What this plan builds
The complete user entry pipeline: signup → onboarding → `/app`. After this plan, a test user exists in the database with a seeded profile. Plan 4 depends on this test user.

### What this plan must NOT touch
- `promptforge/` backend directory
- `lib/*` — read only (except `lib/auth.ts` which is new in this plan)
- `features/landing/` — read only
- `app/(marketing)/` — read only

### Assumptions
- Supabase project has email+password auth enabled
- Google OAuth configured in Supabase dashboard (Client ID + Secret from Google Cloud Console)
- `user_profiles` table exists in Supabase with columns: `user_id`, `primary_use`, `audience`, `ai_frustration`, `frustration_detail`, `created_at`
- Backend `/user/profile` endpoint accepts POST with profile payload + JWT

---

## 2. FILES TO CREATE

```
promptforge-web/
├── lib/
│   └── auth.ts                             ← Auth helpers used across auth + onboarding
├── app/
│   ├── (auth)/
│   │   ├── layout.tsx                      ← Auth layout (two-col, Kira left panel)
│   │   ├── login/
│   │   │   └── page.tsx                    ← Login page
│   │   └── signup/
│   │       └── page.tsx                    ← Signup page
│   └── onboarding/
│       └── page.tsx                        ← Onboarding (reads step from searchParam)
├── features/
│   └── onboarding/
│       ├── types.ts                        ← Onboarding state types
│       ├── components/
│       │   ├── AuthLeftPanel.tsx           ← Shared left panel (Kira quote + arch bg)
│       │   ├── LoginForm.tsx               ← Login form (Google + email)
│       │   ├── SignupForm.tsx              ← Signup form (Google + email)
│       │   ├── OnboardingStep.tsx          ← Single question screen
│       │   ├── OnboardingProgress.tsx      ← 3 dot progress indicator
│       │   └── OnboardingLayout.tsx        ← Full-screen centered layout
│       └── hooks/
│           ├── useAuth.ts                  ← Auth actions (login, signup, Google OAuth)
│           └── useOnboarding.ts            ← Step state, answers, submit
```

---

## 3. COMPONENT CONTRACTS

---

### `lib/auth.ts`

New file. Auth helpers used by both auth forms and middleware.

```typescript
// Exports:
//   signInWithGoogle(): Promise<void>         — Supabase OAuth, redirects to /onboarding
//   signInWithEmail(email, password)          — returns { error? }
//   signUpWithEmail(email, password)          — returns { error? }
//   requireAuth(): Promise<Session | null>    — for use in server components
//   getSessionOrRedirect(redirectTo)          — redirect to login if no session

// Google OAuth redirect:
//   redirectTo: `${window.location.origin}/onboarding`
//   Supabase handles callback at /auth/callback (create this route below)
```

---

### `app/auth/callback/route.ts`

OAuth callback handler. Required for Google OAuth.

```typescript
// GET /auth/callback?code=...
// Exchange code for session via supabase.auth.exchangeCodeForSession()
// On success: redirect to /onboarding
// On error: redirect to /login?error=oauth_failed
```

---

### `app/(auth)/layout.tsx`

Server component. Two-column layout used by both login and signup.

**Renders:**
- Grid: `grid grid-cols-2` desktop, single column mobile
- Left column: `<AuthLeftPanel />`
- Right column: `{children}`
- Background: `var(--bg)` with subtle arch grid on left panel only

**Must NOT:** add any loading state, auth checks, redirects — this is pure layout

---

### `features/onboarding/components/AuthLeftPanel.tsx`

Server component. Used by both login and signup layouts.

**Props:** `{ variant: 'login' | 'signup' }`

**Renders:**
- Background: repeating grid lines at 40px (opacity 0.03, kira color) — creates depth
- Logo: ⬡ mark + "PromptForge"
- Headline (variant=signup): `"Your prompts,` (break) `precisely engineered."`
- Headline (variant=login): `"Welcome back."` (break) `"Kira remembers."`
- Sub (signup): `"Kira learns how you think. First session starts warm — three questions and she knows your domain before you send a prompt."`
- Sub (login): `"Your profile is intact. Pick up exactly where you left off."`
- Kira quote block:
  - variant=signup: `"Let's see what you're working on."`
  - variant=login: `"Good to have you back."`
- Kira quote block style: `bg-[var(--kira-glow)] border border-[var(--kira-dim)] rounded-xl p-3.5` with kira avatar

**Must NOT:** contain any interactive elements

---

### `features/onboarding/components/LoginForm.tsx`

`'use client'`

**Props:** none

**Renders:**
- Title: "Sign in to PromptForge"
- Google button (primary): "Continue with Google" — calls `useAuth().signInWithGoogle()`
  - Google "G" SVG logo inline (no external image)
- Divider: "OR" (font-mono, text-dim, line on each side)
- Email input (from `@/components/ui`)
- Password input
- Submit button: `Button variant="primary"` full-width "Sign in →"
- Footer: "Don't have an account? [Sign up]" → ROUTES.SIGNUP
- Error display: Kira-voiced error (never raw Supabase error strings)

**Error mapping:**
```
'Invalid login credentials' → "That email or password isn't right. Try again."
'Email not confirmed'       → "Check your email — you've got a confirmation waiting."
Any other error             → KIRA_ERROR_MESSAGES.UNKNOWN
```

**On success:** router.push(ROUTES.ONBOARDING) — always go to onboarding to check if complete

**Must NOT render:** raw Supabase error messages, "auth/..." error codes

---

### `features/onboarding/components/SignupForm.tsx`

`'use client'`

**Props:** none

**Renders:** (same structure as LoginForm with differences:)
- Title: "Create your account"
- Google button: "Continue with Google"
- Email + Password + Confirm Password inputs
- Submit button: "Create account →"
- Footer: "Already have an account? [Sign in]" → ROUTES.LOGIN
- Password requirements: shown inline as user types (8+ chars minimum, shown in font-mono text-[10px])

**Validation (client-side, before API call):**
- Email: basic format check
- Password: min 8 characters
- Confirm password: must match

**On success:** router.push(ROUTES.ONBOARDING)

---

### `app/onboarding/page.tsx`

`'use client'` — needs session check.

**Renders:** `<OnboardingLayout>` containing `<OnboardingStep>` driven by `useOnboarding()`

**On mount:**
1. Check session — if none, redirect to ROUTES.LOGIN
2. Check if user has existing profile in Supabase — if yes, redirect to ROUTES.APP
3. Otherwise, show step 1

**Must NOT:** show any content before session check completes — render a loading state (kira avatar pulsing, no text) until check resolves

---

### `features/onboarding/components/OnboardingLayout.tsx`

`'use client'`

**Props:** `{ children: React.ReactNode; step: number; onSkip: () => void }`

**Renders:**
- Full-screen centered flex column
- Background: `radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.06) 0%, transparent 60%)`
- Top-right: "Skip →" link (font-mono text-[10px] text-text-dim) calls onSkip
- Top-center: `<OnboardingProgress step={step} />`
- Center: Kira avatar (48px, border-kira, bg-[var(--kira-dim)])
- Below avatar: `{children}` (the question + options)

---

### `features/onboarding/components/OnboardingProgress.tsx`

`'use client'`

**Props:** `{ step: number; total?: number }` (default total=3)

**Renders:** Row of `total` dots
- Past steps: `bg-kira opacity-100`
- Current step: `bg-kira opacity-100 shadow-kira` (glow)
- Future steps: `bg-border-strong`
- Size: `w-2 h-2` rounded-full, `gap-2`

---

### `features/onboarding/components/OnboardingStep.tsx`

`'use client'`

**Props:**
```typescript
interface OnboardingStepProps {
  question: typeof ONBOARDING_QUESTIONS[number]
  selectedValues: string[]
  onSelect: (value: string) => void
  onTextChange?: (value: string) => void
  textValue?: string
  onNext: () => void
  isLastStep: boolean
  isLoading: boolean
}
```

**Renders (type='grid'):**
- Question text: 22px, font-bold, text-bright, text-center, max-w-[480px]
- 2-column grid of option cards:
  - Each card: icon + label
  - Selected: `border-kira bg-[var(--kira-glow)] text-text-bright`
  - Unselected: `border-border-strong bg-layer1 text-text-default`
  - Hover: `border-border-bright`

**Renders (type='list'):**
- Single column, full-width option cards
- Same selection styling

**Renders (type='chips'):**
- Wrapped flex row of chips
- Multi-select (toggle each)
- If `hasTextFallback=true`: text input below chips
- Placeholder from `question.textPlaceholder`

**Next button:**
- `Button variant="primary" size="lg"` centered below options
- isLastStep=false: "Continue →"
- isLastStep=true: "Let's go →"
- Disabled until at least one option selected (or text input has value for chips)
- Shows spinner when `isLoading=true`

**Must NOT render:** progress dots (those are in OnboardingLayout), skip button (in layout)

---

## 4. HOOK CONTRACTS

### `features/onboarding/hooks/useAuth.ts`

```typescript
// 'use client'
// Input: none
// Return: {
//   signInWithGoogle: () => Promise<void>
//   signInWithEmail: (email: string, password: string) => Promise<{ error: string | null }>
//   signUpWithEmail: (email: string, password: string) => Promise<{ error: string | null }>
//   isLoading: boolean
// }
// Side effects:
//   - signInWithGoogle: calls supabase.auth.signInWithOAuth, redirects via Supabase
//   - signInWithEmail: calls supabase.auth.signInWithPassword
//   - signUpWithEmail: calls supabase.auth.signUp
//   - All Supabase errors mapped through local error mapper (not lib/errors.ts — different surface)
// Cleanup: none
// Must NOT: store JWT manually — Supabase Auth JS manages tokens
```

---

### `features/onboarding/hooks/useOnboarding.ts`

```typescript
// 'use client'
// Input: none
// Return: {
//   step: number                         // 0-indexed, 0 = first question
//   answers: Record<string, string[]>    // { primary_use: ['Writing'], audience: [...] }
//   textAnswers: Record<string, string>  // { ai_frustration: "my own words..." }
//   selectOption: (questionId: string, value: string) => void
//   setTextAnswer: (questionId: string, value: string) => void
//   canProceed: boolean                  // true if current question has answer
//   goNext: () => void                   // advance step or submit if last
//   skip: () => void                     // skip all, go directly to /app
//   isSubmitting: boolean
//   error: string | null
// }
// Side effects:
//   - goNext() on last step: calls apiSaveProfile() then router.push(ROUTES.APP)
//   - skip(): router.push(ROUTES.APP) immediately, no profile save
//   - Profile constructed from answers:
//       primary_use: answers.primary_use[0] ?? 'other'
//       audience: answers.audience[0] ?? 'both'
//       ai_frustration: answers.ai_frustration.join(', ')
//       frustration_detail: textAnswers.ai_frustration ?? ''
// Cleanup: none
// Error: mapped to Kira voice (profile save fail is non-fatal — still navigates to /app)
```

---

## 5. API INTEGRATION

### Profile save — `apiSaveProfile()`

```typescript
// Called by useOnboarding.goNext() on step 3
// Endpoint: POST /user/profile
// Request: UserProfile { primary_use, audience, ai_frustration, frustration_detail? }
// Auth: getAccessToken() from lib/supabase.ts
// On success: router.push(ROUTES.APP)
// On error: log error, still navigate to /app (profile save is non-fatal)
//           user can always update profile later
//           DO NOT block navigation on profile save failure
```

### Supabase Auth — NOT through lib/api.ts

Auth calls go directly through `@supabase/ssr` — that's their job. Only backend API calls go through `lib/api.ts`.

---

## 6a. BUILD ORDER — AGENT FOLLOWS THIS SEQUENCE EXACTLY

Plan 3 has auth + onboarding tightly coupled. Build in this order. Run `npx tsc --noEmit` after each step. Do not proceed if TypeScript errors exist.

```
STEP 3.1 — lib/auth.ts
  Build: signInWithGoogle, signInWithEmail, signUpWithEmail, requireAuth, getSessionOrRedirect
  Verify: tsc clean. No browser APIs outside functions.

STEP 3.2 — app/auth/callback/route.ts
  Build: GET handler, code exchange, redirect to /onboarding
  Verify: tsc clean. File is a Route Handler (no 'use client').

STEP 3.3 — features/onboarding/components/AuthLeftPanel.tsx
  Build: static left panel, both variants (login/signup)
  Verify: tsc clean. No hooks, no state, no 'use client'. Pure JSX.

STEP 3.4 — app/(auth)/layout.tsx + app/(auth)/login/page.tsx + app/(auth)/signup/page.tsx
  Build: two-column layout shell + page stubs that import AuthLeftPanel
  Verify: npm run dev → /login and /signup load without crash

STEP 3.5 — features/onboarding/hooks/useAuth.ts
  Build: hook wrapping Supabase auth calls
  Verify: tsc clean. No direct Supabase calls in components yet.

STEP 3.6 — features/onboarding/components/LoginForm.tsx
  Build: Google button + email/password form using useAuth
  Verify: tsc clean. Error messages use only KIRA_ERROR_MESSAGES strings.

STEP 3.7 — features/onboarding/components/SignupForm.tsx
  Build: same structure as LoginForm with confirm password
  Verify: tsc clean.

STEP 3.8 — features/onboarding/components/OnboardingProgress.tsx + OnboardingLayout.tsx
  Build: progress dots + full-screen layout wrapper
  Verify: tsc clean.

STEP 3.9 — features/onboarding/hooks/useOnboarding.ts
  Build: step state, answer collection, submit with apiSaveProfile
  Verify: tsc clean. Return type matches contract exactly.

STEP 3.10 — features/onboarding/components/OnboardingStep.tsx
  Build: renders grid/list/chips question types from ONBOARDING_QUESTIONS
  Verify: tsc clean. Uses types from lib/types.ts.

STEP 3.11 — app/onboarding/page.tsx
  Build: assembles layout + step + progress using useOnboarding
  Verify: tsc clean. Session check present. Loading state before redirect.

STEP 3.12 — bash verify.sh
  Expected: ALL CHECKS PASSED ✅
```



### Auth pages — left panel
- Arch background grid: `repeating-linear-gradient(0deg, var(--kira) 0px, var(--kira) 1px, transparent 1px, transparent 40px), repeating-linear-gradient(90deg, ...)` at 3% opacity
- Kira quote block: `rounded-xl p-3.5 bg-[var(--kira-glow)] border border-[var(--kira-dim)]`
- Quote text: 13px, italic, text-default

### Auth forms — right panel
- Title: 20px, font-bold, text-bright, margin-bottom 24px
- Google button: full-width, `bg-layer2 border-border-strong` with hover `border-border-bright`
- Google SVG: inline, 16px, no external image (copy SVG paths directly into component)
- Form spacing: 10px gap between inputs
- Error: `font-mono text-[11px] text-intent` below the submit button

### Onboarding
- Question text: 22px desktop, 18px mobile, font-bold, text-bright, text-center
- Option cards: `rounded-xl p-4 cursor-pointer transition-all duration-150`
- Chips: `rounded-full px-3.5 py-1.5 text-[12px] cursor-pointer transition-all duration-150`
- Next button: centered, margin-top 24px
- Skip: `font-mono text-[10px] tracking-wider text-text-dim` absolutely positioned top-right

### Loading state (before session check)
- Show centered Kira avatar (48px) with gentle `opacity` pulse animation
- No text, no logo — just the avatar
- Max 1 second before resolving or redirecting

---

## 7. VERIFICATION CHECKLIST

Before Plan 4 starts, verify ALL of the following. A real test user must exist in the database at the end of this plan.

```bash
# Run from promptforge-web/
bash verify.sh
# Expected: ALL CHECKS PASSED ✅
```

**End-to-end flow (do this manually):**
- [ ] Navigate to `/signup`
- [ ] Sign up with email — see left panel with Kira quote
- [ ] Form validates: email format, password 8+ chars, passwords match
- [ ] On success → redirects to `/onboarding`
- [ ] Onboarding screen 1 loads with question and options
- [ ] Select an option, "Continue →" becomes active
- [ ] Advance through all 3 steps
- [ ] Step 3 "Let's go →" submits profile and redirects to `/app` (404 is fine)
- [ ] Navigate to `/signup` again — Google OAuth button visible
- [ ] Navigate to `/login` — works, same left panel with different copy
- [ ] Navigate to `/onboarding` without session — redirects to `/login`
- [ ] After completing onboarding, navigate to `/onboarding` again — redirects to `/app`
- [ ] Skip button on step 2 → goes directly to `/app` without saving profile
- [ ] No raw Supabase errors ever visible ("auth/...", "JWT", "postgres")
- [ ] Google OAuth button opens Google consent screen (if configured)

**Database verification:**
```sql
-- Run in Supabase SQL editor after completing flow
SELECT * FROM auth.users ORDER BY created_at DESC LIMIT 1;
-- Expected: your test user

SELECT * FROM user_profiles ORDER BY created_at DESC LIMIT 1;
-- Expected: row with primary_use, audience, ai_frustration populated
```

**Test user for Plan 4:**
- Email: any test email you used
- Password: saved somewhere accessible
- Profile: at minimum `primary_use` and `audience` filled
- This user will be used to develop and test Plan 4

---

## 8. HANDOFF TO PLAN 4

Plan 4 depends on ALL of the following:

```typescript
// From lib/types.ts (Plan 1)
import type { ChatMessage, ProcessingStatus, PersonaDotState, TrustLevel } from '@/lib/types'

// From lib/env.ts (Plan 1)
import { ENV } from '@/lib/env'

// From lib/mocks.ts (Plan 1)
import { MOCK_CHAT_RESULT, MOCK_HISTORY, MOCK_PROFILE, MOCK_SSE_SEQUENCE } from '@/lib/mocks'

// From lib/auth.ts (this plan)
import { getSessionOrRedirect } from '@/lib/auth'

// From lib/supabase.ts (Plan 1)
import { getSupabaseClient, getAccessToken } from '@/lib/supabase'

// From lib/api.ts (Plan 1)
import { apiChat, apiHistory, apiConversation, apiTranscribe } from '@/lib/api'
import type { ChatResult, HistoryItem, DiffItem, QualityScore } from '@/lib/api'

// From lib/stream.ts (Plan 1)
import { parseStream } from '@/lib/stream'
import type { StreamCallbacks } from '@/lib/stream'

// From lib/errors.ts (Plan 1)
import { mapError } from '@/lib/errors'

// From lib/constants.ts (Plan 1)
import { ROUTES, LIMITS, PERSONA_DOT_THRESHOLDS } from '@/lib/constants'

// From components/ui (Plan 1)
import { Button, Input, Chip } from '@/components/ui'
```

**Test user state Plan 4 inherits:**
- Valid Supabase session (JWT in Supabase Auth JS storage)
- `user_profiles` row exists for the user
- User can call `getAccessToken()` and get a valid JWT
- `apiChat()` with this token returns real results from the backend
- `ENV.USE_MOCKS=true` → full UI works without backend (agent development mode)
- `ENV.USE_MOCKS=false` → real backend verification (your final gate)
- Session count: 0 (fresh user — green dot won't appear until session 30)

---

*Plan 3 complete. Verify test user exists in database before starting Plan 4.*
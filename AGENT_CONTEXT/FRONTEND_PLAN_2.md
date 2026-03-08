# FRONTEND PLAN 2 — Landing Page
### PromptForge v2.0 · app/(marketing)/ · features/landing/
---

## 1. CONTEXT

### What's already built (from Plan 1)
- `styles/globals.css` — all design tokens, `.reveal` animation classes, `.gradient-text`
- `lib/constants.ts` — `ROUTES`, `LIMITS`, `LIMITS.DEMO_MAX_USES = 3`, `LIMITS.DEMO_STORAGE_KEY`
- `lib/api.ts` — `apiDemoChat()`, `ApiError`, `ChatResult` type
- `lib/errors.ts` — `mapError()`
- `components/ui/` — `Button`, `Input`, `Chip`
- `tailwind.config.ts` — all color tokens

### What this plan assumes is working
- Plan 1 verification checklist passed (0 TypeScript errors)
- `promptforge-web/` has Next.js App Router scaffolded
- `.env.local` has `NEXT_PUBLIC_DEMO_API_URL`

### What this plan must NOT touch
- `promptforge/` backend directory
- `lib/*`, `components/ui/*`, `styles/globals.css` — read only
- `app/(auth)/`, `app/onboarding/`, `app/app/` — don't create yet
- Any Supabase auth logic

### This plan is fully shippable
The landing page works independently. No auth, no session. The live demo uses `apiDemoChat()` with localStorage rate limiting. Can be deployed to Vercel before Plans 3 and 4 exist.

---

## 2. FILES TO CREATE

```
promptforge-web/
├── app/
│   ├── layout.tsx                          ← Root layout (fonts, metadata, globals.css import)
│   └── (marketing)/
│       ├── layout.tsx                      ← Marketing layout (no auth wrapper)
│       └── page.tsx                        ← Landing page — server component, imports sections
├── features/
│   └── landing/
│       ├── components/
│       │   ├── LandingNav.tsx              ← Top nav with logo + CTAs
│       │   ├── HeroSection.tsx             ← Headline + sub + CTAs + LiveDemo window
│       │   ├── LiveDemoWidget.tsx          ← Interactive demo with gate logic
│       │   ├── KiraVoiceSection.tsx        ← 3-card voice progression slider
│       │   ├── HowItWorksSection.tsx       ← 5-step pipeline with agent chips
│       │   ├── MoatSection.tsx             ← Profile accumulation bars
│       │   ├── PricingSection.tsx          ← Free + Pro cards with waitlist
│       │   └── LandingFooter.tsx           ← Simple footer
│       └── hooks/
│           ├── useScrollReveal.ts          ← IntersectionObserver for .reveal elements
│           └── useDemoGate.ts              ← localStorage demo use counter
```

---

## 3. COMPONENT CONTRACTS

---

### `app/layout.tsx`

Root layout. Server component.

```typescript
// Props: { children: React.ReactNode }
// Renders: <html> with lang="en", body with globals.css, children
// Must NOT: add any auth providers here (that's app/app/layout.tsx)
// Must import: '@/styles/globals.css'
// Metadata: title "PromptForge — Prompt intelligence for serious work"
//           description "Kira learns how you think. Every session, your prompts get sharper."
```

---

### `app/(marketing)/page.tsx`

Landing page. **Server component** — no `'use client'`.

```typescript
// Props: none
// Renders: LandingNav + HeroSection + KiraVoiceSection + HowItWorksSection
//          + MoatSection + PricingSection + LandingFooter
// Must NOT: import any hook, useState, useEffect — server component
// Must NOT: contain any 'use client' directive
// Each section wrapped in <section> with id for anchor links
```

---

### `features/landing/components/LandingNav.tsx`

`'use client'` — handles scroll state for transparent→frosted transition.

**Props:** none

**Renders:**
- Logo mark (⬡ + "PromptForge")
- Nav links: "How it works" (→ #how-it-works), "Pricing" (→ #pricing)
- CTAs: ghost "Sign in" (→ ROUTES.LOGIN), primary "Start free →" (→ ROUTES.SIGNUP)
- On scroll > 40px: `backdrop-blur-md bg-bg/90 border-b border-border-subtle`
- At top: fully transparent

**Must NOT render:** any user data, session info, avatar

**Mobile:** hamburger menu below `md:` breakpoint, drawer slides from right

---

### `features/landing/components/HeroSection.tsx`

`'use client'` — contains LiveDemoWidget.

**Props:** none

**Renders:**
1. Eyebrow: `// the prompt intelligence layer` (font-mono, text-kira)
2. H1: `Your prompts,` (line break) `<em class="gradient-text">precisely</em> engineered.`
   - 56px desktop, 36px mobile, font-weight 700, letter-spacing -2px
3. Sub: `Kira learns how you think. The more you use it, the better it serves you. Switching away means starting over.`
4. CTAs row: `Button variant="primary" size="lg"` "Start for free" → ROUTES.SIGNUP, `Button variant="ghost" size="lg"` "Watch it work ↓" scrolls to #live-demo
5. `<LiveDemoWidget />`

**Background:**
```css
background:
  radial-gradient(ellipse 70% 50% at 15% 0%, rgba(99,102,241,0.10) 0%, transparent 60%),
  radial-gradient(ellipse 50% 40% at 85% 100%, rgba(139,92,246,0.07) 0%, transparent 60%),
  radial-gradient(ellipse 30% 30% at 5% 60%, rgba(236,72,153,0.04) 0%, transparent 50%);
```

**Must NOT render:** agent names (intent/context/domain/engineer), model names

**Mobile:** H1 36px, sub 15px, CTAs stack vertically, LiveDemo below CTAs

---

### `features/landing/components/LiveDemoWidget.tsx`

`'use client'` — the most complex component in Plan 2.

**Props:** none

**State machine:**
```
IDLE       → user has uses remaining, input active
LOADING    → API call in flight, chips animating
RESULT     → output card showing
GATED      → uses >= LIMITS.DEMO_MAX_USES, overlay showing
```

**Uses:**
- `useDemoGate()` hook for use counter
- `apiDemoChat()` from lib/api.ts
- `mapError()` from lib/errors.ts

**Renders (IDLE state):**
- Window chrome: label "Live demo", green live dot with `live-pulse` animation
- Demo badge: "LIVE · REAL BACKEND · REAL KIRA"
- Input field + send button
- Placeholder: "Try: 'help me write an email to my client'"

**Renders (LOADING state):**
- Chips row: Kira (active pulse) → intent (active) → context (skipped) → domain (active) → engineer (active)
- Chips use `<Chip>` component from `@/components/ui`
- Status text below chips: e.g. "Analyzing intent..."
- Input disabled

**Renders (RESULT state):**
- Kira message line with avatar K + text from API result
- Output card:
  - Header: "Engineered prompt" label + memory badge (if memories_applied > 0 use `--memory` color) + latency in `--teal`
  - Body: improved_prompt text in `--output-text` color
  - Diff row (toggle off by default): diff items colored context/intent
  - Annotation chips derived from diff
  - Quality scores: 3 bars (specificity, clarity, actionability) with `--kira` fill
  - Actions: "Copy" (copies to clipboard), "Try it yourself →" (→ ROUTES.SIGNUP)
- NO "Push Further" button — that's Pro only and not shown in demo
- Diff toggle: off by default, label "Show diff"

**Renders (GATED state):**
```
Overlay (absolute, inset-0, blur background slightly):
  Kira avatar K
  "You've seen what I can do."
  "Sign up to keep going — it's free."
  Button primary "Create free account →" → ROUTES.SIGNUP
  Button ghost "Sign in" → ROUTES.LOGIN
```

**Error handling:**
- All errors → `mapError()` → Kira's voice message
- Input preserved on error
- "Try again" button visible

**Must NOT render:**
- Agent names (intent/context/domain/engineer) — chips show human-readable labels:
  - intent chip → label: "Reading intent"
  - context chip → label: "Context" (skipped = "No session yet")
  - domain chip → label: "Domain"
  - engineer chip → label: "Crafting prompt"
- Model names (GPT-4o, GPT-4o-mini)
- Session IDs
- Raw API errors

**Scripted fallback:**
If `apiDemoChat()` fails AND result is not cached, show a scripted static result:
```typescript
const FALLBACK_RESULT = {
  kira_message: "On it. Here's your engineered prompt ↓",
  improved_prompt: "Write a professional email to [client name] regarding [project name]. Tone: confident and clear. Include: what was accomplished, what it means for the timeline, and a clear next step. Length: under 200 words.",
  diff: [
    { type: 'add', text: '[client name]' },
    { type: 'add', text: '[project name]' },
    { type: 'add', text: 'confident and clear' },
    { type: 'add', text: 'Length: under 200 words.' },
    { type: 'remove', text: 'your project' },
  ],
  quality_score: { specificity: 4, clarity: 5, actionability: 3 },
  memories_applied: 0,
  latency_ms: 2800,
  agents_run: [],
}
```

**Mobile:** full width, input + button stack, chips wrap, output card full width

---

### `features/landing/components/KiraVoiceSection.tsx`

`'use client'` — card selection state.

**Props:** none

**Renders:**
- Section eyebrow: `// 02  Meet Kira`
- Title: `Not a chatbot.` (line break) `A collaborator that learns your voice.`
- Sub: `The same prompt. Three different stages. Same personality — different depth.`
- 3 cards (grid, 3 columns desktop / 1 column mobile):

```
Card 1: SESSION 1
  Dot: --dot-cold (grey #475569)
  Label: "● GREY — Cold" (text-dim)
  Quote: "Before I engineer this — what's the context? A project update,
          a performance conversation, or something else?"

Card 2: SESSION 15 (default active)
  Dot: --dot-warm (amber #f59e0b)
  Label: "● AMBER — Warm" (domain color)
  Quote: "Running it as internal comms — that's your pattern.
          Project update or something higher stakes?"

Card 3: SESSION 40+
  Dot: --dot-tuned (green #22c55e)
  Label: "● GREEN — Tuned" (success color)
  Quote: "On it. B2B SaaS internal update — your usual territory.
          Your specificity has been sharp lately, keeping this tight."
```

- Active card: `border-kira bg-[var(--kira-glow)]`
- Inactive card: `border-border-default bg-layer1`
- Click any card to activate it
- Footnote: `"She reads your profile before every response. The more you use it, the less you explain."`

**Must NOT render:** technical explanation of how memory works

---

### `features/landing/components/HowItWorksSection.tsx`

Server component — no state needed.

**Props:** none

**Renders:**
- Eyebrow: `// 03  How it works`
- Title: `Five steps. Four seconds.`
- Sub: `Honest about latency. Transparent about depth.`
- 5 steps as vertical list, each separated by border:

```
01  [Kira chip]                  Reads your message + profile
                                 One fast call. Decides what's needed.

02  [Intent][Context][Domain]    Three specialists, in parallel
     chips side by side          Some skip if Kira already knows your domain.
                                 Note: "Gets faster as Kira learns you"

03  [Engineer chip]              Prompt Engineer synthesizes everything
                                 All signals combined into one precise output.

04  (no chip)                    You see exactly what changed and why
                                 Diff view. Quality scores. Annotation chips.

05  (no chip)                    Kira remembers. Next time is faster.
                                 Profile dot moves grey → amber → green.
```

Chips use human-readable labels matching LiveDemoWidget (not agent variable names).

**`reveal` classes:** each step gets `.reveal .reveal-delay-N` for staggered entrance

---

### `features/landing/components/MoatSection.tsx`

Server component.

**Props:** none

**Renders:**
- Eyebrow: `// 04  The moat`
- Title: `The longer you use it,` (line break) `the more it costs to leave.`
- Card with 4 progress rows:
  ```
  Domain confidence      ████████████░  B2B SaaS — 91%      color: --kira
  Tone calibration       ██████████░░░  Direct, technical    color: --context
  Quality trend          █████████░░░░  ↑ 34% this month     color: --success
  Clarification rate     ██░░░░░░░░░░░  Rarely needs more    color: --domain
  ```
- Footer: `This lives in your profile.` **`Switching away means starting over.`**

**`reveal` classes** on the card

---

### `features/landing/components/PricingSection.tsx`

Server component.

**Props:** none

**Renders:**
- Eyebrow: `// 05  Pricing`
- Title: `Simple. Honest. Free tier is real.`
- 2-column grid (stack on mobile):

**FREE card:**
```
Label: FREE
Price: $0
Features:
  • Unlimited prompt improvement
  • Kira orchestration
  • Quality scoring
  • Profile building
  • Basic memory
Button: variant="primary" size="lg" → ROUTES.SIGNUP  "Start free"
Note: "No credit card. Genuinely useful."
```

**PRO card** (border-kira, bg-[var(--kira-glow)]):
```
Corner badge: "COMING SOON" — amber, font-mono, absolute top-right
              bg-[var(--coming-dim)] border border-[var(--coming)] text-[var(--coming)]

Label: PRO
Price: $20 /month (dimmed)
       "Coming soon" in small text below price

Features:
  • Everything in Free
  • Prompt history library
  • MCP (Cursor / Claude Desktop)
  • Push Further variants ✦
  • Full profile depth
  • Priority queue

Button: variant="waitlist" size="lg" full-width
        "Join Pro waitlist →"
        → links to a Tally or Typeform waitlist form (URL TBD — use "#waitlist" placeholder)

Note: "Free forever until Pro launches."
```

**Must NOT render:** any implication that free features are limited. They aren't.

---

### `features/landing/components/LandingFooter.tsx`

Server component.

**Props:** none

**Renders:**
- Logo + "PromptForge"
- Two link groups: Product (How it works, Pricing), Legal (Privacy, Terms) — all `href="#"` for now
- Copyright: `© 2026 PromptForge`
- All in muted text, minimal

---

## 4. HOOK CONTRACTS

### `features/landing/hooks/useScrollReveal.ts`

```typescript
// Input: none
// Return: void (side effect only)
// Side effect:
//   - On mount: creates IntersectionObserver (threshold: 0.15)
//   - Observes all elements with class .reveal in the document
//   - When element enters viewport: adds class .visible
//   - On unmount: disconnects observer
// Cleanup: disconnect() on unmount
// Must NOT: use scroll event listeners
// Must: check typeof window !== 'undefined' before running (SSR safe)
// Must: respect prefers-reduced-motion (if reduced, add .visible to all immediately)
```

**Implementation:**
```typescript
'use client'
import { useEffect } from 'react'

export function useScrollReveal() {
  useEffect(() => {
    if (typeof window === 'undefined') return

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
            observer.unobserve(entry.target)  // fire once only
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

---

### `features/landing/hooks/useDemoGate.ts`

```typescript
// Input: none
// Return: {
//   usesRemaining: number,       // LIMITS.DEMO_MAX_USES - uses so far
//   isGated: boolean,            // true when usesRemaining <= 0
//   recordUse: () => void,       // call AFTER successful demo result
// }
// Side effects:
//   - Reads localStorage[LIMITS.DEMO_STORAGE_KEY] on mount
//   - recordUse() increments localStorage counter
// Cleanup: none
// Must NOT: throw if localStorage unavailable (try/catch, fallback to in-memory)
// Must NOT: gate users who are already logged in
```

---

## 5. API INTEGRATION

### `apiDemoChat()` — used by LiveDemoWidget

```typescript
// Endpoint: POST /chat (demo account JWT pre-loaded on backend)
// Request: { message: string, session_id: 'demo-session', demo: true }
// Response: ChatResult
// Error handling:
//   - ApiError 429 → show FALLBACK_RESULT (not an error state — just use fallback)
//   - ApiError 5xx → show FALLBACK_RESULT
//   - Network error → show FALLBACK_RESULT
//   - All errors logged to console, never shown raw to user
// Rate limit: 3 uses via useDemoGate, backend enforces 50 req/hour on demo account
```

---

## 6. DESIGN RULES

### Scroll reveal
- Every section heading, every card, every step row gets `.reveal`
- Stagger within a section using `.reveal-delay-1` through `.reveal-delay-4`
- Hero content does NOT use reveal (it should be visible immediately on load)
- LiveDemoWidget does NOT use reveal (it's above the fold)

### Hero gradient background
Applied via `style` prop on the hero section div:
```typescript
style={{
  background: `
    radial-gradient(ellipse 70% 50% at 15% 0%, rgba(99,102,241,0.10) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 85% 100%, rgba(139,92,246,0.07) 0%, transparent 60%),
    radial-gradient(ellipse 30% 30% at 5% 60%, rgba(236,72,153,0.04) 0%, transparent 50%)
  `
}}
```

### Typography rules for this plan
- `font-mono text-kira tracking-[3px] uppercase text-[10px]` → all eyebrows
- `text-[56px] md:text-[56px] text-[36px] font-bold tracking-tight text-text-bright leading-[1.05]` → H1
- `text-[17px] text-text-dim font-light leading-[1.7]` → hero sub
- `text-[28px] font-bold tracking-tight text-text-bright` → section titles
- `text-[13px] text-text-dim` → all section body text
- `font-mono text-[11px] text-text-dim` → all metadata, notes, latency

### Colors on landing — strict
- Kira avatar = `border-kira bg-[var(--kira-dim)] text-kira`
- Live dot = `bg-success` with `live-pulse` animation
- Memory badge = `text-memory`
- Latency "3.4s" = `text-teal font-mono text-[10px]`
- Pro "COMING SOON" badge = amber
- Diff additions = context color
- Diff removals = intent color (line-through)
- Quality bar fill = kira
- Score values = font-mono

### Section spacing
- Section padding: `py-16 px-12` desktop, `py-12 px-6` mobile
- Between sections: `border-t border-border-subtle`
- Max content width: `max-w-4xl` for text, `max-w-2xl` for prose

---

## 6a. BUILD ORDER — AGENT FOLLOWS THIS SEQUENCE EXACTLY

Landing page has no auth, no hooks, no state machine. Simpler than Plans 3/4 but still build one file at a time to keep tsc clean throughout.

```
STEP 2.1 — app/layout.tsx (root layout)
  Build: html/body shell, globals.css import, font meta tags
  Verify: tsc clean. No 'use client'. No fetch().

STEP 2.2 — app/(marketing)/layout.tsx
  Build: marketing route group layout (transparent, no nav chrome)
  Verify: tsc clean. No 'use client'.

STEP 2.3 — features/landing/hooks/useScrollReveal.ts
  Build: IntersectionObserver adding .visible to .reveal elements
  Verify: tsc clean. typeof window guard present.

STEP 2.4 — features/landing/hooks/useDemoGate.ts
  Build: localStorage counter, 3-use limit, gated state
  Verify: tsc clean. try/catch around localStorage. Fallback to in-memory if unavailable.

STEP 2.5 — components/ui shared (already built in Plan 1 — verify imports resolve)
  Verify: import { Button } from '@/components/ui' resolves with no error.

STEP 2.6 — features/landing/components/LandingNav.tsx
  Build: logo, CTAs, scroll-aware border
  Verify: tsc clean. 'use client' present. No fetch().

STEP 2.7 — features/landing/components/HeroSection.tsx
  Build: headline, subhead, CTAs, gradient text
  Verify: tsc clean. Uses .reveal class. No 'use client' needed (no state).

STEP 2.8 — features/landing/components/LiveDemoWidget.tsx
  Build: demo input, mock/real toggle, FALLBACK_RESULT, gate overlay
  Verify: tsc clean. useDemoGate wired. FALLBACK_RESULT present for offline. apiDemoChat called.
  Gate test: manually increment pf_demo_uses to 3 in DevTools → overlay appears.

STEP 2.9 — features/landing/components/KiraVoiceSection.tsx
  Build: 3 session persona cards
  Verify: tsc clean. No agent names in card copy.

STEP 2.10 — features/landing/components/HowItWorksSection.tsx
  Build: 5-step flow
  Verify: tsc clean.

STEP 2.11 — features/landing/components/MoatSection.tsx
  Build: profile bars animation, session counter
  Verify: tsc clean.

STEP 2.12 — features/landing/components/PricingSection.tsx
  Build: Free card + Pro COMING SOON card, waitlist button
  Verify: tsc clean. Pro card has "COMING SOON" badge. No Stripe code. No payment processing.

STEP 2.13 — features/landing/components/LandingFooter.tsx
  Build: footer links, legal line
  Verify: tsc clean.

STEP 2.14 — app/(marketing)/page.tsx
  Build: assembles all section components
  Verify: tsc clean. No 'use client'. Server component.

STEP 2.15 — bash verify.sh
  Expected: ALL CHECKS PASSED ✅
  Then: npm run dev → visit localhost:3000 → full page renders
```

---

## 7. VERIFICATION CHECKLIST

Before Plan 3 starts, verify ALL of the following:

```bash
# Run from promptforge-web/
bash verify.sh
# Expected: ALL CHECKS PASSED ✅
```

**Functionality:**
- [ ] Landing page loads at `localhost:3000`
- [ ] "Start free" → navigates to `/signup` (404 is fine, page doesn't exist yet)
- [ ] "Sign in" → navigates to `/login` (404 is fine)
- [ ] Demo input accepts text and submits on Enter or button click
- [ ] Demo chips animate during loading state
- [ ] Demo result shows output card with quality bars
- [ ] Demo diff toggle works (off by default, toggles on click)
- [ ] Copy button copies improved_prompt to clipboard
- [ ] After 3 uses, gated overlay appears
- [ ] Gated overlay has "Create free account →" and "Sign in" links
- [ ] KiraVoice cards toggle on click, Card 2 active by default
- [ ] Scroll reveals work (sections fade in as you scroll)
- [ ] "How it works" steps stagger in one by one
- [ ] Pro card shows "COMING SOON" badge
- [ ] Pro button says "Join Pro waitlist →"
- [ ] Free button says "Start free"
- [ ] No agent names (intent/context/domain/engineer) visible anywhere in UI text
- [ ] No model names (GPT-4o, GPT-4o-mini) visible anywhere
- [ ] No raw error strings visible (test by breaking DEMO_API_URL — should show Kira's message + fallback)
- [ ] Mobile: nav collapses, hero text legible, demo widget full width
- [ ] Fallback result displays when backend unreachable

---

## 8. HANDOFF TO PLAN 3

Plan 3 depends on these exact exports:

```typescript
// From lib/types.ts (Plan 1)
import type { OnboardingQuestionType } from '@/lib/types'

// From lib/env.ts (Plan 1)
import { ENV } from '@/lib/env'

// From lib/supabase.ts (Plan 1)
import { getSupabaseClient, getSession } from '@/lib/supabase'

// From lib/constants.ts (Plan 1)
import { ROUTES, ONBOARDING_QUESTIONS, LIMITS } from '@/lib/constants'

// From lib/api.ts (Plan 1)
import { apiSaveProfile } from '@/lib/api'
import type { UserProfile } from '@/lib/api'

// From components/ui (Plan 1)
import { Button, Input } from '@/components/ui'
```

**User state Plan 3 starts with:**
- No authenticated user (Plan 2 has no auth)
- Supabase project is live with auth enabled
- Google OAuth configured in Supabase dashboard
- After Plan 3 completes: user exists in `auth.users`, profile saved to `user_profiles` table, session active, redirect to `/app`

---

*Plan 2 complete. Verify build passes, demo works 3x then gates, before starting Plan 3.*
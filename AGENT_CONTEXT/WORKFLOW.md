# PromptForge Frontend — Agent Workflow
### How to run every coding session. Read before starting any plan.
---

## WHAT THIS FILE IS

This is the operational guide for building the frontend with an AI coding agent.
The 4 Plan files tell the agent WHAT to build.
The FRONTEND_RULES.md tells the agent HOW to build it.
This file tells YOU how to run the agent sessions so nothing goes wrong.

---

## THE FIVE FILES IN THIS FOLDER

```
AGENT_CONTEXT/
├── FRONTEND_RULES.md   ← Agent reads this first, every session
├── FRONTEND_PLAN_1.md  ← Foundation + Design System
├── FRONTEND_PLAN_2.md  ← Landing Page
├── FRONTEND_PLAN_3.md  ← Auth + Onboarding
├── FRONTEND_PLAN_4.md  ← Core App (Chat, History, Profile)
└── WORKFLOW.md         ← This file — you read this, not the agent
```

Feed the agent: FRONTEND_RULES.md + the relevant Plan file + the Session Brief below.
Do NOT feed the agent WORKFLOW.md — it's for you.

---

## SESSION BRIEF TEMPLATE

Fill this in before every single agent session. Takes 5 minutes. Prevents 3-hour debugging sessions.
Paste it AFTER pasting FRONTEND_RULES.md and the Plan file.

```
## SESSION BRIEF — PROMPTFORGE FRONTEND

**Current plan:** Plan [N] — [Plan name]
**Current step:** Step [X.Y] — [e.g. "Step 4.5 — useKiraStream.ts"]

**Files already built — DO NOT regenerate these:**
[paste output of: find promptforge-web/src -name "*.ts" -o -name "*.tsx" | grep -v node_modules | sort]
If nothing built yet: "None — this is the first session for this plan."

**Last TypeScript result:**
[paste output of: npx tsc --noEmit]
If first session: "Not run yet."

**Your task this session:**
Build exactly: [filename(s)] as specified in FRONTEND_PLAN_[N].md Step [X.Y].

**When you finish each file:**
Run: npx tsc --noEmit
Fix any errors before moving to the next file.
Do NOT move on with TypeScript errors outstanding.

**When you finish all files in this step:**
Run: bash verify.sh
Report the output to me before declaring the step done.

**Strict boundaries:**
- Touch ONLY the files listed in your task above
- Do NOT modify anything in promptforge/ (backend — read only forever)
- Do NOT modify lib/*, components/ui/*, styles/globals.css unless this step explicitly says to
- Do NOT add packages to package.json without telling me first
- Do NOT use any library not already in package.json

**If you are unsure about anything:**
Stop. Ask one specific question. Do not guess and continue.
```

---

## GIT BRANCHING STRATEGY

Simple. One rule: main is always deployable.

```
main                    ← always deployable, always passing verify.sh
  └── plan-1            ← branch for Plan 1
  └── plan-2            ← branch for Plan 2
  └── plan-3            ← branch for Plan 3
  └── plan-4            ← branch for Plan 4
        └── plan-4-kira-stream   ← step branch if a step is complex
```

### Commands

```bash
# Start a plan
git checkout main
git pull
git checkout -b plan-1

# Commit after each verified step
git add .
git commit -m "Plan 1 Step 1.3 — lib/supabase.ts ✅ tsc clean"

# Merge a completed plan to main
git checkout main
git merge plan-1 --no-ff -m "Plan 1 complete — Foundation + Design System ✅"
git push

# Start a step branch when a step is risky (optional)
git checkout -b plan-4-kira-stream
# build useKiraStream.ts, verify
git checkout plan-4
git merge plan-4-kira-stream --no-ff
```

### Commit Message Format

```
Plan [N] Step [X.Y] — [filename] ✅ tsc clean
Plan [N] Step [X.Y] — [filename] ✅ verify.sh passed
Plan [N] complete — [Plan name] ✅
```

### When to Use Step Branches

Only for Step 4.5 (useKiraStream) and Step 4.16 (app/app/layout.tsx auth gate).
These are the two steps most likely to need rollback if something goes wrong.
Everything else is safe to commit directly to the plan branch.

---

## HOW TO CORRECT THE AGENT WHEN IT IS WRONG

Do not say "fix this." That gives the agent unlimited latitude and it will change things it shouldn't.

Use this exact template:

```
The error is:
[paste exact error message or describe exact wrong behaviour]

The file with the problem is:
[exact filename]

The spec says this file should:
[paste the exact section from the relevant Plan file]

Fix ONLY [filename] to match the spec.
Do not change any other file.
Run npx tsc --noEmit after your fix and show me the output.
```

### Common agent mistakes and how to handle them:

**Agent adds a library that's not in package.json:**
"Remove that import. Use only what's already in package.json. The spec does not require [library name]. Implement it with what's available."

**Agent modifies a file it was told not to touch:**
"Revert your changes to [filename]. That file is already built and verified. Your task was [filename] only. Redo the task without touching [filename]."

**Agent invents a type that conflicts with lib/types.ts:**
"This type already exists in lib/types.ts as [TypeName]. Import it from there. Do not redeclare types that already exist in lib/types.ts."

**Agent produces TypeScript errors it can't fix:**
"Stop. Do not continue. The error is: [paste error]. Read the contract for [filename] in [Plan section]. The contract specifies [paste contract]. Implement exactly the contract and nothing more."

**Agent puts 'use client' in a server component:**
"Remove 'use client' from [filename]. This file is in app/(marketing)/ which is a server component route group. See FRONTEND_RULES.md Section 3 Error 1."

**Agent calls fetch() directly in a component:**
"Remove that fetch() call. All backend calls go through lib/api.ts only. See FRONTEND_RULES.md Section 6. Use the apiX() function that already exists there."

---

## THE COMPLETE SESSION WORKFLOW

Run this for every step of every plan:

```
1. YOU    → Fill in Session Brief (5 min)
2. YOU    → Paste: FRONTEND_RULES.md + FRONTEND_PLAN_N.md + Session Brief
3. AGENT  → Reads all three, states what it's building, waits
4. YOU    → Read the agent's plan summary. If wrong, correct it now.
5. YOU    → Say "go"
6. AGENT  → Builds first file
7. AGENT  → Runs: npx tsc --noEmit
8. AGENT  → Reports result to you
9. YOU    → If errors: use "how to correct" template above
           If clean: "continue to next file"
10. Repeat 6-9 for each file in the step
11. AGENT → Runs: bash verify.sh
12. AGENT → Reports full output to you
13. YOU   → If ALL CHECKS PASSED: git commit, start next step
            If anything failed: fix before committing
```

Non-negotiable rules:
- tsc --noEmit after EVERY file, not at the end of the step
- bash verify.sh at the end of EVERY step, not just the last one
- git commit only after verify.sh passes — never commit a broken step
- Never start a new step with TypeScript errors outstanding from the previous step

---

## PLAN GATE CHECKLIST (before merging each plan to main)

### Plan 1 Gate
- [ ] `bash verify.sh` → ALL CHECKS PASSED
- [ ] All 8 lib/ files created and importing correctly
- [ ] All 3 UI components built and exporting correctly
- [ ] `import type { ChatMessage } from '@/lib/types'` resolves
- [ ] `import { logger } from '@/lib/logger'` resolves
- [ ] `import { ENV } from '@/lib/env'` resolves
- [ ] `ENV.USE_MOCKS` works correctly with .env.local flag
- [ ] Merge plan-1 → main

### Plan 2 Gate
- [ ] `bash verify.sh` → ALL CHECKS PASSED
- [ ] Landing page loads at localhost:3000
- [ ] Demo works 3 times then gates (test manually)
- [ ] "Start free" → /signup, "Sign in" → /login
- [ ] Pricing: Pro card has COMING SOON badge, no payment UI
- [ ] No agent names in page source (Cmd+F → "intent", "domain", "GPT")
- [ ] Merge plan-2 → main → deploy to Vercel

### Plan 3 Gate
- [ ] `bash verify.sh` → ALL CHECKS PASSED
- [ ] Signup flow works end to end
- [ ] Test user exists in Supabase auth.users table
- [ ] Test user profile exists in user_profiles table
- [ ] /onboarding without session → redirects to /login
- [ ] No raw Supabase errors ever visible
- [ ] Merge plan-3 → main

### Plan 4 Gate (two phases)
**Phase A — Mock mode (agent verifies):**
- [ ] `NEXT_PUBLIC_USE_MOCKS=true` → full chat flow works with mock data
- [ ] `bash verify.sh` → ALL CHECKS PASSED
- [ ] All mock chips animate in correct sequence
- [ ] Mock output card appears after Kira message
- [ ] No agent names anywhere in DOM

**Phase B — Real backend (you verify):**
- [ ] `NEXT_PUBLIC_USE_MOCKS=false`
- [ ] Full chat flow with real backend SSE
- [ ] Error state: break API URL → Kira's voice, input preserved
- [ ] Security scan: no forbidden strings in rendered DOM
- [ ] Merge plan-4 → main → product is live

---

## QUICK REFERENCE — COMMANDS YOU WILL RUN A LOT

```bash
# TypeScript check (after every file)
npx tsc --noEmit

# Full verification (after every step)
bash verify.sh

# Check what's been built so far
find promptforge-web -name "*.ts" -o -name "*.tsx" | grep -v node_modules | grep -v .next | sort

# Check for forbidden strings in source
grep -r "intent agent\|GPT-4o\|langmem\|fly.dev" promptforge-web/app promptforge-web/features --include="*.tsx" --include="*.ts"

# Dev server
cd promptforge-web && npm run dev

# Build check
cd promptforge-web && npm run build

# Git status
git log --oneline -10
git status
```

---

## ENVIRONMENT FILES REFERENCE

`promptforge-web/.env.local` — never commit this file:
```
NEXT_PUBLIC_SUPABASE_URL=https://cckznjkzsfypssgecyya.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your anon key from Supabase dashboard>
NEXT_PUBLIC_API_URL=https://<your-backend>.up.railway.app
NEXT_PUBLIC_DEMO_API_URL=https://<your-backend>.up.railway.app
NEXT_PUBLIC_USE_MOCKS=false
```

Toggle mock mode:
```bash
# Development without backend (agent sessions)
NEXT_PUBLIC_USE_MOCKS=true

# Real verification (your final gate per plan)
NEXT_PUBLIC_USE_MOCKS=false
```

`.env.local` is in `.gitignore` by default with create-next-app. Verify before first commit:
```bash
cat promptforge-web/.gitignore | grep env
# Expected: .env*.local
```

---

## WHAT THE AGENT MUST NEVER DO

These are hard stops. If the agent does any of these, stop the session immediately and use the correction template.

```
NEVER touch promptforge/ (backend) — not a single file
NEVER call fetch() outside lib/api.ts or lib/stream.ts
NEVER add 'use client' to app/(marketing)/ files
NEVER hardcode a color hex — CSS variables only
NEVER display raw error messages to users
NEVER log user prompt content
NEVER log JWT tokens or session IDs
NEVER add an npm package without explicit approval
NEVER skip the tsc check between files
NEVER commit with TypeScript errors
NEVER start a new step before verify.sh passes on the previous step
```

---

*WORKFLOW.md is your guide. The agent never sees this file.*
*Feed the agent: FRONTEND_RULES.md + relevant Plan file + Session Brief only.*
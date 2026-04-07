---
description: Senior dev security-driven development lifecycle for PromptForge
---

# Senior Dev Rules — Security-Driven Development Lifecycle

## IDENTITY

You are a senior software engineer. You do NOT guess. You do NOT assume.
You read files before touching them. You verify after every change.
You follow security-first principles. You close every loop.

---

## PHASE 0 — BEFORE ANY CHANGE

### 0.1 Read First, Always
- **Read the ENTIRE file** you're about to modify — not just the lines you think you need
- Paste the exact current code you're changing (before/after)
- If the file is >300 lines, read in sections and note line ranges

### 0.2 Check Dependencies
- Will this change break any file that imports from the file you're modifying?
- Run: `grep -rn "import.*<module>" --include="*.py" --include="*.ts" --include="*.tsx"`
- List all dependents before proceeding

### 0.3 State the Contract
Before writing any code, state:
1. **What file** you're changing
2. **What lines** are changing
3. **What the change does** (one sentence)
4. **What could break** (blast radius)
5. **How you'll verify** it worked

---

## PHASE 1 — SECURITY-FIRST DEVELOPMENT

### 1.1 Security Checklist (Every Change)
- [ ] No secrets hardcoded (API keys, tokens, passwords)
- [ ] No `dangerouslySetInnerHTML` without sanitization
- [ ] No wildcard CORS (`*`) in production
- [ ] No `eval()`, `exec()`, or dynamic code execution
- [ ] Input validation on all user-facing endpoints
- [ ] Error messages don't leak internals (stack traces, file paths, DB names)

### 1.2 Boundary Rules (DO NOT TOUCH)
These files are off-limits unless explicitly asked:
- `useKiraStream.ts` — SSE parsing logic (lines 265-350)
- `memory/langmem.py`, `memory/supermemory.py` — memory layer
- `database.py` — database operations
- `auth.py` — authentication
- `agents/intent.py`, `agents/context.py`, `agents/domain.py` — agent swarm
- `state.py`, `workflow.py` — state machine

### 1.3 Additive-Only Rule
- **Never rewrite a file** — edit only what changes, preserve everything else
- **Never remove existing exports** — other files may depend on them
- **Never change function signatures** — only add optional parameters
- **New components go in new files** — import them cleanly

---

## PHASE 2 — IMPLEMENTATION

### 2.1 One Fix at a Time
- Implement ONE fix completely before starting the next
- Each fix follows: Read → Change → Verify → Report
- Never batch multiple unrelated changes into one edit

### 2.2 Code Standards
**Python:**
- Type hints on all functions
- Docstrings with Args/Returns
- `logger.info()` for operations, `logger.error()` for failures
- Follow existing patterns in the codebase

**TypeScript/React:**
- `'use client'` on interactive components
- Props interfaces defined inline or imported
- Follow existing naming conventions (e.g., `useKiraStream`, `ChatContainer`)
- Preserve `forwardRef` behavior when wrapping components

### 2.3 File Location Rules
- Backend utils → `agents/utils/` (existing pattern)
- Frontend components → appropriate feature folder
- Shared constants → `lib/constants.ts`
- New hooks → feature-specific `hooks/` folder

---

## PHASE 3 — VERIFICATION (Close the Loop)

### 3.1 After EVERY Single Fix
// turbo-all

```
# TypeScript check (frontend) — MUST be zero errors
cd promptforge-web && npx tsc --noEmit

# Python syntax check (backend) — MUST be zero errors  
python -m py_compile <changed_file.py>

# Import check (backend) — MUST print OK
python -c "from <module> import <function>; print('OK')"
```

### 3.2 After ALL Fixes Complete
```
# Full TypeScript check
cd promptforge-web && npx tsc --noEmit

# Full Python check (if pyflakes available)
python -m pyflakes <changed_files>

# Start servers and smoke test
# Backend: uvicorn api:app --port 8000
# Frontend: cd promptforge-web && npm run dev
```

### 3.3 Report Format for Each Fix
```
FIX N — [Name]
  Changed: [file:line-range]
  Before:  [exact old code]
  After:   [exact new code]
  Verify:  [command run + output]
  Status:  ✅ PASS / ❌ FAIL
```

---

## PHASE 4 — DEPLOYMENT CHECKLIST

### 4.1 Before Deploying Backend (Railway)
- [ ] `ENVIRONMENT=production` set in Railway env vars
- [ ] `FRONTEND_URLS` includes Vercel production URL
- [ ] `SENTRY_DSN` set in Railway env vars
- [ ] `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET` set
- [ ] `REDIS_URL` set (Upstash)
- [ ] `POLLINATIONS_API_KEY` set
- [ ] `GEMINI_API_KEY` set
- [ ] `/test-error` route removed or gated
- [ ] Rate limiter enabled (not bypassed by ENVIRONMENT)

### 4.2 Before Deploying Frontend (Vercel)
- [ ] `NEXT_PUBLIC_API_URL` points to Railway production URL
- [ ] `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` set
- [ ] `NEXT_PUBLIC_SENTRY_DSN` set
- [ ] Sentry sample rates reduced for production (0.1, not 1.0)
- [ ] `next build` completes with zero errors
- [ ] `NEXT_PUBLIC_USE_MOCKS=false`

### 4.3 Post-Deploy Verification
- [ ] Hit `GET /health` on Railway URL — returns `{"status":"ok"}`
- [ ] Load Vercel URL — page renders without console errors
- [ ] Sign up / log in — auth flow works
- [ ] Send a prompt — SSE streaming works end-to-end
- [ ] Check Sentry dashboard — events appearing (not /test-error spam)

---

## ANTI-PATTERNS (Never Do These)

1. ❌ "I'll fix that later" — Fix it now or document it as a known issue
2. ❌ Changing files you haven't read completely
3. ❌ Multiple parallel edits to the same file
4. ❌ Installing new dependencies without checking bundle size impact
5. ❌ Trusting previous audit findings without re-reading the actual code
6. ❌ Making "temporary" dev bypasses that reach production
7. ❌ Hardcoding URLs, keys, or environment-specific values
8. ❌ Removing code without checking what imports it

# Monitoring Setup Documentation

## Part 1: Model Configuration ✅ COMPLETED

### Selected Models (Free Tier)

| Role | Model | Context | Cost (/M tokens) | Purpose |
|------|-------|---------|------------------|---------|
| **FAST** | `gemini-fast` | 5.6K | $0.10 | Intent analysis, domain detection, context classification |
| **FULL** | `qwen-coder` | 1.8K | $0.06 | Prompt engineering, detailed outputs, agent briefs |

### Why These Models?

**gemini-fast (FAST):**
- ✅ Responds with conversational text (unlike qwen-safety which outputs safety classifications)
- ✅ 5.6K context sufficient for analysis tasks
- ✅ Fast (~3-4s latency in testing)
- ✅ Cheap ($0.10/M tokens)

**qwen-coder (FULL):**
- ✅ Best FREE coder model (30B params)
- ✅ Produces detailed, verbose outputs (1000+ chars in testing)
- ✅ 1.8K context adequate for prompt engineering
- ✅ Very cheap ($0.06/M tokens)

### Health Test Results

```
FAST Model (gemini-fast):
  ✓ Status:  PASS
  ⏱ Latency: 3656ms
  📝 Length: 31 chars
  💬 Output: FAST_OK gemini-1.5-flash-latest

FULL Model (qwen-coder):
  ✓ Status:  PASS
  ⏱ Latency: 4155ms
  📝 Length: 1098 chars
  💬 Output: A multi-agent AI system is a distributed artificial intelligence...
```

### Configuration Files

**Backend (.env):**
```env
POLLINATIONS_MODEL_FAST=gemini-fast
POLLINATIONS_MODEL_FULL=qwen-coder
```

---

## Part 2: Sentry Frontend Setup ✅ COMPLETED

### Installed Packages

- `@sentry/nextjs@^10.45.0` (via npm)

### Created Configuration Files

| File | Purpose |
|------|---------|
| `sentry.client.config.ts` | Browser-side Sentry init (tracing + session replay) |
| `sentry.server.config.ts` | Node.js server-side Sentry init |
| `sentry.edge.config.ts` | Edge runtime Sentry init |
| `instrumentation.ts` | Next.js instrumentation registration |
| `next.config.ts` | Updated with `withSentryConfig()` wrapper |
| `app/sentry-example-page/page.tsx` | Test page for error triggering |

### Environment Variables

**.env.local:**
```env
NEXT_PUBLIC_SENTRY_DSN=https://mw3gfyygarneck5yng6726m6192my7s1aq1pjj42x237tprekm3ptrarz2mphwmy@o4508748599369728.ingest.us.sentry.io/4508748604481536
```

### Sentry Project Details

- **Organization:** student-cjs
- **Project:** javascript-nextjs
- **Platform:** Next.js (JavaScript)
- **DSN:** Configured via `NEXT_PUBLIC_SENTRY_DSN`

### Features Enabled

1. **Error Tracking** - Captures uncaught errors with stack traces
2. **Tracing** - Performance monitoring (100% sample rate in dev)
3. **Session Replay** - Video-like reproduction of user sessions (100% sample rate)
4. **Logs** - Application log aggregation

### How to Verify Sentry is Working

1. **Start dev server:**
   ```bash
   cd promptforge-web
   npm run dev
   ```

2. **Visit test page:**
   ```
   http://localhost:3000/sentry-example-page
   ```

3. **Click "Trigger Test Error" button**

4. **Check Sentry Dashboard:**
   - URL: https://sentry.io/settings/student-cjs/projects/javascript-nextjs/issues/
   - Look for error titled: "Sentry Test Error - This is a test error to verify Sentry integration"
   - Verify environment shows "development"
   - Check "Replays" tab for session recording
   - Check "Performance" tab for transaction trace

### Proof of Connection (Expected)

After triggering the test error, Sentry dashboard should show:

- **Issue:** "Error: Sentry Test Error - This is a test error to verify Sentry integration"
- **Project:** student-cjs / javascript-nextjs
- **Environment:** development
- **Timestamp:** Current time
- **Tags:** `transaction: /sentry-example-page`, `level: error`
- **Replay:** Session recording showing button click
- **Transaction:** Page load + error timing

---

## Part 3: Backend Sentry Setup (TODO)

### Required Steps

1. **Install Sentry SDK:**
   ```bash
   cd C:\Users\user\OneDrive\Desktop\newnew
   pip install sentry-sdk[fastapi]
   ```

2. **Add to api.py (top of file, before other imports):**
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.fastapi import FastApiIntegration
   
   sentry_sdk.init(
       dsn=os.getenv("SENTRY_DSN"),
       integrations=[FastApiIntegration()],
       traces_sample_rate=1.0,
       environment=os.getenv("NODE_ENV", "development"),
   )
   ```

3. **Add to .env:**
   ```env
   SENTRY_DSN=https://mw3gfyygarneck5yng6726m6192my7s1aq1pjj42x237tprekm3ptrarz2mphwmy@o4508748599369728.ingest.us.sentry.io/4508748604481536
   ```

4. **Create new Sentry project for backend (optional but recommended):**
   - Go to https://sentry.io
   - New Project → Python → FastAPI
   - Copy DSN to `.env`

---

## Part 4: Better Stack Uptime Monitoring (TODO)

### What is Better Stack?

Better Stack Uptime monitors your API endpoints and alerts you when they go down.

### Setup Steps

1. **Create Better Stack account:**
   - Go to https://betterstack.com/uptime
   - Sign up (free tier available)

2. **Add HTTP Monitor:**
   - Monitor Type: HTTP(s)
   - URL: `https://your-railway-app.railway.app/health`
   - Check Interval: 3 minutes (free tier)
   - Regions: US, EU, Asia (select all available)

3. **Configure Alerts:**
   - Email alerts: Your email
   - Notify when: Down for 2 consecutive checks
   - Recovery notifications: Yes

4. **Add Status Page (optional):**
   - Public status page for users
   - Custom domain (optional)

### Railway Deployment

1. **Deploy backend to Railway:**
   ```bash
   cd C:\Users\user\OneDrive\Desktop\newnew
   git push
   ```

2. **Add environment variables in Railway:**
   - `SENTRY_DSN` (from Sentry dashboard)
   - `POLLINATIONS_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `REDIS_URL`
   - `GEMINI_API_KEY`

3. **Get Railway URL:**
   - Railway Dashboard → Your Project → Generate Domain
   - Example: `promptforge-api-production.up.railway.app`

4. **Update Better Stack monitor URL:**
   - `https://promptforge-api-production.up.railway.app/health`

---

## Part 5: Complete Monitoring Stack Summary

| Component | Tool | Status | Purpose |
|-----------|------|--------|---------|
| **Frontend Errors** | Sentry | ✅ Done | Error tracking, session replay |
| **Backend Errors** | Sentry | ⏳ TODO | Error tracking for FastAPI |
| **Uptime Monitoring** | Better Stack | ⏳ TODO | HTTP endpoint monitoring |
| **Performance** | Sentry | ✅ Done | Tracing for FE, TODO for BE |
| **Logs** | Sentry | ✅ Done | Log aggregation (FE only) |

### What We Skipped (Per Your Plan)

- ❌ PostHog (event analytics) - Deferred
- ❌ Axiom (log aggregation) - Using Sentry instead
- ❌ Grafana (metrics dashboards) - Overkill for MVP

---

## Next Actions (Priority Order)

1. ✅ **DONE:** Model config updated (`gemini-fast` + `qwen-coder`)
2. ✅ **DONE:** Sentry frontend setup complete
3. ⏳ **TODO:** Test Sentry by visiting `/sentry-example-page` and triggering error
4. ⏳ **TODO:** Install Sentry SDK for backend (FastAPI)
5. ⏳ **TODO:** Deploy backend to Railway
6. ⏳ **TODO:** Set up Better Stack uptime monitor
7. ⏳ **TODO:** Add payment integration to frontend (Stripe/Paddle)
8. ⏳ **TODO:** Deploy frontend with payment gate

---

## Timeout Issue Documentation

### Problem

Previous agent call failed with:
```
API Error: Streaming request timeout after 35s
API Error: Connection error. (cause: fetch failed)
```

### Root Cause

- Input was too large (full model pricing table + monitoring plan + Sentry logs)
- Streaming mode with 35s timeout
- Complex reasoning exceeded timeout limit

### Solution

For future large tasks:

1. **Split into smaller prompts** - Don't include full logs/transcripts
2. **Increase timeout** - Set `contentGenerator.timeout` to 60s+ for long tasks
3. **Use non-streaming mode** - For batch processing of large inputs
4. **Avoid repetition** - Don't paste same transcript multiple times

### Applied Fix

This session uses:
- Focused, modular prompts
- No log echoing unless necessary
- Clear task separation (model test → Sentry → monitoring plan)

---

**Document Created:** March 25, 2026  
**Status:** Frontend Sentry ✅ | Backend Sentry ⏳ | Better Stack ⏳

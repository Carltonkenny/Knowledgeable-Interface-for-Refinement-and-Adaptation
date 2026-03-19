# AGENT BRIEF — Observability & Monitoring Setup

**Title:** Production Observability Stack (Sentry + Better Stack)  
**Estimated Time:** 45 minutes  
**Priority:** CRITICAL — Deploy AFTER Railway migration passes  
**Prerequisites:** Railway deployment successful, SSE curl test passed

---

## **🎯 OBJECTIVE**

Add production-grade monitoring to detect crashes, track uptime, and debug issues **before users report them**.

---

## **📋 WHAT YOU'RE BUILDING**

```
┌─────────────────────────────────────────────────────────────┐
│                     PROMPTFORGE                             │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Sentry    │  │ Better Stack│  │   Axiom     │        │
│  │  (Errors)   │  │  (Uptime)   │  │  (Logs)     │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                 │
│         └────────────────┴────────────────┘                 │
│                          │                                  │
│                  ┌───────▼───────┐                          │
│                  │  api.py       │                          │
│                  │  (Backend)    │                          │
│                  └───────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## **🚫 WHAT YOU'RE NOT BUILDING**

- ❌ PostHog event tracking (nice-to-have, defer to Move 3)
- ❌ Custom dashboards (use default dashboards first)
- ❌ Alert routing (email alerts are enough for MVP)
- ❌ Axiom log aggregation (Railway logs sufficient for now)

---

## **📦 SESSION A: SENTRY (Error Tracking)**

### **TASK A1: Backend Sentry** (15 mins)

**FILE:** `newnew/api.py`

**ADD at very top (before any other import):**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import os

# Sentry initialization — must be before any other imports
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # Sample 10% of transactions
    environment=os.getenv("ENVIRONMENT", "production"),
    release="promptforge-2.0.0",
)
```

**INSTALL:**
```bash
cd newnew
pip install sentry-sdk[fastapi]
echo "sentry-sdk[fastapi]==2.20.0" >> requirements.txt
git add requirements.txt
git commit -m "feat: Add Sentry SDK for error tracking"
git push
```

**RAILWAY ENV VAR:**
```
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
ENVIRONMENT=production
```

**GET DSN:**
1. Go to [sentry.io](https://sentry.io)
2. Create account (free tier)
3. New Project → Python → FastAPI
4. Copy DSN from "Connect to Sentry" → "SDK Setup"

---

### **TASK A2: Frontend Sentry** (15 mins)

**DIRECTORY:** `promptforge-web/`

**RUN WIZARD:**
```bash
cd promptforge-web
npx @sentry/wizard@latest -i nextjs
```

**Follow wizard prompts:**
- Select "Sentry Cloud"
- Enter organization/project
- Let it auto-configure

**ADD TO `.env.local`:**
```bash
NEXT_PUBLIC_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

**ADD TO VERCEL ENV VARS:**
```
NEXT_PUBLIC_SENTRY_DSN=(same value)
```

**VERIFY:**
```bash
npm run build
# Should complete without errors
```

---

### **TASK A3: Test Sentry** (5 mins)

**TRIGGER TEST ERROR:**

**Backend test:**
```python
# Add temporary route in api.py for testing
@app.get("/test-error")
async def test_error():
    raise ValueError("This is a test error from Sentry setup")
```

**Frontend test:**
```typescript
// Add temporary button in any component
<button onClick={() => { throw new Error("Test error from frontend") }}>
  Test Sentry
</button>
```

**DEPLOY TO RAILWAY:**
```bash
git push
```

**VISIT:**
- Backend: `https://yourapp.up.railway.app/test-error`
- Frontend: Click test button

**CHECK SENTRY DASHBOARD:**
- Errors should appear within 60 seconds
- Should show stack trace, environment, release

**REMOVE TEST CODE:**
```bash
git revert last commit
git push
```

---

## **📦 SESSION B: BETTER STACK (Uptime Monitoring)**

### **TASK B1: Uptime Monitor** (5 mins)

**NO CODE REQUIRED — Configuration only**

**STEPS:**
1. Go to [betterstack.com/uptime](https://betterstack.com/uptime)
2. Create free account
3. Click "Add Monitor"
4. **Configure:**
   - **URL:** `https://yourapp.up.railway.app/health`
   - **Check interval:** 3 minutes
   - **Regions:** 3 regions (default)
   - **Alert email:** your email
5. Click "Create Monitor"

**VERIFICATION:**
- Wait 5 minutes
- Check email for status report
- Should show "Up" with response time

**DONE.** No code changes needed.

---

## **📦 SESSION C: OPTIONAL — AXIOM (Log Aggregation)**

### **TASK C1: Axiom Setup** (10 mins)

**ONLY IF Railway logs become unmanageable**

**INSTALL:**
```bash
cd newnew
pip install python-json-logger
echo "python-json-logger==2.0.7" >> requirements.txt
```

**ADD TO `api.py`:**

```python
import logging
from pythonjsonlogger import jsonlogger

# Configure JSON logging for Axiom
logger = logging.getLogger(__name__)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

**RAILWAY ENV VARS:**
```
AXIOM_TOKEN=your_token
AXIOM_DATASET=promptforge-logs
```

**VERIFICATION:**
- Check Axiom dashboard
- Should see logs streaming in

**SKIP FOR NOW** — Railway logs are sufficient for MVP.

---

## **📦 SESSION D: POSTHOG (Event Tracking)**

### **TASK D1: PostHog Setup** (10 mins)

**ONLY IF you need user analytics**

**INSTALL:**
```bash
cd promptforge-web
npm install posthog-js posthog-node
```

**ADD TO `promptforge-web/pages/_app.tsx`:**

```typescript
import posthog from 'posthog-js'
import { PostHogProvider } from 'posthog-js/react'

if (typeof window !== 'undefined') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com',
  })
}

export default function App({ Component, pageProps }) {
  return (
    <PostHogProvider client={posthog}>
      <Component {...pageProps} />
    </PostHogProvider>
  )
}
```

**ENV VARS:**
```
NEXT_PUBLIC_POSTHOG_KEY=phc_xxx
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
```

**TRACK EVENTS:**
```typescript
// In components
import posthog from 'posthog-js'

posthog.capture('prompt_sent', { prompt_length: 50 })
```

**SKIP FOR NOW** — Not critical for MVP.

---

## **✅ VERIFICATION CHECKLIST**

After completing observability setup:

- [ ] **Sentry backend installed** — `sentry-sdk` in requirements.txt
- [ ] **Sentry frontend installed** — `@sentry/nextjs` in package.json
- [ ] **Test error triggered** — Visible in Sentry dashboard
- [ ] **Better Stack monitor active** — Shows "Up" status
- [ ] **Railway logs accessible** — Via dashboard
- [ ] **No console errors** — Frontend clean
- [ ] **No deployment errors** — Railway build green

---

## **📊 SUCCESS METRICS**

| Metric | Target | How to Check |
|--------|--------|--------------|
| Error detection | < 60 seconds | Sentry dashboard |
| Uptime monitoring | 3-min intervals | Better Stack |
| Log availability | Real-time | Railway dashboard |
| False positives | < 1% | Alert accuracy |

---

## **🚨 TROUBLESHOOTING**

### **Problem: Sentry Not Receiving Errors**

**Check:**
1. DSN correct in Railway env vars?
2. `sentry_sdk.init()` called before any other imports?
3. `traces_sample_rate` > 0?

**Fix:**
```python
# Verify init is at very top of api.py
import sentry_sdk  # ← Must be FIRST
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

# Then other imports
import os
import logging
```

---

### **Problem: Better Stack Shows "Down"**

**Check:**
1. Railway URL correct?
2. `/health` endpoint working?
3. Railway deployment successful?

**Fix:**
```bash
curl https://yourapp.up.railway.app/health
# Should return {"status":"ok"}
```

---

### **Problem: Frontend Errors Not in Sentry**

**Check:**
1. `NEXT_PUBLIC_SENTRY_DSN` in Vercel env vars?
2. `_app.tsx` configured with Sentry?
3. Build completed successfully?

**Fix:**
```bash
npm run build
# Check for Sentry-related warnings
```

---

## **📝 CHECK-IN REPORT TEMPLATE**

After completing observability setup:

```
OBSERVABILITY SETUP REPORT
==========================

Date: [DATE]
Setup by: [YOUR NAME]

TASKS COMPLETED:
1. Sentry backend installed — yes/no
2. Sentry frontend installed — yes/no
3. Test error triggered — yes/no
4. Better Stack monitor active — yes/no
5. Axiom setup — yes/no (skip if deferred)
6. PostHog setup — yes/no (skip if deferred)

METRICS:
- Sentry DSN configured — yes/no
- First error received — latency: X seconds
- Uptime monitor interval — X minutes
- Alert email configured — yes/no

ISSUES ENCOUNTERED:
[List any issues and how you fixed them]

NEXT STEPS:
[List any follow-up tasks needed]
```

---

## **🎯 SUMMARY**

**This setup gives you:**

1. ✅ **Error detection** — Know when crashes happen (Sentry)
2. ✅ **Uptime monitoring** — Know when site is down (Better Stack)
3. ✅ **Log access** — Debug via Railway logs
4. ✅ **Email alerts** — Get notified immediately

**Time required:** 45 minutes  
**Complexity:** LOW (copy-paste config)  
**Value:** CRITICAL (production blind without)

---

## **🤖 AGENT INSTRUCTIONS**

**Execute in this exact order:**

1. **Complete Railway migration** (Move 1) ✅
2. **Verify SSE works** (curl test) ✅
3. **Setup Sentry backend** (Task A1 - 15 mins)
4. **Setup Sentry frontend** (Task A2 - 15 mins)
5. **Test error detection** (Task A3 - 5 mins)
6. **Setup Better Stack** (Task B1 - 5 mins)
7. **Skip Axiom + PostHog** (defer to Move 3)

**STOP after Step 7. Do not continue to Move 3.**

**Check in with this report:**
- Sentry backend — working/not working
- Sentry frontend — working/not working
- Better Stack — active/not active
- Test error — visible/not visible in dashboard

---

**READY TO EXECUTE. Start after Railway migration passes.**

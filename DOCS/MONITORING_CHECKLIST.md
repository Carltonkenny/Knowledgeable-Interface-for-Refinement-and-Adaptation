# Monitoring Deployment Checklist

Follow this checklist step-by-step to complete the monitoring setup and deploy to production.

---

## PHASE 1: Local Development Verification (30 mins)

### 1.1 Test Frontend Sentry Integration

- [ ] **Start Next.js dev server**
  ```bash
  cd C:\Users\user\OneDrive\Desktop\newnew\promptforge-web
  npm run dev
  ```

- [ ] **Visit Sentry test page**
  ```
  http://localhost:3000/sentry-example-page
  ```

- [ ] **Click "Trigger Test Error" button**

- [ ] **Verify error in Sentry dashboard**
  - Open: https://sentry.io/settings/student-cjs/projects/javascript-nextjs/issues/
  - Look for: "Sentry Test Error"
  - Confirm: Environment = "development"
  - Confirm: Transaction appears in "Performance" tab
  - Confirm: Replay appears in "Replays" tab (may take 30s to process)

- [ ] **Screenshot for records** (optional)
  - Issues list showing test error
  - Transaction trace
  - Session replay thumbnail

### 1.2 Verify Model Configuration

- [ ] **Confirm .env has correct models**
  ```bash
  cd C:\Users\user\OneDrive\Desktop\newnew
  type .env | findstr MODEL
  ```
  Expected output:
  ```
  POLLINATIONS_MODEL_FULL=qwen-coder
  POLLINATIONS_MODEL_FAST=gemini-fast
  ```

- [ ] **Restart backend to load new models**
  ```bash
  # If backend is running, stop and restart
  # Backend will auto-load new models from .env
  ```

---

## PHASE 2: Backend Sentry Setup (15 mins)

### 2.1 Install Sentry SDK

- [ ] **Install Python package**
  ```bash
  cd C:\Users\user\OneDrive\Desktop\newnew
  pip install sentry-sdk[fastapi]
  ```

- [ ] **Add to requirements.txt**
  ```bash
  echo sentry-sdk[fastapi]==2.20.0 >> requirements.txt
  ```

### 2.2 Configure api.py

- [ ] **Add Sentry init at top of api.py** (before other imports)

  Edit `C:\Users\user\OneDrive\Desktop\newnew\api.py`:

  ```python
  # api.py
  # ─────────────────────────────────────────────
  # FastAPI App Factory — PromptForge v2.0
  # ─────────────────────────────────────────────

  import os
  import logging
  import sentry_sdk
  from sentry_sdk.integrations.fastapi import FastApiIntegration

  # Initialize Sentry (before FastAPI app creation)
  sentry_sdk.init(
      dsn=os.getenv("SENTRY_DSN"),
      integrations=[FastApiIntegration()],
      traces_sample_rate=1.0,
      environment=os.getenv("NODE_ENV", "development"),
  )

  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  # ... rest of imports
  ```

### 2.3 Add Sentry DSN to .env

- [ ] **Add to backend .env**
  ```bash
  cd C:\Users\user\OneDrive\Desktop\newnew
  echo SENTRY_DSN=https://mw3gfyygarneck5yng6726m6192my7s1aq1pjj42x237tprekm3ptrarz2mphwmy@o4508748599369728.ingest.us.sentry.io/4508748604481536 >> .env
  ```

### 2.4 Test Backend Sentry

- [ ] **Restart backend server**

- [ ] **Trigger a test error** (create temporary endpoint)
  
  Add to `routes/prompts.py` or any route file:
  ```python
  @router.get("/test-error")
  async def test_error():
      """Test endpoint for Sentry - REMOVE IN PRODUCTION"""
      raise ValueError("Backend Sentry Test Error")
  ```

- [ ] **Call test endpoint**
  ```bash
  curl http://localhost:8000/test-error
  ```

- [ ] **Check Sentry dashboard**
  - Should show Python error with stack trace
  - Environment: "development"

- [ ] **Remove test endpoint** after verification

---

## PHASE 3: Railway Deployment (30 mins)

### 3.1 Prepare Railway Project

- [ ] **Create Railway account** (if not exists)
  - Go to: https://railway.app
  - Sign up with GitHub

- [ ] **Create new project**
  - Click "New Project"
  - Select "Deploy from GitHub repo"
  - Choose repo: `promptforge-web` (frontend) OR `newnew` (backend)

### 3.2 Deploy Backend to Railway

- [ ] **Configure Railway service**
  - Service Name: `promptforge-api`
  - Root Directory: `.` (or subfolder if applicable)
  - Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

- [ ] **Add environment variables in Railway**
  
  Go to Railway Dashboard → Variables → Add:
  ```
  POLLINATIONS_API_KEY=sk_hp7lv3M4MYipJKG6ordeDaHTzqCaGNwV
  POLLINATIONS_BASE_URL=https://gen.pollinations.ai/v1
  POLLINATIONS_MODEL_FULL=qwen-coder
  POLLINATIONS_MODEL_FAST=gemini-fast
  SUPABASE_URL=https://cckznjkzsfypssgecyya.supabase.co
  SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  REDIS_URL=rediss://default:AZjkAAIncDE4...
  GEMINI_API_KEY=AIzaSyAAJJGwnMMgTc531tKlwhdv_TGONb5sg4g
  SENTRY_DSN=https://mw3gfyygarneck5yng6726m6192my7s1aq1pjj42x237tprekm3ptrarz2mphwmy@o4508748599369728.ingest.us.sentry.io/4508748604481536
  FRONTEND_URLS=http://localhost:3000,https://your-frontend-url.vercel.app
  NODE_ENV=production
  ```

- [ ] **Deploy**
  - Railway auto-deploys on push
  - Wait for build to complete (~2-5 mins)

- [ ] **Get Railway URL**
  - Railway Dashboard → Settings → Domains
  - Example: `promptforge-api-production.up.railway.app`

- [ ] **Test health endpoint**
  ```bash
  curl https://promptforge-api-production.up.railway.app/health
  ```
  Expected: `{"status": "ok"}`

### 3.3 Verify Sentry in Production

- [ ] **Call production API**
  ```bash
  curl https://promptforge-api-production.up.railway.app/test-error
  ```

- [ ] **Check Sentry dashboard**
  - Environment should show "production"
  - Error should appear from Railway IP

---

## PHASE 4: Better Stack Uptime Setup (15 mins)

### 4.1 Create Better Stack Account

- [ ] **Sign up**
  - Go to: https://betterstack.com/uptime
  - Free tier: 10 monitors, 3-min intervals

### 4.2 Configure HTTP Monitor

- [ ] **Add new monitor**
  - Monitor Type: HTTP(s)
  - Friendly Name: `PromptForge API Production`
  - URL: `https://promptforge-api-production.up.railway.app/health`
  - Check Interval: 3 minutes (free tier)
  - Regions: Select all available (US, EU, Asia)

- [ ] **Configure alerting**
  - Email Alerts: Your email address
  - Notify When: Down for 2 consecutive checks (6 mins)
  - Recovery Notifications: Yes
  - SMS/Push: Optional (paid tier)

- [ ] **Create monitor**

### 4.3 Verify Monitor

- [ ] **Wait for first check** (~3 mins)

- [ ] **Confirm status shows "Up"**
  - Green checkmark
  - Response time displayed

- [ ] **Test alert** (optional)
  - Pause monitor
  - Wait for alert email
  - Resume monitor

---

## PHASE 5: Frontend Deployment (After Payment Integration)

### ⚠️ DO NOT DEPLOY YET

**Reason:** No payment integration = no revenue path

### When Ready (After Stripe/Paddle):

- [ ] **Add payment to frontend** (Stripe or Paddle)
- [ ] **Create frontend Dockerfile**
- [ ] **Deploy to Vercel/Netlify**
- [ ] **Add frontend URL to backend CORS**
- [ ] **Update Better Stack to monitor frontend too**

---

## PHASE 6: Production Hardening (Week 3)

### 6.1 Error Tracking Optimization

- [ ] **Reduce Sentry sample rate** (cost control)
  ```python
  # In api.py
  traces_sample_rate=0.1  # 10% of requests
  ```

- [ ] **Configure alert filters**
  - Ignore 404 errors
  - Ignore rate limit errors
  - Alert on 500 errors only

### 6.2 Performance Monitoring

- [ ] **Review Sentry Performance dashboard**
  - Identify slow endpoints
  - Set performance budgets

- [ ] **Add custom spans** (optional)
  ```python
  with sentry_sdk.start_span(op="db", description="Supabase query"):
      # DB call
  ```

### 6.3 Uptime Optimization

- [ ] **Add status page** (optional)
  - Better Stack public status page
  - Custom domain: `status.promptforge.ai`

- [ ] **Configure maintenance windows**
  - Scheduled downtime (deploys)
  - Suppress alerts during maintenance

---

## VERIFICATION CHECKLIST

After completing all phases, verify:

- [ ] **Frontend errors appear in Sentry** (student-cjs/javascript-nextjs)
- [ ] **Backend errors appear in Sentry** (student-cjs/python-fastapi or same project)
- [ ] **Better Stack shows API as "Up"**
- [ ] **Email alerts work** (test by pausing monitor)
- [ ] **Railway deployment successful** (health endpoint returns 200)
- [ ] **Models working in production** (gemini-fast + qwen-coder)
- [ ] **No secrets in code** (all via env vars)
- [ ] **CORS locked to frontend domain** (no wildcard)

---

## TROUBLESHOOTING

### Sentry Not Receiving Events

1. Check DSN is correct in .env
2. Verify network access to sentry.io
3. Check browser console for Sentry errors (FE)
4. Check api.py logs for init errors (BE)

### Better Stack Shows "Down"

1. Verify Railway URL is correct
2. Check Railway logs for crashes
3. Test health endpoint manually: `curl https://your-url.railway.app/health`
4. Check Railway has enough resources (free tier limits)

### Railway Build Fails

1. Check `requirements.txt` is complete
2. Verify Python version in `runtime.txt` (if needed)
3. Check Railway logs for specific error
4. Ensure PORT env var is used in uvicorn

---

## COST PROJECTION (Free Tier)

| Service | Free Tier Limit | Your Usage | Cost |
|---------|----------------|------------|------|
| **Sentry** | 50K errors/mo | ~1K errors | $0 |
| **Better Stack** | 10 monitors | 1 monitor | $0 |
| **Railway** | $5 credit/mo | ~$2-3 | $0 |
| **Total** | | | **$0/mo** |

---

**Last Updated:** March 25, 2026  
**Status:** Ready for execution

# 🚀 PromptForge v2.0 — Docker + Vercel Deployment Guide

**Status:** Ready for Deployment  
**Last Updated:** March 2026  
**Follows:** RULES.md Engineering Standards

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### ✅ Completed Tasks

- [x] Sentry SDK added to `api.py` (initialization at top of file)
- [x] `sentry-sdk[fastapi]==2.20.0` added to `requirements.txt`
- [x] Test error route `/test-error` added for verification
- [x] Frontend Sentry configured via wizard (`@sentry/nextjs@10.45.0`)
- [x] Models configured: `qwen-coder` (FULL) + `gemini-fast` (FAST)

### ⏳ Pending Tasks

- [ ] Add `SENTRY_DSN` to environment variables
- [ ] Build and test Docker image locally
- [ ] Deploy to Vercel/Railway
- [ ] Set up Better Stack uptime monitoring
- [ ] Verify errors appear in Sentry dashboard

---

## 🔧 STEP 1: GET YOUR SENTRY DSN

### Option A: Use Existing Sentry Project (Recommended)

You already have a Sentry account from the frontend wizard setup.

1. **Go to Sentry Dashboard:**
   ```
   https://sentry.io/settings/student-cjs/projects/javascript-nextjs/keys/
   ```

2. **Copy the DSN** (looks like):
   ```
   https://xxx@xxx.ingest.sentry.io/xxx
   ```

3. **Add to `.env` file:**
   ```env
   SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
   ENVIRONMENT=production
   ```

### Option B: Create New Python Project

1. **Go to:** https://sentry.io
2. **Create New Project:** Python → FastAPI
3. **Copy DSN** from "SDK Setup" section
4. **Add to `.env`** as shown above

---

## 🐳 STEP 2: BUILD & TEST LOCALLY WITH DOCKER

### 2.1 Build Docker Image

```powershell
# Navigate to backend directory
cd C:\Users\user\OneDrive\Desktop\newnew

# Build Docker image
docker build -t promptforge-api:v2.0 .

# Expected output:
# Step 1/15 : FROM python:3.11-slim as builder
# ...
# Successfully built promptforge-api:v2.0
```

### 2.2 Run with Docker Compose (Recommended)

```powershell
# Start both API and Redis
docker-compose up -d

# View logs
docker-compose logs -f api

# Expected output:
# promptforge-api  | INFO:     Started server process
# promptforge-api  | INFO:     Application startup complete.
# promptforge-api  | [api] CORS allowed for: ['http://localhost:3000', 'http://localhost:9000']
# promptforge-api  | [api] Rate limiting enabled: 100 requests/hour per user
# promptforge-api  | [config] Pollinations Gen API: https://gen.pollinations.ai/v1
# promptforge-api  | [config] Models: FULL=qwen-coder, FAST=gemini-fast
```

### 2.3 Test Health Endpoint

```powershell
# Test health check
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","version":"2.0.0"}
```

### 2.4 Test Sentry Integration

```powershell
# Trigger test error
curl http://localhost:8000/test-error

# Expected response: 500 Internal Server Error
# Check Sentry dashboard at: https://sentry.io/student-cjs/
```

### 2.5 Stop Docker Containers

```powershell
# Stop all services
docker-compose down

# View stopped containers
docker ps -a
```

---

## ☁️ STEP 3: DEPLOY TO VERCEL (Backend)

### ⚠️ IMPORTANT: Vercel is for Frontend Only

**Vercel is optimized for Next.js frontend, not FastAPI backends.**

**Recommended Architecture:**
```
Frontend (Next.js) → Vercel (FREE)
Backend (FastAPI)  → Railway (FREE tier) or Koyeb
Database (Supabase) → Supabase Cloud (FREE tier)
Redis (Upstash)    → Upstash Cloud (FREE tier)
```

### Option A: Deploy Backend to Railway (Recommended)

#### 3.1 Install Railway CLI

```powershell
npm install -g @railway/cli
```

#### 3.2 Login to Railway

```powershell
railway login
```

#### 3.3 Create New Project

```powershell
railway init
# Select: Create new project
# Project name: promptforge-backend
```

#### 3.4 Deploy

```powershell
# Deploy from current directory
railway up

# Or deploy via Git (recommended)
git push railway main
```

#### 3.5 Set Environment Variables

```powershell
# Set all required variables
railway variables set \
  SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx \
  ENVIRONMENT=production \
  POLLINATIONS_API_KEY=sk_xxx \
  POLLINATIONS_MODEL_FULL=qwen-coder \
  POLLINATIONS_MODEL_FAST=gemini-fast \
  SUPABASE_URL=https://xxx.supabase.co \
  SUPABASE_KEY=eyJxxx \
  SUPABASE_JWT_SECRET=xxx \
  REDIS_URL=rediss://xxx \
  GEMINI_API_KEY=xxx \
  FRONTEND_URLS=https://your-app.vercel.app
```

#### 3.6 View Logs

```powershell
# Stream logs
railway logs
```

### Option B: Deploy Backend to Koyeb

#### 3.1 Create `koyeb.yaml` (if not exists)

```yaml
name: promptforge-backend
services:
  - name: api
    type: web
    ports:
      - 8000
    routes:
      - path: /*
    build:
      type: docker
      dockerfile: ./Dockerfile
    env:
      - key: ENVIRONMENT
        value: production
      - key: SENTRY_DSN
        scope: secret
      # Add all other env vars as secrets
```

#### 3.2 Deploy

```powershell
# Install Koyeb CLI
npm install -g koyeb

# Login
koyeb login

# Deploy
koyeb app create promptforge-backend
koyeb app deploy
```

---

## 🎨 STEP 4: DEPLOY FRONTEND TO VERCEL

### 4.1 Install Vercel CLI

```powershell
npm install -g vercel
```

### 4.2 Login to Vercel

```powershell
vercel login
```

### 4.3 Deploy Frontend

```powershell
cd C:\Users\user\OneDrive\Desktop\newnew\promptforge-web

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### 4.4 Set Environment Variables in Vercel Dashboard

1. Go to: https://vercel.com/dashboard
2. Select your project
3. Settings → Environment Variables
4. Add:
   ```
   NEXT_PUBLIC_API_URL=https://promptforge-backend.railway.app
   NEXT_PUBLIC_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
   ```

### 4.5 Update Backend CORS

After frontend is deployed, update backend `FRONTEND_URLS`:

```powershell
# Railway
railway variables set FRONTEND_URLS=https://your-app.vercel.app

# Koyeb
koyeb app set env FRONTEND_URLS=https://your-app.vercel.app
```

---

## 📊 STEP 5: BETTER STACK UPTIME MONITORING

### 5.1 Create Account

1. Go to: https://betterstack.com/uptime
2. Sign up for free account

### 5.2 Add Monitor

1. Click **"Add Monitor"**
2. Configure:
   - **URL:** `https://promptforge-backend.railway.app/health`
   - **Check interval:** 3 minutes
   - **Regions:** Select 3 regions (default)
   - **Alert email:** your@email.com
3. Click **"Create Monitor"**

### 5.3 Verify

- Wait 5 minutes
- Check email for status report
- Should show "Up" with response time

---

## ✅ STEP 6: VERIFICATION CHECKLIST

### Backend (Railway/Koyeb)

```powershell
# Test health
curl https://promptforge-backend.railway.app/health
# Expected: {"status":"ok","version":"2.0.0"}

# Test Sentry integration
curl https://promptforge-backend.railway.app/test-error
# Expected: 500 error
# Check: https://sentry.io/student-cjs/ → Should see error
```

### Frontend (Vercel)

```
1. Visit: https://your-app.vercel.app
2. Open browser console (F12)
3. No Sentry errors should appear (unless you trigger one)
4. Visit: https://your-app.vercel.app/sentry-example-page
5. Click "Trigger Test Error"
6. Check Sentry dashboard → Should see frontend error
```

### Sentry Dashboard

```
1. Go to: https://sentry.io/student-cjs/
2. Check "Issues" tab
3. Should see:
   - Backend test error (from /test-error)
   - Frontend test error (from /sentry-example-page)
4. Verify environment = "production"
```

---

## 🚨 TROUBLESHOOTING

### Problem: Docker Build Fails

**Error:** `sentry-sdk not found`

**Fix:**
```powershell
# Clear Docker cache
docker builder prune -f

# Rebuild
docker build -t promptforge-api:v2.0 .
```

### Problem: Sentry Not Receiving Errors

**Check:**
1. DSN correct in environment variables?
2. `sentry_sdk.init()` called before other imports?
3. `traces_sample_rate` > 0?

**Fix:**
```python
# Verify in api.py (must be FIRST)
import sentry_sdk  # ← Before ALL other imports
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
```

### Problem: Railway Deployment Fails

**Check logs:**
```powershell
railway logs
```

**Common issues:**
- Missing environment variables → `railway variables set KEY=value`
- Build timeout → Check `requirements.txt` for large packages
- Port not exposed → Verify `EXPOSE 8000` in Dockerfile

### Problem: Frontend Can't Connect to Backend

**Check CORS:**
```python
# In api.py
frontend_urls = os.getenv("FRONTEND_URLS", "http://localhost:3000")
# Must include your Vercel URL
FRONTEND_URLS=https://your-app.vercel.app
```

---

## 📝 POST-DEPLOYMENT TASKS

### 1. Remove Test Route (Production Safety)

**Delete from `api.py`:**
```python
# Remove this entire function before production
@app.get("/test-error")
async def test_sentry_error():
    ...
```

### 2. Reduce Sentry Sample Rate (Cost Control)

**In `api.py`:**
```python
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.01,  # 1% instead of 10%
    profiles_sample_rate=0.01,
)
```

### 3. Set Up Alert Notifications

**Better Stack:**
- Go to Settings → Notifications
- Add SMS/Slack alerts for downtime

**Sentry:**
- Go to Project Settings → Alerts
- Create alert for high error rate

---

## 📊 DEPLOYMENT SUMMARY

| Component | Platform | Status | URL |
|-----------|----------|--------|-----|
| Frontend | Vercel | ⏳ Pending | https://your-app.vercel.app |
| Backend | Railway | ⏳ Pending | https://promptforge-backend.railway.app |
| Database | Supabase | ✅ Ready | https://cckznjkzsfypssgecyya.supabase.co |
| Redis | Upstash | ✅ Ready | aware-bluebird-39140.upstash.io |
| Error Tracking | Sentry | ✅ Configured | https://sentry.io/student-cjs |
| Uptime Monitor | Better Stack | ⏳ Pending | https://betterstack.com |

---

## 🎯 NEXT STEPS

1. ✅ **Add SENTRY_DSN to `.env`**
2. ✅ **Build Docker image locally**
3. ✅ **Test with Docker Desktop**
4. ✅ **Deploy backend to Railway**
5. ✅ **Deploy frontend to Vercel**
6. ✅ **Set up Better Stack monitoring**
7. ✅ **Verify Sentry receives errors**

---

**Ready to deploy like a senior dev. Follow steps in order. 🚀**

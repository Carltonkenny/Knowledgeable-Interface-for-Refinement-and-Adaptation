# 🚀 Koyeb Deployment Guide — PromptForge Backend

**Last Updated:** 2026-03-09  
**Status:** Ready for Production Deployment

---

## 📋 WHAT WE'LL DO

1. ✅ Install Koyeb CLI
2. ✅ Create Koyeb account (if you don't have one)
3. ✅ Create Redis service on Koyeb
4. ✅ Deploy the backend with Docker
5. ✅ Set environment variables securely
6. ✅ Verify deployment with health check
7. ✅ Test with a real API call
8. ✅ Update frontend to use production URL

**Time:** 15-20 minutes  
**Cost:** Koyeb free tier (512MB RAM, always-on)

---

## STEP 1: CREATE KOYEB ACCOUNT

### 1.1 Go to Koyeb
Open: https://www.koyeb.com/signup

### 1.2 Sign Up
Choose one:
- **GitHub** (recommended — easiest)
- **Google**
- **Email**

### 1.3 Verify Email
Check your inbox for verification email from Koyeb.

### 1.4 Create Organization
- Organization name: `promptforge` (or your choice)
- This is your workspace for all services

---

## STEP 2: INSTALL KOYEB CLI

### Windows (PowerShell as Administrator)

```powershell
# Install via npm (recommended)
npm install -g koyeb
```

### Verify Installation

```powershell
koyeb version
```

**Expected:**
```
koyeb version 0.x.x
```

### If Installation Fails

Download binary directly:
1. Go to: https://github.com/koyeb/cli/releases
2. Download `koyeb-windows-amd64.exe`
3. Rename to `koyeb.exe`
4. Move to `C:\Windows\System32\`

---

## STEP 3: LOGIN TO KOYEB

### 3.1 Run Login Command

```powershell
koyeb login
```

### 3.2 Browser Opens
- Koyeb will open your browser
- Click "Authorize" to grant CLI access
- Return to terminal

### 3.3 Verify Login

```powershell
koyeb app list
```

**Expected:**
```
No applications found.
```

---

## STEP 4: CREATE REDIS SERVICE

Redis is required for caching. We create it first.

### 4.1 Create Redis

```powershell
koyeb redis create promptforge-redis --region geo:us-east
```

**Wait for output:**
```
✓ Redis service created
  ID: rds_xxxxxxxxxxxxx
  Name: promptforge-redis
  Region: us-east
  Status: PROVISIONING
```

### 4.2 Get Redis Connection String

```powershell
koyeb redis get promptforge-redis
```

**Copy the connection string** — it looks like:
```
redis://default:PASSWORD@hostname.koyeb.app:6379
```

**Save this for Step 5!**

---

## STEP 5: PREPARE ENVIRONMENT VARIABLES

### 5.1 Create Production .env File

Create a new file: `C:\Users\user\OneDrive\Desktop\newnew\.env.koyeb`

**Copy this template:**

```bash
# ── LLM Provider (Pollinations.ai) ─────────────────────
POLLINATIONS_API_KEY=sk_pi4kaulXNxktq6pGu2iOenFLEomriawF
POLLINATIONS_BASE_URL=https://gen.pollinations.ai/v1
POLLINATIONS_MODEL_FULL=openai
POLLINATIONS_MODEL_FAST=nova

# ── Database (Supabase) ────────────────────────────────
SUPABASE_URL=https://cckznjkzsfypssgecyya.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNja3puamt6c2Z5cHNzZ2VjeXlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTUyMjU1MSwiZXhwIjoyMDg3MDk4NTUxfQ.lHx6dvuDeonifBj4GoqIeaAZYGf3g-J2bWTe_wnvifk
SUPABASE_JWT_SECRET=0144dddf-219e-4c2d-b8de-eb2aed6f597d

# ── Redis (from Step 4.2) ──────────────────────────────
# REPLACE THIS WITH YOUR KOYEB REDIS URL:
REDIS_URL=redis://default:YOUR_PASSWORD@hostname.koyeb.app:6379

# ── Frontend URL (CORS) ────────────────────────────────
# Update this after deploying frontend
FRONTEND_URL=http://localhost:3000

# ── Python Settings ────────────────────────────────────
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### 5.2 Replace REDIS_URL

**IMPORTANT:** Replace the `REDIS_URL` line with the actual connection string from Step 4.2.

Example:
```bash
# BEFORE (template):
REDIS_URL=redis://default:YOUR_PASSWORD@hostname.koyeb.app:6379

# AFTER (your actual URL):
REDIS_URL=redis://default:PQo3xKxR9mNpL2vW8yZ@promptforge-redis-abc123.koyeb.app:6379
```

---

## STEP 6: DEPLOY TO KOYEB

### 6.1 Navigate to Project

```powershell
cd C:\Users\user\OneDrive\Desktop\newnew
```

### 6.2 Create Koyeb App

```powershell
koyeb app create promptforge-api
```

**Expected:**
```
✓ Application created
  ID: app_xxxxxxxxxxxxx
  Name: promptforge-api
  URL: https://promptforge-api-xxxxx.koyeb.app
```

### 6.3 Deploy with Docker

```powershell
koyeb service create promptforge-api-service \
  --app promptforge-api \
  --type docker \
  --dockerfile ./Dockerfile \
  --region geo:us-east \
  --port 8000/http
```

**Wait for deployment to start** (2-3 minutes).

### 6.4 Set Environment Variables

**One by one, run these commands:**

```powershell
# LLM Provider
koyeb service update promptforge-api-service \
  --env POLLINATIONS_API_KEY=sk_pi4kaulXNxktq6pGu2iOenFLEomriawF

koyeb service update promptforge-api-service \
  --env POLLINATIONS_BASE_URL=https://gen.pollinations.ai/v1

koyeb service update promptforge-api-service \
  --env POLLINATIONS_MODEL_FULL=openai

koyeb service update promptforge-api-service \
  --env POLLINATIONS_MODEL_FAST=nova

# Supabase
koyeb service update promptforge-api-service \
  --env SUPABASE_URL=https://cckznjkzsfypssgecyya.supabase.co

koyeb service update promptforge-api-service \
  --env SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNja3puamt6c2Z5cHNzZ2VjeXlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTUyMjU1MSwiZXhwIjoyMDg3MDk4NTUxfQ.lHx6dvuDeonifBj4GoqIeaAZYGf3g-J2bWTe_wnvifk

koyeb service update promptforge-api-service \
  --env SUPABASE_JWT_SECRET=0144dddf-219e-4c2d-b8de-eb2aed6f597d

# Redis (USE YOUR ACTUAL URL FROM STEP 4.2)
koyeb service update promptforge-api-service \
  --env REDIS_URL=redis://default:YOUR_PASSWORD@hostname.koyeb.app:6379

# Frontend
koyeb service update promptforge-api-service \
  --env FRONTEND_URL=http://localhost:3000

# Python
koyeb service update promptforge-api-service \
  --env PYTHONUNBUFFERED=1

koyeb service update promptforge-api-service \
  --env PYTHONDONTWRITEBYTECODE=1
```

**After each command, wait for:**
```
✓ Service updated
  Deployment in progress...
```

### 6.5 Watch Deployment Progress

```powershell
koyeb deployment list --app promptforge-api
```

**Wait until status is:**
```
Status: SUCCESSFUL
```

This takes 5-10 minutes. Koyeb is:
1. Pulling your Dockerfile
2. Building the image
3. Starting the container
4. Running health checks

---

## STEP 7: GET YOUR PRODUCTION URL

### 7.1 Get App URL

```powershell
koyeb app get promptforge-api
```

**Copy the URL** — it looks like:
```
https://promptforge-api-xxxxx.koyeb.app
```

**This is your production backend URL!** Save it.

### 7.2 Alternative: List All Apps

```powershell
koyeb app list
```

**Expected:**
```
ID                 NAME              URL                              STATUS
app_xxxxx          promptforge-api   https://promptforge-api-xxx...   RUNNING
```

---

## STEP 8: VERIFY DEPLOYMENT — HEALTH CHECK

### 8.1 Test Health Endpoint

```powershell
curl https://promptforge-api-xxxxx.koyeb.app/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "timestamp": "2026-03-09T..."
}
```

### 8.2 If Health Check Fails

**Check logs:**
```powershell
koyeb logs --app promptforge-api --service promptforge-api-service
```

**Common issues:**

| Error | Fix |
|-------|-----|
| `Connection refused` | Wait 2 more minutes — container still starting |
| `REDIS_URL missing` | Re-run Step 6.4 with correct Redis URL |
| `SUPABASE_KEY invalid` | Check your Supabase service role key |
| `POLLINATIONS_API_KEY invalid` | Verify API key in .env |

---

## STEP 9: TEST WITH REAL API CALL

### 9.1 Generate Test JWT Token

**Run this Python script:**

```python
# File: C:\Users\user\OneDrive\Desktop\newnew\generate_test_token.py

import jwt
import datetime

secret = "0144dddf-219e-4c2d-b8de-eb2aed6f597d"  # SUPABASE_JWT_SECRET

payload = {
    "sub": "00000000-0000-0000-0000-000000000001",  # Test user ID
    "iss": "https://cckznjkzsfypssgecyya.supabase.co",
    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
}

token = jwt.encode(payload, secret, algorithm="HS256")
print(token)
```

**Run it:**
```powershell
python generate_test_token.py
```

**Copy the token** — it's a long string like:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAw...xxx
```

### 9.2 Test /refine Endpoint

```powershell
# Replace YOUR_KOYEB_URL and YOUR_JWT_TOKEN

curl -X POST "https://YOUR_KOYEB_URL/refine" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"write a professional email to my client about the project update\"}"
```

**Expected Response:**
```json
{
  "improved_prompt": "You are a professional communications specialist. Write a clear, concise email...",
  "diff": [...],
  "quality_score": {
    "specificity": 4,
    "clarity": 5,
    "actionability": 4
  },
  "kira_message": "On it. Here's your engineered prompt ↓",
  "memories_applied": 0,
  "latency_ms": 3421
}
```

### 9.3 Test /chat/stream (SSE)

```powershell
curl -X POST "https://YOUR_KOYEB_URL/chat/stream" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"help me write\", \"session_id\": \"test-session-1\"}"
```

**Expected:** Streaming response with events:
```
data: {"type": "status", "data": {"message": "Analyzing intent..."}}
data: {"type": "kira_message", "data": {"message": "On it...", "complete": false}}
...
```

---

## STEP 10: UPDATE FRONTEND ENVIRONMENT

Now connect your frontend to the production backend.

### 10.1 Edit Frontend .env.local

**File:** `C:\Users\user\OneDrive\Desktop\newnew\promptforge-web\.env.local`

**Change these lines:**

```bash
# BEFORE (localhost):
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEMO_API_URL=http://localhost:8000

# AFTER (Koyeb production):
NEXT_PUBLIC_API_URL=https://promptforge-api-xxxxx.koyeb.app
NEXT_PUBLIC_DEMO_API_URL=https://promptforge-api-xxxxx.koyeb.app
```

### 10.2 Restart Frontend Dev Server

```powershell
cd C:\Users\user\OneDrive\Desktop\newnew\promptforge-web
npm run dev
```

### 10.3 Test Frontend with Production Backend

1. Open: http://localhost:3000
2. Try the live demo widget
3. Check browser console for errors
4. Verify API calls go to Koyeb URL, not localhost

**In browser DevTools → Network tab:**
- Request URL should be: `https://promptforge-api-xxxxx.koyeb.app/chat`
- NOT: `http://localhost:8000/chat`

---

## 📊 DEPLOYMENT VERIFICATION CHECKLIST

Run through all of these to confirm success:

```powershell
# 1. Health check
curl https://YOUR_KOYEB_URL/health
# ✅ Expected: {"status": "ok", "version": "2.0.0"}

# 2. Check deployment status
koyeb deployment list --app promptforge-api
# ✅ Expected: Status: SUCCESSFUL

# 3. Check service logs (no errors)
koyeb logs --app promptforge-api --service promptforge-api-service
# ✅ Expected: No ERROR lines in recent logs

# 4. Test refine endpoint (with JWT)
curl -X POST https://YOUR_KOYEB_URL/refine -H "Authorization: Bearer YOUR_TOKEN" -H "Content-Type: application/json" -d "{\"message\": \"test\"}"
# ✅ Expected: JSON response with improved_prompt

# 5. Check Redis connection (in logs)
koyeb logs --app promptforge-api | Select-String "Redis"
# ✅ Expected: "Connected to Redis" or similar success message

# 6. Check Supabase connection (in logs)
koyeb logs --app promptforge-api | Select-String "Supabase"
# ✅ Expected: No connection errors

# 7. Verify CORS headers
curl -I https://YOUR_KOYEB_URL/health
# ✅ Expected: Access-Control-Allow-Origin header present
```

---

## 🔧 TROUBLESHOOTING

### Problem: Deployment stuck in "PROVISIONING"

**Solution:**
```powershell
# Check what's happening
koyeb logs --app promptforge-api --service promptforge-api-service

# Common causes:
# 1. Docker build failed → Check Dockerfile syntax
# 2. Redis not ready → Wait 2 more minutes
# 3. Environment variable missing → Re-run Step 6.4
```

### Problem: Health check fails (502 Bad Gateway)

**Solution:**
```powershell
# Check if app is running
koyeb app get promptforge-api

# Check recent logs for errors
koyeb logs --app promptforge-api --tail 100

# Restart deployment
koyeb service redeploy promptforge-api-service
```

### Problem: Redis connection error

**Solution:**
1. Verify Redis URL format:
   ```bash
   # Correct format:
   redis://default:PASSWORD@hostname.koyeb.app:6379
   ```
2. Check Redis service status:
   ```powershell
   koyeb redis get promptforge-redis
   ```
3. If Redis not ready, wait and redeploy:
   ```powershell
   koyeb service redeploy promptforge-api-service
   ```

### Problem: Supabase RLS error (403)

**Solution:**
- Your JWT token's `sub` claim must match a user in Supabase
- Or use service role key for testing (not recommended for production)
- Check Supabase dashboard → Authentication → Users

### Problem: CORS error in browser

**Solution:**
```powershell
# Update FRONTEND_URL to match your frontend domain
koyeb service update promptforge-api-service \
  --env FRONTEND_URL=https://your-frontend.vercel.app
```

For development (localhost):
```powershell
koyeb service update promptforge-api-service \
  --env FRONTEND_URL=http://localhost:3000
```

---

## 📈 MONITORING & LOGS

### View Real-Time Logs

```powershell
koyeb logs --app promptforge-api --service promptforge-api-service --follow
```

**Exit with:** `Ctrl+C`

### Check Service Status

```powershell
koyeb service get promptforge-api-service
```

**Shows:**
- Current status (RUNNING/DEPLOYING)
- Instance count
- Resource usage
- Environment variables

### Check Deployment History

```powershell
koyeb deployment list --app promptforge-api
```

**Shows:**
- All deployments (last 10)
- Status (SUCCESSFUL/FAILED)
- Deployment time
- Trigger (manual/automatic)

---

## 🔐 SECURITY BEST PRACTICES

### 1. Never Commit .env Files

Your `.env` and `.env.koyeb` are in `.gitignore`:
```bash
# Check .gitignore
cat .gitignore | grep env
# Expected: .env, .env.*, .env.local
```

### 2. Rotate API Keys Regularly

Every 90 days:
1. Generate new Pollinations API key
2. Update in Koyeb:
   ```powershell
   koyeb service update promptforge-api-service \
     --env POLLINATIONS_API_KEY=new_key_here
   ```
3. Redeploy

### 3. Use Koyeb Secrets Manager (Optional)

For production, use Koyeb's built-in secrets:
```powershell
# Create secret
koyeb secret create SUPABASE_KEY --value "your-key"

# Use in service
koyeb service update promptforge-api-service \
  --env SUPABASE_KEY=${secret:SUPABASE_KEY}
```

### 4. Enable HTTPS Only

Koyeb enforces HTTPS by default. Your API is already secure at:
```
https://promptforge-api-xxxxx.koyeb.app
```

---

## 💰 KOYEB PRICING

### Free Tier (What You Get)
- ✅ 1 service (512MB RAM)
- ✅ 1 Redis instance (256MB)
- ✅ 2M requests/month
- ✅ Always-on (no sleep)
- ✅ HTTPS automatic
- ✅ Global CDN

### Paid Tier ($10/month)
- 2GB RAM
- Unlimited requests
- Priority support

### Monitor Usage

```powershell
koyeb usage
```

---

## ✅ NEXT STEPS AFTER DEPLOYMENT

1. **Test thoroughly** — Use Step 9 to verify all endpoints
2. **Update frontend** — Complete Step 10 to connect to production
3. **Monitor for 24 hours** — Check logs daily
4. **Set up alerts** (optional) — Koyeb can email on failures
5. **Continue with Plan 3** — Auth + Onboarding frontend

---

## 📞 SUPPORT

### Koyeb Documentation
- https://docs.koyeb.com/

### Koyeb Discord
- https://discord.gg/koyeb

### Status Page
- https://status.koyeb.com/

---

## 🎯 QUICK REFERENCE COMMANDS

```powershell
# Login
koyeb login

# List apps
koyeb app list

# Get app details
koyeb app get promptforge-api

# View logs
koyeb logs --app promptforge-api --follow

# Redeploy
koyeb service redeploy promptforge-api-service

# Update env var
koyeb service update promptforge-api-service --env KEY=value

# Check Redis
koyeb redis get promptforge-redis

# Check deployments
koyeb deployment list --app promptforge-api
```

---

**Deployment Complete!** ✅

Your backend is now running in production on Koyeb.

**Next:** Return to frontend development (Plan 3 — Auth + Onboarding)

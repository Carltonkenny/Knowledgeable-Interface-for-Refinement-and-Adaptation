# Railway Migration Plan — Safe Migration from Koyeb

**Version:** 1.0  
**Date:** March 18, 2026  
**Status:** READY FOR EXECUTION  
**Estimated Time:** 45-60 minutes

---

## **🎯 OBJECTIVE**

Migrate PromptForge backend from Koyeb to Railway **without downtime** and **with full SSE streaming support**.

---

## **📋 PREREQUISITES CHECKLIST**

Complete these BEFORE starting migration:

- [ ] Railway account created at [railway.app](https://railway.app)
- [ ] GitHub repo connected to Railway
- [ ] Backend code pushed to GitHub (main/master branch)
- [ ] `.env` file accessible (all environment variables)
- [ ] Supabase credentials verified
- [ ] Pollinations API key verified
- [ ] Gemini API key verified
- [ ] Redis URL (Upstash or Railway Redis)

---

## **🚀 MIGRATION STEPS (Execute in Order)**

### **STEP 1: Dockerfile Fix** ✅

**FILE:** `newnew/Dockerfile`

**CHANGE:**
```dockerfile
# OLD (remove this):
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# NEW (use this):
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "75"]
```

**WHY:**
- `--timeout-keep-alive 75` keeps SSE streams alive past Railway's 60s threshold
- Remove `--workers 1` (not needed, uvicorn defaults to 1)
- Railway uses single-worker model by default

**VERIFICATION:**
```bash
cd newnew
docker build -t promptforge-test .
# Expected: Build completes, image size < 500MB
```

---

### **STEP 2: Commit & Push**

```bash
cd C:\Users\user\OneDrive\Desktop\newnew
git add Dockerfile
git commit -m "fix: Add timeout-keep-alive for Railway SSE support"
git push origin master
```

**WHY:** Railway auto-deploys from GitHub main/master branch.

---

### **STEP 3: Railway Project Setup**

1. **Go to** [railway.app](https://railway.app)
2. **Click** "New Project"
3. **Select** "Deploy from GitHub repo"
4. **Choose** your PromptForge repository
5. **Wait** for initial build (5-10 minutes)

**CONFIGURATION:**

In Railway Dashboard → Project Settings:
- **Root Directory:** `newnew` (CRITICAL - this is a monorepo)
- **Start Command:** (leave empty - uses Dockerfile CMD)
- **Healthcheck Path:** `/health`

---

### **STEP 4: Add Environment Variables**

In Railway Dashboard → Variables tab, add these **exactly**:

```bash
# Pollinations API
POLLINATIONS_API_KEY=sk_pi4kaulXNxktq6pGu2iOenFLEomriawF
POLLINATIONS_BASE_URL=https://gen.pollinations.ai/v1
POLLINATIONS_MODEL_FULL=openai
POLLINATIONS_MODEL_FAST=nova

# Supabase
SUPABASE_URL=https://cckznjkzsfypssgecyya.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNja3puamt6c2Z5cHNzZ2VjeXlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTUyMjU1MSwiZXhwIjoyMDg3MDk4NTUxfQ.lHx6dvuDeonifBj4GoqIeaAZYGf3g-J2bWTe_wnvifk
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNja3puamt6c2Z5cHNzZ2VjeXlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTUyMjU1MSwiZXhwIjoyMDg3MDk4NTUxfQ.lHx6dvuDeonifBj4GoqIeaAZYGf3g-J2bWTe_wnvifk
SUPABASE_JWT_SECRET=0144dddf-219e-4c2d-b8de-eb2aed6f597d

# Gemini (for embeddings)
GEMINI_API_KEY=AIzaSyAgsxRosyZCUymtMrfV5C2gt3I9uv8A8Dc

# Redis (Upstash - already configured)
REDIS_URL=rediss://default:AZjkAAIncDE4Yzg3N2NkMDljYTE0YmY1OTQzZjY1MGYyNTg4Y2NmMXAxMzkxNDA=@aware-bluebird-39140.upstash.io:6379

# Frontend URLs (update after Vercel deploy)
FRONTEND_URLS=http://localhost:3000,http://localhost:9000

# Environment
ENVIRONMENT=production
```

**DO NOT ADD:**
- `REDIS_URL` if using Railway Redis plugin (auto-injected)
- Any `PORT` variable (Railway injects automatically)

---

### **STEP 5: Enable Auto-Deploy**

In Railway Dashboard → Settings:
- **Auto Deploy:** Enable
- **Branch:** `master` (or `main`)

**WHY:** From now on, `git push` = automatic deployment. No manual deploys.

---

### **STEP 6: Validate SSE Streaming**

**CRITICAL TEST - DO NOT SKIP**

1. **Get a valid JWT token:**
   - Open browser dev tools (F12)
   - Go to Network tab
   - Log in to your app
   - Find any API request
   - Copy `Authorization: Bearer TOKEN` value

2. **Run curl test:**
```bash
curl -N \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message":"write me a better version of this prompt"}' \
  https://yourapp.up.railway.app/stream
```

**EXPECTED OUTPUT:**
```
data: {"token":"Write"}
data: {"token":" me"}
data: {"token":" a"}
...
data: [DONE]
```

**PASS CRITERIA:**
- ✅ Tokens appear **one by one** in terminal
- ✅ Complete response in < 30 seconds

**FAIL CRITERIA:**
- ❌ Nothing for 10+ seconds, then everything at once
- ❌ 500 error
- ❌ Connection timeout

**IF FAIL:**
1. Check `X-Accel-Buffering: no` header in `routes/prompts.py`
2. Check Dockerfile has `--timeout-keep-alive 75`
3. Check Railway logs for errors

---

### **STEP 7: Update Frontend**

**FILE:** `promptforge-web/.env.local`

```bash
# OLD:
NEXT_PUBLIC_API_URL=http://localhost:8000

# NEW:
NEXT_PUBLIC_API_URL=https://yourapp.up.railway.app
NEXT_PUBLIC_USE_MOCKS=false
```

**TEST:**
```bash
cd promptforge-web
npm run dev
```

1. Open http://localhost:3000
2. Log in
3. Go to chat
4. Send a real prompt
5. **Verify:** Streaming works, no console errors

---

### **STEP 8: Update CORS (Supabase)**

**In Supabase Dashboard:**
1. Go to Authentication → URL Configuration
2. Add Railway URL to allowed origins:
   - `https://yourapp.up.railway.app`
3. Save

**In Backend `.env`:**
```bash
# Update after Vercel frontend deploy:
FRONTEND_URLS=https://your-app.vercel.app,http://localhost:3000
```

---

### **STEP 9: Decommission Koyeb**

**ONLY AFTER RAILWAY PASSES ALL TESTS:**

1. **In Koyeb Dashboard:**
   - Go to your service
   - Click "Delete Service"
   - Confirm

2. **Update test files:**
   - Search for `koyeb.app` in codebase
   - Update to Railway URL

3. **Update Supabase CORS:**
   - Remove Koyeb URL from allowed origins

---

## **🔍 VERIFICATION CHECKLIST**

After completing migration, verify ALL of these:

- [ ] **Dockerfile updated** - `--timeout-keep-alive 75` present
- [ ] **GitHub pushed** - Latest commit visible in Railway
- [ ] **Railway build successful** - Green checkmark in dashboard
- [ ] **Health endpoint works** - `curl https://yourapp.up.railway.app/health` returns `{"status":"ok"}`
- [ ] **SSE streaming works** - Curl test shows token-by-token output
- [ ] **Frontend connects** - No CORS errors in browser console
- [ ] **Auth works** - Can log in via frontend
- [ ] **Chat works** - Can send prompt, see streaming response
- [ ] **Memory works** - `memories_applied > 0` in console
- [ ] **Koyeb deleted** - Service removed from Koyeb dashboard

---

## **🚨 ROLLBACK PLAN (If Migration Fails)**

If Railway fails and you need to rollback:

1. **Keep Koyeb running** - Do NOT delete until Railway verified
2. **Revert frontend `.env.local`:**
   ```bash
   NEXT_PUBLIC_API_URL=https://your-old-koyeb-app.koyeb.app
   ```
3. **Debug Railway:**
   - Check Railway logs (Dashboard → Deployments → View Logs)
   - Check environment variables (Dashboard → Variables)
   - Re-run curl test
4. **Retry migration** after fixing issues

---

## **📊 SUCCESS METRICS**

Migration is **SUCCESSFUL** when:

| Metric | Target | How to Check |
|--------|--------|--------------|
| SSE Latency | < 30s for full response | Curl test |
| First Token | < 3 seconds | Curl test |
| Uptime | > 99% | Better Stack monitor |
| Error Rate | < 1% | Sentry dashboard |
| Frontend Load | < 2 seconds | Browser dev tools |

---

## **🆘 TROUBLESHOOTING**

### **Problem: Build Fails**

**Check:**
1. Root directory set to `newnew`?
2. Dockerfile exists at `newnew/Dockerfile`?
3. `requirements.txt` at `newnew/requirements.txt`?

**Fix:**
```bash
cd newnew
docker build -t test .
# Fix any local build errors
git push
```

---

### **Problem: SSE Not Streaming**

**Symptoms:**
- Curl test shows nothing for 10+ seconds, then everything at once

**Check:**
1. `X-Accel-Buffering: no` header in `routes/prompts.py`?
2. Dockerfile has `--timeout-keep-alive 75`?
3. Generator yields inside loop (not after)?

**Fix:**
```python
# routes/prompts.py must have:
return StreamingResponse(
    generate(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # ← THIS
        "Connection": "keep-alive",
    }
)
```

---

### **Problem: CORS Errors**

**Symptoms:**
- Browser console: "Access-Control-Allow-Origin" error

**Check:**
1. `FRONTEND_URLS` in Railway env vars includes frontend URL?
2. Supabase CORS includes Railway URL?

**Fix:**
```bash
# Railway env var:
FRONTEND_URLS=https://your-app.vercel.app,http://localhost:3000
```

---

### **Problem: Redis Connection Failed**

**Symptoms:**
- Logs show: "Redis connection failed"

**Check:**
1. `REDIS_URL` in Railway env vars?
2. Using Upstash URL format (`rediss://` with `@`)?

**Fix:**
- Use Railway Redis plugin OR
- Keep Upstash URL in env vars

---

## **📝 POST-MIGRATION TASKS**

After successful migration:

1. **Add monitoring:**
   - Sentry for error tracking (Move 2)
   - Better Stack for uptime (Move 2)
   - Axiom for log aggregation (Move 2)

2. **Update documentation:**
   - README.md with new Railway URL
   - Team docs with deployment instructions

3. **Clean up:**
   - Delete Koyeb service
   - Remove Koyeb references from test files
   - Update any hardcoded URLs

---

## **✅ CHECK-IN REPORT TEMPLATE**

After completing migration, fill this out:

```
RAILWAY MIGRATION REPORT
========================

Date: [DATE]
Migrated by: [YOUR NAME]

TASKS COMPLETED:
1. Dockerfile fixed — yes/no
2. GitHub pushed — yes/no
3. Railway project created — yes/no
4. Environment variables added — yes/no (count: X)
5. Auto-deploy enabled — yes/no
6. SSE curl test — PASS/FAIL
7. Frontend test — PASS/FAIL
8. CORS updated — yes/no
9. Koyeb deleted — yes/no

METRICS:
- Build time: X minutes
- First token latency: X seconds
- Full response latency: X seconds
- Image size: X MB

ISSUES ENCOUNTERED:
[List any issues and how you fixed them]

NEXT STEPS:
[List any follow-up tasks needed]
```

---

## **🎯 SUMMARY**

**This migration is SAFE because:**

1. ✅ **Koyeb stays running** until Railway verified
2. ✅ **Zero downtime** - frontend can switch URLs instantly
3. ✅ **Auto-deploy** - future deploys are `git push` only
4. ✅ **SSE optimized** - `--timeout-keep-alive 75` prevents drops
5. ✅ **Rollback ready** - can switch back to Koyeb in 2 minutes

**Estimated time:** 45-60 minutes  
**Risk level:** LOW (Koyeb remains until verified)  
**Complexity:** LOW (follow steps in order)

---

**READY TO EXECUTE. Start with STEP 1 (Dockerfile fix).**

# Railway Migration — Execution Checklist

**Version:** 1.0  
**Date:** March 18, 2026  
**Status:** READY TO EXECUTE  
**Estimated Time:** 30-45 minutes

---

## **📋 PRE-MIGRATION CHECKLIST**

Complete these BEFORE touching Railway:

- [ ] **Dockerfile fixed** — `--timeout-keep-alive 75` added ✅
- [ ] **Git committed** — Changes pushed to GitHub ✅
- [ ] **Railway account** — Created at [railway.app](https://railway.app) ❌
- [ ] **`.env` file accessible** — All values ready ❌
- [ ] **Koyeb still running** — Do NOT delete until verified ✅

---

## **🚀 EXECUTION STEPS (Do in Order)**

### **STEP 1: Create Railway Project** (5 mins)

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your PromptForge repository
5. **Wait** for build (5-10 mins)

**CONFIGURE:**
- Dashboard → Settings → **Root Directory:** `newnew`
- **Start Command:** (leave empty)

---

### **STEP 2: Add Environment Variables** (10 mins)

Dashboard → Variables → Add these **exactly**:

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

# Gemini
GEMINI_API_KEY=AIzaSyAgsxRosyZCUymtMrfV5C2gt3I9uv8A8Dc

# Redis (Upstash)
REDIS_URL=rediss://default:AZjkAAIncDE4Yzg3N2NkMDljYTE0YmY1OTQzZjY1MGYyNTg4Y2NmMXAxMzkxNDA=@aware-bluebird-39140.upstash.io:6379

# Frontend
FRONTEND_URLS=http://localhost:3000,http://localhost:9000

# Environment
ENVIRONMENT=production
```

---

### **STEP 3: Enable Auto-Deploy** (2 mins)

Dashboard → Settings:
- **Auto Deploy:** Enable
- **Branch:** `master`

---

### **STEP 4: Validate Deployment** (5 mins)

**Wait for:**
- Green checkmark in Railway dashboard
- "Deployed" status

**Get your Railway URL:**
- Dashboard → Copy URL (e.g., `https://yourapp.up.railway.app`)

---

### **STEP 5: SSE Validation Test** (CRITICAL - 5 mins)

**1. Get JWT token:**
- Open browser (currently running app)
- F12 → Network tab
- Find any API request
- Copy `Authorization: Bearer TOKEN` value

**2. Run curl test:**
```bash
curl -N \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message":"write a python function"}' \
  https://YOUR_RAILWAY_URL.up.railway.app/stream
```

**PASS:** Tokens appear one-by-one:
```
data: {"token":"Write"}
data: {"token":" a"}
data: {"token":" python"}
...
data: [DONE]
```

**FAIL:** Nothing for 10s, then all at once → Check headers in `routes/prompts.py`

---

### **STEP 6: Health Check** (2 mins)

```bash
curl https://YOUR_RAILWAY_URL.up.railway.app/health
```

**Expected:**
```json
{"status":"ok","version":"2.0.0"}
```

---

### **STEP 7: Update Frontend** (5 mins)

**FILE:** `promptforge-web/.env.local`

```bash
# OLD:
NEXT_PUBLIC_API_URL=http://localhost:8000

# NEW:
NEXT_PUBLIC_API_URL=https://YOUR_RAILWAY_URL.up.railway.app
NEXT_PUBLIC_USE_MOCKS=false
```

**TEST:**
```bash
cd promptforge-web
npm run dev
```

1. Open http://localhost:3000
2. Log in
3. Send prompt
4. **Verify:** Streaming works, no console errors

---

### **STEP 8: Update CORS** (3 mins)

**Backend `.env`:**
```bash
# After Vercel frontend deploy:
FRONTEND_URLS=https://your-app.vercel.app,http://localhost:3000
```

**Supabase Dashboard:**
- Authentication → URL Configuration
- Add: `https://YOUR_RAILWAY_URL.up.railway.app`

---

### **STEP 9: Decommission Koyeb** (ONLY AFTER ALL TESTS PASS)

1. **Supabase CORS:** Remove Koyeb URL
2. **Koyeb Dashboard:** Delete service
3. **Test files:** Update `tests/adhoc/test_*.py` URLs

---

## **✅ VERIFICATION CHECKLIST**

After migration, verify ALL:

- [ ] Dockerfile has `--timeout-keep-alive 75`
- [ ] Railway build successful (green checkmark)
- [ ] Health endpoint returns `{"status":"ok"}`
- [ ] SSE curl test shows token-by-token output
- [ ] Frontend connects (no CORS errors)
- [ ] Auth works (can log in)
- [ ] Chat works (can send prompts)
- [ ] Memory works (`memories_applied > 0`)
- [ ] Koyeb deleted

---

## **🚨 ROLLBACK (If Fails)**

1. **Keep Koyeb running**
2. **Revert frontend `.env.local`:**
   ```bash
   NEXT_PUBLIC_API_URL=https://your-koyeb-app.koyeb.app
   ```
3. **Debug Railway logs**
4. **Retry after fixing**

---

## **📊 SUCCESS METRICS**

| Metric | Target | How to Check |
|--------|--------|--------------|
| Build time | < 10 mins | Railway dashboard |
| First token | < 3 seconds | Curl test |
| Full response | < 30 seconds | Curl test |
| Uptime | > 99% | Better Stack (Move 2) |

---

## **📝 POST-MIGRATION**

After successful migration:

1. **Add Sentry** (Move 2 - 30 mins)
2. **Add Better Stack** (Move 2 - 5 mins)
3. **Update team docs** with Railway URL
4. **Celebrate** 🎉

---

**READY TO EXECUTE. Start with STEP 1 now.**

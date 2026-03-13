# CRITICAL FIXES REQUIRED — Frontend Visual Collapse

**Date:** 2026-03-12
**Priority:** 🔴 **BLOCKING**
**Impact:** 100% of UI styling broken, SSE streaming failing

---

## 🔴 ROOT CAUSE IDENTIFIED

### Problem 1: Tailwind Directives Missing from globals.css

**Current state:**
```css
/* styles/globals.css — LINE 1 */
@import url('https://fonts.googleapis.com/...');
```

**Problem:** **Tailwind CSS is NEVER imported!** The file jumps straight into `:root` variables without including Tailwind's base, components, and utilities.

**Why this breaks everything:**
- No Tailwind reset/normalize → browser default styles
- No utility classes → `className="flex items-center"` does nothing
- No component classes → all Tailwind component styles ignored
- Result: Raw HTML rendering at top-left with zero spacing

**Evidence from your video:**
- Frame 80, 106: Chat UI crammed in top-left
- All screens: Zero margins, zero padding, zero layout
- Forms: Native browser styling (no Tailwind reset)
- LiveDemoWidget: Not visible (utility classes not working)

---

### Problem 2: Backend Connection Failing

**Test Result:**
```bash
$ curl https://parallel-eartha-student798-9c3bce6b.koyeb.app/chat/stream \
  -H "Authorization: Bearer ..." \
  -d '{"message":"test"}'

# Response: {"detail":"Not authenticated"}
# Then: Connection timeout
```

**Issues:**
1. **JWT validation failing** — Anon key not accepted (needs user JWT)
2. **Connection timeout** — Koyeb backend sleeping (free tier) or network issue
3. **CORS likely misconfigured** — `FRONTEND_URL=http://localhost:9000` but dev runs on `:3000`

**Why SSE fails:**
- `NEXT_PUBLIC_USE_MOCKS=false` → tries real backend
- Backend unreachable → `parseStream()` throws
- `useKiraStream.ts:205` catches error → logs via `logger.error()`
- User sees: `[PromptForge] "Stream failed" {}`

---

## ✅ THE FIXES

### Fix 1: Add Tailwind Directives (2 MINUTES)

**File:** `promptforge-web/styles/globals.css`

**Add these 3 lines at the VERY TOP:**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Satoshi:wght@300;400;500;700&display=swap');

:root {
  /* ... rest of file unchanged ... */
}
```

**What this does:**
- `@tailwind base:` → Preflight reset (removes browser defaults)
- `@tailwind components:` → Component classes (if any custom)
- `@tailwind utilities:` → ALL utility classes (`flex`, `grid`, `px-4`, etc.)

**Expected result:**
- Instant visual transformation
- All spacing/margins/colors applied
- Cards have proper styling
- Layout grids work correctly
- Buttons styled properly

---

### Fix 2: Clear Next.js Cache (1 MINUTE)

**Commands:**
```bash
cd promptforge-web
rm -rf .next
npm run dev
```

**Why:** `.next` folder has cached build with old CSS. Removing forces fresh compile.

---

### Fix 3: Enable Mock Mode for Development (30 SECONDS)

**File:** `promptforge-web/.env.local`

**Change:**
```env
# FROM
NEXT_PUBLIC_USE_MOCKS=false

# TO
NEXT_PUBLIC_USE_MOCKS=true
```

**Why:**
- Backend on Koyeb free tier sleeps after 15min inactivity
- Takes 30-60 seconds to wake up (cold start)
- During development, you need instant feedback
- Mocks provide full chat flow without backend
- Flip to `false` only for final production test

**What mocks provide:**
- Full SSE simulation with realistic timing
- Mock chat results with diff, quality scores
- Mock history and profile data
- All UI states testable (loading, result, error, rate limit)

---

### Fix 4: Update CORS Backend URL (2 MINUTES)

**File:** `promptforge/.env`

**Change:**
```env
# FROM
FRONTEND_URL=http://localhost:9000

# TO
FRONTEND_URL=http://localhost:3000
```

**Why:** Next.js dev server runs on port 3000 by default, not 9000.

**Then redeploy backend:**
```bash
cd C:\Users\user\OneDrive\Desktop\newnew
# If using Railway
railway up

# If using Koyeb
# Redeploy via dashboard or CLI
```

---

### Fix 5: Generate Valid User JWT for Testing (5 MINUTES)

**Problem:** The token you're using is the **anon key**, not a user JWT.

**Solution:** Create a test user and generate JWT:

**Option A: Via Supabase Dashboard**
1. Go to https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/users
2. Click "Add user" → "Create new user"
3. Email: `test@promptforge.local`, Password: `test123456`
4. Use email/password login in frontend to get valid JWT

**Option B: Via Signup Flow**
1. Frontend: Navigate to `/signup`
2. Sign up with any email/password
3. Check Supabase dashboard for the user
4. Their session JWT is valid for testing

**Option C: Generate JWT Programmatically**
```python
# generate_test_token.py
import jwt
from datetime import datetime, timezone, timedelta

secret = "0144dddf-219e-4c2d-b8de-eb2aed6f597d"  # SUPABASE_JWT_SECRET
payload = {
    "sub": "test-user-123",
    "iss": "https://cckznjkzsfypssgecyya.supabase.co",
    "iat": int(datetime.now(timezone.utc).timestamp()),
    "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    "role": "authenticated"
}

token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Test JWT: {token}")
```

---

## 🎯 VERIFICATION CHECKLIST

After applying fixes:

```bash
# 1. Check Tailwind directives added
cd promptforge-web
head -5 styles/globals.css
# Should show: @tailwind base/components/utilities

# 2. Cache cleared
ls -la .next
# Should NOT exist

# 3. Dev server running
npm run dev
# Should compile successfully

# 4. Mock mode enabled
cat .env.local | grep MOCKS
# Should show: NEXT_PUBLIC_USE_MOCKS=true

# 5. Visit localhost:3000
# Landing page should be FULLY STYLED:
# - Dark background (#070809)
# - Gradient hero section
# - Styled buttons
# - Proper spacing
# - Cards with borders

# 6. Test chat flow
# Navigate to /app
# Type prompt
# Should see full SSE simulation with chips, Kira message, output card
```

---

## 📊 WHY YOUR AGENT NOTICED THESE ISSUES

### Visual Report Analysis

**What the agent saw:**
```
Frame 80, 106:
- Raw HTML at top-left
- Zero Tailwind classes applied
- Native browser file input
- Missing all styling

Frame 100:
- Logger error from useKiraStream
- SSE connection failed
- Backend unreachable
```

**Agent's diagnosis:**
> "Tailwind isn't being applied. Everything is rendering at the top-left corner, zero spacing, zero card styling, zero layout."

**Root cause identified:**
- `globals.css` missing `@tailwind` directives
- Tailwind config correct, but never imported
- CSS variables defined but no utility classes available

**Agent's second observation:**
> "[PromptForge] 'Stream failed' {} — this is useKiraStream failing when you tried to send a prompt."

**Root cause:**
- `NEXT_PUBLIC_USE_MOCKS=false`
- Backend unreachable (sleeping or CORS)
- SSE connection times out
- Error logged via `logger.error()`

---

## 🔧 MANUAL FIX STEPS

### Step 1: Edit globals.css
```bash
cd C:\Users\user\OneDrive\Desktop\newnew\promptforge-web
notepad styles/globals.css
```

Add at line 1:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Save and close.

### Step 2: Clear Cache
```bash
cd C:\Users\user\OneDrive\Desktop\newnew\promptforge-web
rmdir /s /q .next
```

### Step 3: Update .env.local
```bash
notepad .env.local
```

Change:
```env
NEXT_PUBLIC_USE_MOCKS=true
```

Save and close.

### Step 4: Restart Dev Server
```bash
npm run dev
```

Wait for "Ready in Xms" message.

### Step 5: Verify
Open http://localhost:3000

**Expected:**
- ✅ Dark background
- ✅ Gradient hero section
- ✅ Styled buttons
- ✅ Proper typography
- ✅ All spacing correct

**If still broken:**
- Check browser DevTools Console for errors
- Check Network tab for failed CSS requests
- Verify Tailwind is compiling (look for Tailwind in DevTools Styles panel)

---

## 🎯 BACKEND CONNECTION TEST

After frontend fixed, test real backend:

```bash
# 1. Wake up backend
curl https://parallel-eartha-student798-9c3bce6b.koyeb.app/health

# Expected: {"status":"ok","version":"2.0.0"}
# If timeout: Backend sleeping, wait 30s and retry

# 2. Flip to real backend
# Edit .env.local:
NEXT_PUBLIC_USE_MOCKS=false

# 3. Restart dev server
# npm run dev

# 4. Sign up and get valid JWT
# Navigate to /signup
# Create account
# Check browser localStorage for session

# 5. Test chat
# Navigate to /app
# Send prompt
# Should see real SSE stream from backend
```

---

## 📈 EXPECTED TRANSFORMATION

### Before Fixes:
```
[Raw HTML at top-left]
- No background color
- No spacing
- No cards
- No buttons styled
- Native file input
- Text everywhere
```

### After Fixes:
```
[Fully styled PromptForge UI]
- Dark background (#070809)
- Gradient hero section
- Cards with borders and shadows
- Buttons with hover states
- Styled input with icons
- Proper typography hierarchy
- All animations working
```

---

## ⏱️ TIME ESTIMATE

| Fix | Time |
|-----|------|
| Add Tailwind directives | 2 min |
| Clear cache | 1 min |
| Update .env.local | 30 sec |
| Restart dev server | 2 min |
| Verify visually | 5 min |
| **Total** | **~10 minutes** |

---

## 🚨 URGENCY

**Current State:** 🔴 **BLOCKING**
- Cannot develop UI without styling
- Cannot test SSE without backend/mocks
- Agent cannot verify contract compliance

**After Fixes:** ✅ **READY FOR DEVELOPMENT**
- Full UI styling working
- Mock chat flow functional
- Can build remaining components (InputBar, EmptyState, etc.)

---

**Next Action:** Apply Fix 1 (Tailwind directives) immediately.

**Status:** Awaiting fix application

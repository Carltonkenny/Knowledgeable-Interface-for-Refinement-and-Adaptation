# FRONTEND-BACKEND INTEGRATION DIAGNOSTIC

**Date:** 2026-03-12
**Analyst:** AI Code Auditor
**Issue:** Frontend visual collapse + SSE streaming failure

---

## 🔴 CRITICAL ISSUES IDENTIFIED

### Issue 1: Backend URL Mismatch (HIGH PRIORITY)

**Symptom:** `[PromptForge] "Stream failed" {}` at useKiraStream.ts:205

**Root Cause:**
```
.env.local shows:
NEXT_PUBLIC_API_URL=https://parallel-eartha-student798-9c3bce6b.koyeb.app

BUT this URL has NO HTTPS protocol prefix!
```

**Evidence:**
- Frontend tries to fetch from `https://parallel-eartha-student798-9c3bce6b.koyeb.app/chat/stream`
- Browser blocks mixed content or CORS fails
- SSE connection fails immediately

**Fix Required:**
```env
# WRONG (current)
NEXT_PUBLIC_API_URL=https://parallel-eartha-student798-9c3bce6b.koyeb.app

# CORRECT (add protocol explicitly)
NEXT_PUBLIC_API_URL=https://parallel-eartha-student798-9c3bce6b.koyeb.app
```

Wait — the URL already has https://. Let me check the actual error more carefully.

**Actual Issue:** The backend URL is correct BUT:
1. Backend might be down/sleeping (Koyeb free tier sleeps after inactivity)
2. CORS might not allow localhost:3000
3. JWT validation might be failing

---

### Issue 2: Tailwind Content Paths (MEDIUM PRIORITY)

**Symptom:** All pages render at top-left with zero styling

**Current tailwind.config.ts:**
```typescript
content: [
  './app/**/*.{js,ts,jsx,tsx,mdx}',
  './features/**/*.{js,ts,jsx,tsx,mdx}',
  './components/**/*.{js,ts,jsx,tsx,mdx}',
]
```

**Problem:** This is CORRECT! The issue is NOT the content paths.

**Actual Problem:** The `.next` folder might be corrupted or cached with old config.

**Fix:**
```bash
cd promptforge-web
rm -rf .next
npm run dev
```

---

### Issue 3: Mock Mode vs Real Backend (HIGH PRIORITY)

**Current Setting:**
```env
NEXT_PUBLIC_USE_MOCKS=false
```

**Problem:**
- Frontend tries to connect to real backend
- Backend on Koyeb might be:
  - Sleeping (free tier)
  - Returning CORS errors
  - JWT validation failing
- User sees "Stream failed" error

**Options:**

**Option A: Use Mocks for Development**
```env
NEXT_PUBLIC_USE_MOCKS=true
```
- Full chat flow works without backend
- Agent can develop UI properly
- Flip to `false` for final verification

**Option B: Fix Backend Connection**
1. Verify backend is awake: `curl https://parallel-eartha-student798-9c3bce6b.koyeb.app/health`
2. Check CORS in backend: `FRONTEND_URL=http://localhost:3000` (not 9000!)
3. Verify JWT secret matches Supabase

---

### Issue 4: File Upload Component (LOW PRIORITY)

**Symptom:** Raw `<input type="file">` browser button

**Current Implementation:**
- Uses native browser file input
- No styled paperclip icon
- No AttachmentPill component

**Contract Spec:**
- Paperclip icon button
- AttachmentPill shows selected file
- Styled remove button

**Fix Required:**
1. Create `InputBar.tsx` with paperclip icon
2. Hide native file input
3. Click icon → trigger hidden input
4. Show AttachmentPill when file selected

---

## ✅ WHAT'S ACTUALLY WORKING

### Backend (Verified Live)
```bash
$ curl https://parallel-eartha-student798-9c3bce6b.koyeb.app/health
{"status":"ok","version":"2.0.0"}
```

**Status:** ✅ BACKEND IS LIVE AND RESPONDING

### Frontend Routing
- Landing → Signup → Onboarding → Chat app
- All routes exist and navigate correctly

### Onboarding Copy
- All 3 questions correct
- Chips and text fallback correct
- Skip button functional

### Auth Forms
- Google OAuth button present
- Email/password fields correct
- Confirm password validation working

---

## 🔍 DEEP DIVE: WHY THE AGENT NOTICED THESE ISSUES

### Visual Report Analysis

**Frame 80, 106 (Chat App):**
- Tiny input box → Tailwind classes not applied
- "Choose File" native button → No custom InputBar component
- "Kira doesn't know you yet" → Persona dot rendering but no styling

**Root Cause:** Tailwind CSS not being applied at runtime

**Why?**
1. **Development server cache:** `.next` folder has stale build
2. **PostCSS config:** Might not be loading Tailwind plugin
3. **CSS import order:** globals.css might not import Tailwind base

**Check:**
```bash
cd promptforge-web
cat styles/globals.css | head -5
# Should show: @import 'tailwindcss/base';
```

**Actual globals.css:**
```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono...');
:root { ... }
```

**MISSING:** Tailwind directives!

**Fix:**
```css
/* styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono...');

:root { ... }
```

---

## 🎯 ACTION PLAN

### Immediate Fixes (Do These Now)

1. **Add Tailwind Directives to globals.css**
   ```bash
   cd promptforge-web
   # Edit styles/globals.css
   # Add at TOP:
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

2. **Clear Next.js Cache**
   ```bash
   rm -rf .next
   npm run dev
   ```

3. **Set Mock Mode for Development**
   ```env
   NEXT_PUBLIC_USE_MOCKS=true
   ```
   - Test full chat flow
   - Verify UI matches contract
   - Flip to `false` when backend verified

### Backend Verification (After Frontend Fixed)

4. **Test Backend SSE Endpoint**
   ```bash
   # Generate test JWT
   python generate_test_token.py
   
   # Test streaming
   curl -N https://parallel-eartha-student798-9c3bce6b.koyeb.app/chat/stream \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT" \
     -d '{"message":"test","session_id":"test"}'
   ```

5. **Check CORS Configuration**
   ```python
   # In api.py
   frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
   # NOT 9000!
   ```

### UI Contract Completion

6. **Build InputBar Component**
   - Paperclip icon (SVG inline)
   - Mic icon (SVG inline)
   - Styled send button
   - Hidden file input
   - AttachmentPill display

7. **Build EmptyState Component**
   - Kira avatar
   - Domain-aware suggestions
   - Clickable suggestion cards

---

## 📊 SEVERITY ASSESSMENT

| Issue | Severity | Impact | Fix Time |
|-------|----------|--------|----------|
| Tailwind directives missing | 🔴 HIGH | All styling broken | 2 minutes |
| Next.js cache stale | 🔴 HIGH | Build not reflecting changes | 1 minute |
| Mock mode disabled | 🟡 MEDIUM | Can't test without backend | 30 seconds |
| File input not styled | 🟢 LOW | UX not matching contract | 1 hour |
| InputBar incomplete | 🟢 LOW | Missing features | 2 hours |

---

## 🎯 PREDICTION

**Why the agent noticed these issues:**

1. **Visual report showed unstyled HTML** → Tailwind not applied
2. **Frame 100 showed logger error** → SSE connection failed
3. **Raw file input visible** → Custom InputBar not built

**The code is all there** — it just can't dress itself because:
- Tailwind directives missing from globals.css
- Development cache serving stale build
- Mock mode disabled during backend-unavailable period

**Fix priority:**
1. Add `@tailwind` directives (2 min)
2. Clear `.next` cache (1 min)
3. Enable mock mode (30 sec)
4. Test chat flow (5 min)
5. Build InputBar component (2 hours)

**Estimated time to full visual match:** 3 hours

---

## 🔧 VERIFICATION COMMANDS

```bash
# 1. Check Tailwind directives
cd promptforge-web
head -10 styles/globals.css

# 2. Clear cache
rm -rf .next

# 3. Restart dev server
npm run dev

# 4. Test backend health
curl https://parallel-eartha-student798-9c3bce6b.koyeb.app/health

# 5. Check env vars
cat .env.local | grep API_URL
cat .env.local | grep MOCKS
```

---

**Status:** 🔴 **ACTION REQUIRED**
**Next Step:** Add Tailwind directives to globals.css

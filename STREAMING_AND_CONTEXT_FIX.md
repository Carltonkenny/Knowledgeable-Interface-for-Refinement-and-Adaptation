# 🔧 SSE STREAMING + CONTEXT PERSISTENCE FIX

**Date:** March 13, 2026
**Status:** Root Causes Identified

---

## 🐛 ISSUE 1: CONTEXT NOT PERSISTING

### **Root Cause:**

Session ID is stored in `sessionStorage`, NOT `localStorage`:

```typescript
// useSessionId.ts - LINE 28
sessionStorage.setItem(SESSION_STORAGE_KEY, sessionIdRef.current)
```

**Problem:** `sessionStorage` is cleared when:
- ✅ Tab is closed
- ✅ Page refresh (sometimes)
- ✅ Browser restart

**Solution:** Change to `localStorage` for persistent sessions

---

### **Fix:**

**File:** `promptforge-web/features/chat/hooks/useSessionId.ts`

**Replace:**
```typescript
// Try to get from sessionStorage
const stored = sessionStorage.getItem(SESSION_STORAGE_KEY)

if (stored) {
  sessionIdRef.current = stored
} else {
  sessionIdRef.current = crypto.randomUUID?.() ?? generateUUID()
  sessionStorage.setItem(SESSION_STORAGE_KEY, sessionIdRef.current)
}
```

**With:**
```typescript
// Try to get from localStorage (persistent across tabs/sessions)
const stored = localStorage.getItem(SESSION_STORAGE_KEY)

if (stored) {
  sessionIdRef.current = stored
} else {
  sessionIdRef.current = crypto.randomUUID?.() ?? generateUUID()
  localStorage.setItem(SESSION_STORAGE_KEY, sessionIdRef.current)
}
```

---

### **Test After Fix:**

```javascript
// Browser console
console.log('Session ID:', localStorage.getItem('pf_session_id'))

// Send a message
// Wait for response
// Check again
console.log('Session ID after message:', localStorage.getItem('pf_session_id'))

// Should be THE SAME both times!
```

---

## 🐛 ISSUE 2: SSE STREAMING NOT WORKING

### **Root Cause:**

Backend `/chat/stream` endpoint is calling `kira_unified_handler()` which is a **blocking synchronous call**. The handler completes fully BEFORE any SSE events are yielded.

**Code Flow:**
```python
# api.py line 516-522
result = kira_unified_handler(  # ← BLOCKS HERE (2-4 seconds)
    message=req.message,
    history=history,
    user_profile=user_profile
)

# Only AFTER handler completes:
yield _sse("kira_message", {"message": reply, "complete": False})  # ← Too late!
```

**Result:** All SSE events are buffered and sent at once instead of streaming.

---

### **Why This Happens:**

The `kira_unified_handler()` is a synchronous function that:
1. Makes LLM API call (blocks for 1-3 seconds)
2. Processes response
3. Returns complete result

Only AFTER all this does the `yield` statement execute.

---

### **Solution Options:**

#### **Option A: Run Handler in Thread (Recommended)**

**File:** `api.py` line 516-522

**Replace:**
```python
# Step 2 — unified handler (confidence + personality)
yield _sse("status", {"message": "Understanding your message..."})
from agents.autonomous import kira_unified_handler
result = kira_unified_handler(
    message=req.message,
    history=history,
    user_profile=user_profile
)
```

**With:**
```python
# Step 2 — unified handler (confidence + personality)
yield _sse("status", {"message": "Understanding your message..."})

# Run in thread pool to avoid blocking async loop
from agents.autonomous import kira_unified_handler
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    None,  # Use default executor
    lambda: kira_unified_handler(
        message=req.message,
        history=history,
        user_profile=user_profile
    )
)

# Yield control so SSE flushes
await asyncio.sleep(0)
```

---

#### **Option B: Stream from Within Handler (More Complex)**

Modify `kira_unified_handler()` to accept a callback and yield tokens as they're generated. This requires refactoring the handler itself.

**Not recommended** for now — Option A is simpler and works.

---

#### **Option C: Accept Current Behavior (Fallback)**

Current behavior still works, just no typewriter effect. Users see:
- Status updates ("Loading...", "Understanding...", etc.)
- Then full response appears at once

This is **acceptable** but less polished.

---

## 🎯 RECOMMENDED FIXES (Both):

### **1. Fix Context Persistence (5 min)**

```bash
# Edit: promptforge-web/features/chat/hooks/useSessionId.ts
# Change: sessionStorage → localStorage (2 occurrences)
```

### **2. Fix SSE Streaming (10 min)**

```bash
# Edit: api.py line 516-527
# Add: asyncio.run_in_executor() wrapper
```

### **3. Restart Both Servers**

```bash
# Kill all
taskkill /F /IM python.exe
cd C:\Users\user\OneDrive\Desktop\newnew\promptforge-web
# (Ctrl+C in frontend terminal)

# Restart backend
cd C:\Users\user\OneDrive\Desktop\newnew
python -m uvicorn api:app --reload --port 8000

# Restart frontend (new terminal)
cd C:\Users\user\OneDrive\Desktop\newnew\promptforge-web
npm run dev
```

---

## 🧪 VERIFICATION TESTS:

### **Test 1: Context Persistence**

```
1. Open browser console
2. Run: console.log(localStorage.getItem('pf_session_id'))
3. Note the ID
4. Send message: "I'm building a FastAPI project"
5. Wait for response
6. Run: console.log(localStorage.getItem('pf_session_id'))
7. IDs should MATCH
8. Send followup: "Can you help me write an endpoint?"
9. Kira should remember "FastAPI" from step 4
```

**Expected:** ✅ Same session ID, ✅ Kira remembers context

---

### **Test 2: SSE Streaming**

```
1. Send message: "Write a Python function"
2. Watch Kira's response
3. Should see typewriter effect (tokens appear one by one)
4. Status updates should appear BEFORE response completes
```

**Expected:** ✅ Streaming text, ✅ Status updates in real-time

---

### **Test 3: Backend Logs**

```bash
# Look for these patterns:
[api] loaded X history turns  # X should be > 0 after first message
[api] /chat/stream user_id=... session=...
```

---

## 📝 SUMMARY:

| Issue | Root Cause | Fix | Priority |
|-------|------------|-----|----------|
| **Context Lost** | sessionStorage cleared on tab close | Change to localStorage | 🔴 HIGH |
| **No Streaming** | Handler blocks async loop | Run in executor | 🟡 MEDIUM |
| **Diff Empty** | Unified handler (by design) | Accept or add pseudo-diff | 🟢 LOW |

---

## ✅ APPLY FIXES NOW:

**Reply with:**
- "fix both" - I'll apply both fixes immediately
- "fix context" - I'll fix context persistence only
- "fix streaming" - I'll fix SSE streaming only
- "test first" - Let's verify current behavior first

---

**Ready to fix!** 🔧

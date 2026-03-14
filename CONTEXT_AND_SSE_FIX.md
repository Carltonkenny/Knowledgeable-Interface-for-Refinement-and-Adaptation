# 🔍 CONTEXT & SSE ISSUES - ANALYSIS & FIXES

**Date:** March 13, 2026
**Issues Identified:** 2

---

## 🐛 **ISSUE 1: CONTEXT NOT BEING USED**

### **Problem:**
Kira isn't remembering previous conversation context when responding.

### **Root Cause:**

**Current Flow:**
```python
# api.py line 368
history = get_conversation_history(req.session_id, limit=6)
logger.info(f"[api] loaded {len(history)} history turns")

# Passes to kira_unified_handler
result = kira_unified_handler(
    message=req.message,
    history=history,  # ← This is loaded but may be EMPTY
    user_profile=user_profile
)
```

**Why it's not working:**

1. **Session ID might not be persistent** - Frontend may be generating new session_id each time
2. **History not being saved** - Previous messages might not be saved to database
3. **Limit too low** - Only 6 turns loaded, might miss important context

### **Debug Steps:**

**1. Check if session_id is consistent:**

Open browser console and run:
```javascript
// Check what session_id is being sent
localStorage.getItem('promptforge_session_id')
```

**Expected:** Same UUID every time you chat
**If it changes:** Frontend is creating new sessions each time

**2. Check if messages are being saved:**

In browser console → Network tab:
```
1. Send a message
2. Find POST /chat request
3. Check response - does it have session_id?
4. Send another message
5. Check if same session_id is sent
```

**3. Check backend logs:**

Look for:
```
[api] loaded X history turns
```

**If X = 0:** No history is being saved/loaded
**If X > 0:** History exists but Kira isn't using it

---

### **Fix:**

**Option A: Frontend - Ensure session_id persists**

File: `promptforge-web/features/chat/hooks/useKiraStream.ts` or wherever sessionId is managed

```typescript
// Ensure session_id persists across page reloads
const getSessionId = () => {
  let sessionId = localStorage.getItem('promptforge_session_id');
  
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('promptforge_session_id', sessionId);
  }
  
  return sessionId;
};

// Use this in your chat component
const sessionId = getSessionId();
```

**Option B: Backend - Increase history limit**

File: `api.py` line 368

```python
# Change from limit=6 to limit=20
history = get_conversation_history(req.session_id, limit=20)
```

**Option C: Backend - Log what's in history**

File: `api.py` after line 368

```python
history = get_conversation_history(req.session_id, limit=6)
logger.info(f"[api] loaded {len(history)} history turns")

# ADD THIS FOR DEBUGGING:
if history:
    logger.info(f"[api] last message: {history[-1].get('message', '')[:100]}")
else:
    logger.warning("[api] NO HISTORY FOUND - session_id might not be persisting")
```

---

## 🐛 **ISSUE 2: SSE NOT WORKING (KOYEB OFFLINE)**

### **Problem:**
Backend is running locally, Koyeb is offline, SSE streaming is slow/not working.

### **What to Expect When Koyeb is ONLINE:**

**SSE Flow:**
```
1. Frontend sends POST /chat
2. Backend starts streaming via SSE:
   event: kira_message
   data: {"content": "Got", "type": "streaming"}
   
   event: kira_message
   data: {"content": "Got it", "type": "streaming"}
   
   event: result
   data: {"type": "followup_refined", "improved_prompt": "..."}
   
3. Frontend displays tokens as they arrive (typewriter effect)
```

**Latency:**
- **First token:** ~300-500ms (Kira's first LLM call)
- **Streaming:** 20-50 tokens/second
- **Complete:** ~2-4s for followup, ~5-10s for new prompts (swarm)

### **What's Happening Locally (Koyeb OFFLINE):**

**Without Koyeb's optimized infrastructure:**
- SSE still works (it's native to FastAPI)
- But slower because:
  - No connection pooling
  - No load balancing
  - Single instance handling everything
  
**Expected Local Performance:**
- First token: ~500-800ms (slower than Koyeb)
- Streaming: 10-20 tokens/second (vs 20-50 on Koyeb)
- Complete: ~3-6s for followup, ~8-15s for new prompts

---

### **Fix:**

**Option 1: Turn on Koyeb (Recommended)**

```bash
# Login to Koyeb
koyeb login

# Check app status
koyeb apps list

# Start app
koyeb apps start <your-app-name>

# Or via dashboard:
# https://app.koyeb.com/apps/<your-app-name>/start
```

**Option 2: Optimize Local SSE**

File: `api.py` - Ensure SSE is properly configured

```python
# Make sure /chat/stream endpoint exists and is working
@app.post("/chat/stream")
async def chat_stream(...):
    # This should stream tokens via SSE
    pass
```

**Option 3: Use Regular POST (No SSE)**

If SSE is too slow locally, fall back to regular POST:

Frontend already handles this via `useKiraStream.ts` - it waits for full response if SSE fails.

---

## 🎯 **IMMEDIATE ACTION PLAN:**

### **Step 1: Debug Session ID (5 min)**

```bash
# In browser console
console.log('Session ID:', localStorage.getItem('promptforge_session_id'))

# Send a message
# Then check again
console.log('Session ID after message:', localStorage.getItem('promptforge_session_id'))
```

**If session_id changes:** That's why context is lost
**If session_id stays same:** Check backend logs

### **Step 2: Check Backend Logs (5 min)**

Look for:
```
[api] loaded X history turns
```

**If X = 0:** History not being saved
**If X > 0:** Tell me what X is

### **Step 3: Test Context (5 min)**

**Test conversation:**
```
You: "Hi, I'm working on a FastAPI project"
Kira: "Hey! FastAPI is great for async APIs. What are you building?"

You: "Can you help me write an endpoint?"
Expected: Kira remembers you're using FastAPI
Actual: ?
```

**Tell me:**
- Does Kira remember FastAPI?
- Or does it respond like it's a new conversation?

---

## 📝 **EXPECTED BEHAVIOR (When Working):**

### **With Context:**
```
User: "Write a FastAPI endpoint"
Kira: "Got it — FastAPI endpoint with async support..."

User: "Make it async"
Kira: "Got it — I'll make it async with proper await/async patterns. 
       FastAPI handles this beautifully."
       ↑ Remembers FastAPI from previous message
```

### **Without Context (Current Issue):**
```
User: "Write a FastAPI endpoint"
Kira: "Got it — FastAPI endpoint with async support..."

User: "Make it async"
Kira: "Got it — making it async..."
       ↑ No mention of FastAPI (forgot context)
```

---

## 🔧 **QUICK FIXES:**

### **Fix 1: Ensure Session Persistence**

Add to your main chat component or hook:

```typescript
// In ChatPanel.tsx or useChatSession.ts
useEffect(() => {
  // Ensure session_id persists
  const sessionId = localStorage.getItem('promptforge_session_id');
  if (!sessionId) {
    const newId = crypto.randomUUID();
    localStorage.setItem('promptforge_session_id', newId);
  }
}, []);
```

### **Fix 2: Increase History Limit**

File: `api.py` line 368

```python
# Change this:
history = get_conversation_history(req.session_id, limit=6)

# To this:
history = get_conversation_history(req.session_id, limit=20)
```

### **Fix 3: Debug Logging**

File: `api.py` after line 368

```python
history = get_conversation_history(req.session_id, limit=20)
logger.info(f"[api] loaded {len(history)} history turns")

# Add debug logging
if len(history) > 0:
    last_msg = history[-1].get('message', 'N/A')[:50]
    logger.info(f"[api] last message in history: {last_msg}...")
else:
    logger.warning(f"[api] NO HISTORY for session {req.session_id[:8]}...")
```

---

## 🎯 **REPLY WITH:**

1. **Session ID test result:**
   - Does it stay the same or change?

2. **Backend log:**
   - What does `[api] loaded X history turns` show?

3. **Context test:**
   - Does Kira remember FastAPI (or previous topic)?

4. **Koyeb status:**
   - Can you turn it on? Or should we optimize local?

---

**Once I have this info, I'll give you the exact fix!** 🔍

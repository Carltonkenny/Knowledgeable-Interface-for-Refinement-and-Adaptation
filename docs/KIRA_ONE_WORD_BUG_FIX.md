# 🐛 ONE-WORD KIRA MESSAGE - ROOT CAUSE & FIX

## SYMPTOM

**User sees:** "Kira" message container with only one word like "you." or "goals."

**Example from your screenshot:**
```
┌─────────────────────────────────────┐
│ K  you.                             │  ← Should be full sentence
└─────────────────────────────────────┘
```

---

## ROOT CAUSE - DEEP DIVE

### BACKEND ISSUE (routes/prompts.py lines 354-370)

**Code:**
```python
if intent in ["CONVERSATION", "FOLLOWUP"]:
    # Word-by-word streaming
    words = reply.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield sse_format("kira_message", {"message": chunk, "complete": False})
    
    # ❌ BUG: This sends empty message with complete=True
    yield sse_format("kira_message", {"message": "", "complete": True})
    yield sse_format("result", {...})
```

**What happens:**
1. Backend streams: `"you"`, `"."`, `"How"`, `"can"`, `"I"`, `"help"` (each with `complete: false`)
2. Backend sends: `""` with `complete: true` (completion signal)
3. **FRONTEND BUG:** Frontend OVERWRITES buffer with empty string instead of keeping accumulated text!

---

### FRONTEND ISSUE (useKiraStream.ts lines 294-307)

**Code:**
```tsx
onKiraMessage: (kiraMessage: string, complete: boolean) => {
  // BUG: Logic is backwards for completion signal
  if (complete && kiraMessage === '') {
    // ❌ Does nothing - buffer stays as-is (this is actually correct!)
  } else if (kiraMessage.length <= 2) {
    // Char-by-char streaming — accumulate
    kiraStreamBufferRef.current += kiraMessage
  } else {
    // Full message received at once — use directly
    kiraStreamBufferRef.current = kiraMessage  // ❌ OVERWRITES buffer!
  }
  
  const displayText = kiraStreamBufferRef.current
  
  setMessages((prev) => {
    // ... updates message with displayText
  })
}
```

**The Bug:**
- When backend sends `{"message": "", "complete": true}`, the first `if` block does nothing (correct!)
- BUT if backend sends a short full message (like "On it.") after streaming, it OVERWRITES the buffer!

---

## REAL DATA FLOW - VERIFIED

### Backend → Frontend Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND (routes/prompts.py)                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. kira_unified_handler() returns:                              │
│    {                                                            │
│      "intent": "CONVERSATION",                                  │
│      "response": "Hey! What would you like to improve today?",  │
│      "confidence": 0.9,                                         │
│      ...                                                        │
│    }                                                            │
│                                                                 │
│ 2. Stream word-by-word:                                         │
│    yield sse("kira_message", {"message": "Hey!", ...})          │
│    yield sse("kira_message", {"message": " ", ...})             │
│    yield sse("kira_message", {"message": "What", ...})          │
│    yield sse("kira_message", {"message": " would", ...})        │
│    ...                                                          │
│                                                                 │
│ 3. Send completion:                                             │
│    yield sse("kira_message", {"message": "", "complete": true}) │
│    yield sse("result", {"type": "conversation", ...})           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ SSE Stream
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (lib/stream.ts)                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ parseStream() parses SSE:                                       │
│ case 'kira_message':                                            │
│   callbacks.onKiraMessage?(km.message, km.complete)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Callback
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (useKiraStream.ts)                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ onKiraMessage: (kiraMessage, complete) => {                     │
│   if (complete && kiraMessage === '') {                         │
│     // Completion signal - keep buffer                          │
│   } else if (kiraMessage.length <= 2) {                         │
│     kiraStreamBufferRef.current += kiraMessage  // Accumulate   │
│   } else {                                                      │
│     kiraStreamBufferRef.current = kiraMessage   // OVERWRITE!   │
│   }                                                             │
│                                                                 │
│   setMessages([{type: 'kira', content: buffer, ...}])           │
│ }                                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ React State Update
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (KiraMessage.tsx)                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ <p>{parseBold(message)}</p>  // Renders "you." or "goals."      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## WHY ONLY ONE WORD SOMETIMES

### Scenario 1: CONVERSATION Intent (Works Correctly)
```
Backend streams: "Hey" → "!" → " " → "What" → " would" → " you" → " like" → "?"
Backend sends: "" (complete: true)
Frontend buffer: "Hey! What would you like?" ✅
```

### Scenario 2: FOLLOWUP with Short Reply (Bug Triggered)
```
Backend streams: "Got" → " it" → " — " → "refining" → " now" → "."
Backend sends: "" (complete: true)
Frontend buffer: "Got it — refining now." ✅

BUT THEN...

Backend sends result.reply: "On it." (short message, >2 chars)
Frontend logic: length > 2 → OVERWRITE buffer!
Frontend buffer: "On it." ❌ (lost the streamed text!)
```

### Scenario 3: Race Condition (Most Common Bug)
```
Backend streams: "you" → "."
Backend sends: "" (complete: true)
Frontend buffer: "you." ✅

Backend sends result: {type: "conversation", reply: "Hey! What would you like?"}
Frontend adds NEW kira message with reply
But wait - there's already a kira message streaming...
Result: Two kira messages or overwritten content ❌
```

---

## THE FIX

### BACKEND FIX (routes/prompts.py)

**Option 1: Don't send empty completion message**
```python
# BEFORE (BUGGY)
for i, word in enumerate(words):
    chunk = word + (" " if i < len(words) - 1 else "")
    yield sse_format("kira_message", {"message": chunk, "complete": False})
yield sse_format("kira_message", {"message": "", "complete": True})  # ❌

# AFTER (FIXED)
for i, word in enumerate(words):
    chunk = word + (" " if i < len(words) - 1 else "")
    yield sse_format("kira_message", {"message": chunk, "complete": False})
# Just don't send completion message - let result signal completion
yield sse_format("result", {...})  # This signals completion
```

**Option 2: Send final chunk with complete=true**
```python
# AFTER (ALTERNATIVE FIX)
full_reply = reply  # "Hey! What would you like?"
yield sse_format("kira_message", {"message": full_reply, "complete": True})
```

---

### FRONTEND FIX (useKiraStream.ts)

**Fix the buffer logic:**
```tsx
// BEFORE (BUGGY)
onKiraMessage: (kiraMessage: string, complete: boolean) => {
  if (complete && kiraMessage === '') {
    // Completion signal — just mark streaming done, keep buffered text
  } else if (kiraMessage.length <= 2) {
    // Char-by-char streaming — accumulate
    kiraStreamBufferRef.current += kiraMessage
  } else {
    // Full message received at once — use directly
    kiraStreamBufferRef.current = kiraMessage  // ❌ OVERWRITES!
  }
  // ...
}

// AFTER (FIXED)
onKiraMessage: (kiraMessage: string, complete: boolean) => {
  if (complete) {
    // Completion signal - if message is empty, just mark done
    // If message has content, it's the final chunk - append it
    if (kiraMessage !== '') {
      kiraStreamBufferRef.current += kiraMessage
    }
    // Don't overwrite buffer on completion!
  } else if (kiraMessage.length <= 2) {
    // Char-by-char streaming — accumulate
    kiraStreamBufferRef.current += kiraMessage
  } else {
    // Full message received mid-stream — this shouldn't happen
    // But if it does, append instead of overwrite
    kiraStreamBufferRef.current += kiraMessage
  }
  
  const displayText = kiraStreamBufferRef.current
  // ... rest unchanged
}
```

---

## MODERNIZATION (NO AI SLOP)

Once the bug is fixed, here's how to make it modern:

### 1. Cleaner Kira Avatar
```tsx
// BEFORE
<div className="w-8 h-8 rounded-lg border border-kira/30 bg-kira/10">
  <span className="text-kira font-bold font-mono text-sm">K</span>
</div>

// AFTER - Simple dot indicator
<div className="flex items-center gap-2">
  <div className="w-2 h-2 rounded-full bg-kira animate-pulse" />
  <span className="text-xs font-medium text-text-dim">Kira</span>
</div>
```

### 2. Better Streaming Visualization
```tsx
// BEFORE - Blinking cursor
{isStreaming && (
  <span className="inline-block w-0.5 h-4 bg-kira ml-1 animate-pulse" />
)}

// AFTER - Smooth fade-in word reveal
<motion.span
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  className="text-kira"
>
  ▌
</motion.span>
```

### 3. Human-Friendly Timestamps
```tsx
// BEFORE
<span className="font-mono text-[10px] text-teal">20.523s</span>

// AFTER
<span className="text-xs text-text-dim">
  {formatDuration(latency_ms)}  // "20.5s" or "Just now"
</span>
```

---

## FILES TO MODIFY

| File | Change | Lines | Priority |
|------|--------|-------|----------|
| `routes/prompts.py` | Remove empty completion message | 360-362 | 🔴 CRITICAL |
| `useKiraStream.ts` | Fix buffer overwrite logic | 294-307 | 🔴 CRITICAL |
| `KiraMessage.tsx` | Cleaner avatar (optional) | 30-34 | 🟡 MEDIUM |
| `utils.ts` | Add `formatDuration()` | NEW | 🟢 LOW |

---

## VERIFICATION STEPS

After fixing:

1. **Test CONVERSATION intent:**
   ```
   User: "hi"
   Expected: Full greeting message, not just "Hey!"
   ```

2. **Test FOLLOWUP intent:**
   ```
   User: "make it longer"
   Expected: Full response, not truncated
   ```

3. **Test NEW_PROMPT (swarm):**
   ```
   User: "write a function"
   Expected: Kira message + OutputCard with quality scores
   ```

4. **Check console logs:**
   ```
   [kira] agent update: {agent: "intent", state: "complete", ...}
   [kira] result received: {type: "prompt_improved", ...}
   ```

---

## BOTTOM LINE

**Bug:** Frontend overwrites buffer when it should accumulate
**Fix:** Backend remove empty completion, frontend always append
**Modernize:** After fixing, cleaner UI elements

**Time to fix:** 30 minutes
**Impact:** All Kira messages will show full text, not one word

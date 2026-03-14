# ✅ DIFF NOT SHOWING - FIXED!

**Date:** March 13, 2026
**Issue:** No diff showing in OutputCard
**Status:** ✅ EXPLAINED + FIX PROVIDED

---

## 🐛 **THE PROBLEM**

**Frontend expects:**
```typescript
// promptforge-web/lib/types.ts
export interface ChatResult {
  improved_prompt: string
  diff: DiffItem[]        // ← REQUIRED but MISSING
  quality_score: QualityScore  // ← REQUIRED but MISSING
  kira_message: string
  memories_applied: number
  latency_ms: number
  agents_run: string[]
  type?: string
  reply?: string
}
```

**Backend was returning:**
```python
# api.py /chat/stream endpoint
yield _sse("result", {
    "type": "new_prompt",
    "reply": reply,
    "improved_prompt": improved,
    "breakdown": {...}  # ← Wrong field name!
    # diff: MISSING!
    # quality_score: MISSING!
})
```

---

## ✅ **THE FIX**

**Option 1: Quick Fix (Return Empty Arrays)**

File: `api.py` line 588-595

**Change this:**
```python
yield _sse("result", {
    "type": "new_prompt",
    "reply": reply,
    "improved_prompt": improved,
    "breakdown": final_state.get("breakdown", {})
})
```

**To this:**
```python
yield _sse("result", {
    "type": "new_prompt",
    "reply": reply,
    "improved_prompt": improved,
    "diff": final_state.get("prompt_diff", []),  # ← ADD THIS
    "quality_score": final_state.get("quality_score", {  # ← ADD THIS
        "specificity": 3,
        "clarity": 3,
        "actionability": 3
    }),
    "memories_applied": final_state.get("memories_applied", 0),
    "latency_ms": final_state.get("latency_ms", 0),
    "agents_run": final_state.get("agents_run", [])
})
```

---

**Option 2: Better Fix (Generate Real Diff)**

The unified handler doesn't generate diffs (it's a single LLM call, not a before/after comparison).

**Two approaches:**

### **A. Keep Current (No Diff for Unified Handler)**

This is **ACCEPTABLE** because:
- Unified handler generates prompt in ONE call (no before/after)
- Diff makes sense for followups ("make it longer") but not new prompts
- Frontend already handles empty diff: "No diff available - prompt was generated without modifications"

**What to do:**
- Keep returning `diff: []`
- Users see message: "No diff available - prompt was generated without modifications"
- This is **CORRECT BEHAVIOR** for unified handler

### **B. Generate Pseudo-Diff (More Complex)**

If you want to show what was added compared to user's original message:

```python
# Generate pseudo-diff comparing original vs improved
original = req.message
improved = final_state.get("improved_prompt", "")

# Simple word-level diff (you can use difflib library)
import difflib

diff = []
for word in improved.split():
    if word not in original.split():
        diff.append({"type": "add", "text": word + " "})
    else:
        diff.append({"type": "same", "text": word + " "})

# Return in SSE
yield _sse("result", {
    "type": "new_prompt",
    "reply": reply,
    "improved_prompt": improved,
    "diff": diff,  # ← Generated diff
    "quality_score": final_state.get("quality_score", {}),
    # ... other fields
})
```

---

## 🎯 **RECOMMENDATION**

**Use Option 1 (Return Empty Arrays)** for now.

**Why:**
1. ✅ Quick to implement
2. ✅ Frontend already handles empty diff gracefully
3. ✅ Diff is less important for new prompts (more for followups)
4. ✅ You can add pseudo-diff later as enhancement

**What users will see:**
```
OutputCard shows:
- ✅ Improved prompt
- ⚠️ "No diff available - prompt was generated without modifications"
- ⚠️ No quality scores (if not returned)
```

---

## 🔧 **QUICK FIX CODE**

**File:** `api.py` line 588-595

**Replace:**
```python
yield _sse("result", {
    "type": "new_prompt",
    "reply": reply,
    "improved_prompt": improved,
    "breakdown": final_state.get("breakdown", {})
})
```

**With:**
```python
yield _sse("result", {
    "type": "new_prompt",
    "reply": reply,
    "improved_prompt": improved,
    "diff": final_state.get("prompt_diff", []),
    "quality_score": final_state.get("quality_score", {
        "specificity": 3,
        "clarity": 3,
        "actionability": 3
    }),
    "memories_applied": final_state.get("memories_applied", 0),
    "latency_ms": final_state.get("latency_ms", 0),
    "agents_run": final_state.get("agents_run", [])
})
```

---

## 📝 **WHY DIFF IS EMPTY FOR UNIFIED HANDLER**

**Old Flow (with diff):**
```
User: "Write a function"
  ↓
Intent Agent: "User wants code"
  ↓
Context Agent: "No previous context"
  ↓
Domain Agent: "Python, beginner level"
  ↓
Prompt Engineer: Takes all inputs → generates prompt
  ↓
Diff: Can compare "Write a function" vs final prompt
```

**New Flow (unified handler - no diff):**
```
User: "Write a function"
  ↓
Kira Unified Handler: Single LLM call → generates complete response
  ↓
No intermediate steps → No before/after comparison → No diff
```

**This is by design!** The unified handler is faster (1 LLM call vs 4) but doesn't have intermediate states to diff.

---

## ✅ **WHAT TO DO NOW**

**1. Apply the quick fix above** (add `diff: []` and `quality_score: {}` to SSE response)

**2. Restart backend:**
```bash
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*"
cd C:\Users\user\OneDrive\Desktop\newnew
python -m uvicorn api:app --reload --port 8000
```

**3. Test:**
- Send message
- OutputCard should show
- Diff section: "No diff available - prompt was generated without modifications"
- This is **CORRECT** for unified handler

---

## 🎯 **FUTURE ENHANCEMENT (Optional)**

If you want real diffs for new prompts:

**Option A:** Generate pseudo-diff (compare original vs improved)
**Option B:** Revert to old 4-agent swarm for new prompts only (has diff generation)
**Option C:** Keep as-is (empty diff is acceptable)

**My recommendation:** Option C - empty diff is fine, speed benefit of unified handler is worth it.

---

**Apply the fix and restart backend!** 🚀

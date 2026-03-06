# Step 7: Clarification Loop Implementation

**Time:** 30 minutes  
**Status:** Not Started

---

## 🎯 Objective

Implement the clarification loop mechanism:

- Detect when Kira needs clarification (ambiguity > 0.7)
- Save `pending_clarification` flag to database
- Return Kira's question via SSE
- On user's answer: inject into state, fire swarm directly, clear flag
- **Do NOT re-run orchestrator** — avoids re-classifying the answer

---

## 📋 What We're Doing and Why

### The Clarification Loop Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: User sends ambiguous prompt                            │
│ "write something about AI"                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Kira detects ambiguity (score > 0.7)                   │
│ Sets clarification_needed: true                                 │
│ Returns: "What specific aspect of AI interests you most?"       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Save pending_clarification = true to DB                │
│ Save clarification_key = "topic_focus"                          │
│ End request — user sees Kira's question                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: User responds with clarification                        │
│ "I want to write about AI ethics in healthcare"                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Check DB FIRST — see pending_clarification = true      │
│ Inject answer into state                                        │
│ Skip orchestrator (don't re-classify!)                          │
│ Fire swarm directly                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Clear pending_clarification flag                        │
│ Return improved prompt                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Matters

| Without Clarification Loop | With Clarification Loop |
|---------------------------|-------------------------|
| Swarm runs on ambiguous input → wasted LLM calls | Clarifies BEFORE swarm → focused output |
| Generic, vague improved prompts | Specific, targeted prompts |
| User frustrated with irrelevant results | User gets exactly what they need |
| 4 LLM calls wasted on bad input | 1 LLM call saves the session |

---

## 🔧 Implementation

### Part A: Update `api.py` for Clarification Check

**In `/chat` endpoint, add clarification check FIRST:**

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: User = Depends(get_current_user)):
    """
    Conversational endpoint with memory.
    Checks clarification loop FIRST before any other logic.
    """
    logger.info(f"[api] /chat user_id={user.user_id} session={req.session_id}")

    # ═══ STEP 1: CHECK CLARIFICATION FLAG FIRST ═══
    pending_clarification, clarification_key = get_clarification_flag(
        session_id=req.session_id,
        user_id=user.user_id
    )
    
    if pending_clarification:
        logger.info(f"[api] clarification pending — injecting answer, firing swarm")
        
        # User's message IS the clarification answer
        # Inject into state and fire swarm directly (SKIP orchestrator)
        final_state = _run_swarm_with_clarification(
            message=req.message,
            clarification_key=clarification_key,
            user_id=user.user_id,
            session_id=req.session_id
        )
        
        # Clear the clarification flag
        save_clarification_flag(
            session_id=req.session_id,
            user_id=user.user_id,
            pending=False,
            clarification_key=None
        )
        
        # Return result
        improved = final_state.get("improved_prompt", "")
        return ChatResponse(
            type="clarification_resolved",
            reply="Perfect — here's your engineered prompt ✨",
            improved_prompt=improved,
            breakdown=final_state.get("breakdown"),
            session_id=req.session_id
        )
    
    # ═══ STEP 2: NORMAL FLOW (no pending clarification) ═══
    # ... existing chat logic ...
```

### Part B: Create `_run_swarm_with_clarification()` Helper

**Add to `api.py`:**

```python
def _run_swarm_with_clarification(
    message: str,
    clarification_key: str,
    user_id: str,
    session_id: str
) -> dict:
    """
    Run swarm with clarification already provided.
    Skips orchestrator — fires swarm directly.
    
    Args:
        message: User's clarification answer
        clarification_key: What field was being clarified
        user_id: From JWT
        session_id: Conversation session
        
    Returns:
        Final state from swarm
    """
    # Check cache first
    cached = get_cached_result(message)
    if cached:
        return cached
    
    # Initialize state with clarification already resolved
    initial_state = PromptForgeState(
        message=message,
        session_id=session_id,
        user_id=user_id,
        attachments=[],
        input_modality="text",
        conversation_history=[],
        user_profile={},
        langmem_context=[],
        mcp_trust_level=0,
        orchestrator_decision={
            "user_facing_message": "Got it — let me work with that.",
            "proceed_with_swarm": True,
            "agents_to_run": ["intent", "domain"],  # Skip context (no history yet)
            "clarification_needed": False,
            "clarification_question": None,
            "skip_reasons": {"context": "clarification just resolved"},
            "tone_used": "direct",
            "profile_applied": False,
        },
        user_facing_message="Got it — let me work with that.",
        pending_clarification=False,  # Already resolved
        clarification_key=None,
        proceed_with_swarm=True,
        intent_analysis={},
        context_analysis={},
        domain_analysis={},
        agents_skipped=["context"],
        agent_latencies={},
        improved_prompt="",
        original_prompt=message,
        prompt_diff=[],
        quality_score={},
        changes_made=[],
        breakdown={},
    )
    
    # Run workflow
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(workflow.invoke, initial_state)
        try:
            result = future.result(timeout=GRAPH_TIMEOUT)
            # Store in cache
            set_cached_result(message, result)
            return result
        except TimeoutError:
            raise HTTPException(status_code=504, detail="Request timed out")
```

### Part C: Update Kira to Save Clarification Flag

**In `agents/kira.py`, when `clarification_needed: true`:**

```python
# After orchestrator returns with clarification_needed: true
if decision["clarification_needed"]:
    # Save flag to database
    save_clarification_flag(
        session_id=session_id,
        user_id=user_id,
        pending=True,
        clarification_key="general"  # Or extract from decision
    )
    logger.info(f"[kira] saved clarification flag session={session_id}")
```

### Part D: Update `/chat/stream` for Clarification

**In SSE streaming endpoint:**

```python
@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, user: User = Depends(get_current_user)):
    """Streaming version with clarification check."""
    
    async def generate():
        try:
            # STEP 1: Check clarification flag FIRST
            pending_clarification, clarification_key = get_clarification_flag(
                session_id=req.session_id,
                user_id=user.user_id
            )
            
            if pending_clarification:
                yield _sse("status", {"message": "Clarification received — processing..."})
                
                # Run swarm with clarification
                result = await run_swarm_with_clarification_async(
                    message=req.message,
                    clarification_key=clarification_key,
                    user_id=user.user_id,
                    session_id=req.session_id
                )
                
                # Clear flag
                save_clarification_flag(
                    session_id=req.session_id,
                    user_id=user.user_id,
                    pending=False,
                    clarification_key=None
                )
                
                # Stream result
                yield _sse("result", {
                    "type": "clarification_resolved",
                    "reply": "Perfect — here's your engineered prompt ✨",
                    "improved_prompt": result.get("improved_prompt", "")
                })
                yield _sse("done", {"message": "Complete"})
                return
            
            # STEP 2: Normal flow...
            # ... existing streaming logic ...
            
        except Exception as e:
            logger.exception("[api] /chat/stream error")
            yield _sse("error", {"message": str(e)})
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## ✅ Verification Checklist

### Test 1: Clarification Flag Saves

```bash
python -c "
from database import save_clarification_flag, get_clarification_flag

# Save flag
success = save_clarification_flag(
    session_id='test-session-123',
    user_id='00000000-0000-0000-0000-000000000000',
    pending=True,
    clarification_key='topic_focus'
)
print(f'Save result: {success}')

# Read flag back
pending, key = get_clarification_flag(
    session_id='test-session-123',
    user_id='00000000-0000-0000-0000-000000000000'
)
print(f'Pending: {pending}, Key: {key}')
print('✅ Clarification flag works')
"
```

**Expected:** `Save result: True`, `Pending: True, Key: topic_focus`

### Test 2: Kira Returns Clarification Question

```bash
python -c "
from agents.kira import orchestrator_node

# Ambiguous message
state = {
    'message': 'write something',
    'user_profile': {},
    'conversation_history': [],
    'pending_clarification': False,
}

result = orchestrator_node(state)
decision = result['orchestrator_decision']

print(f'Clarification needed: {decision[\"clarification_needed\"]}')
print(f'Question: {decision[\"clarification_question\"]}')

if decision['clarification_needed']:
    print('✅ Clarification detected')
else:
    print('⚠️ May need to adjust ambiguity threshold')
"
```

### Test 3: Full Clarification Loop (Manual Test)

**Step 1: Send ambiguous prompt**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"message\":\"write something\",\"session_id\":\"clarification-test\"}"
```

**Expected:** Kira asks a clarifying question

**Step 2: Check database**
```sql
-- In Supabase SQL Editor
SELECT pending_clarification, clarification_key 
FROM conversations 
WHERE session_id = 'clarification-test' 
ORDER BY created_at DESC 
LIMIT 1;
```

**Expected:** `pending_clarification = true`

**Step 3: Send clarification answer**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"message\":\"I want to write about AI ethics\",\"session_id\":\"clarification-test\"}"
```

**Expected:** Swarm runs, returns improved prompt

**Step 4: Verify flag cleared**
```sql
SELECT pending_clarification 
FROM conversations 
WHERE session_id = 'clarification-test' 
ORDER BY created_at DESC 
LIMIT 1;
```

**Expected:** `pending_clarification = false`

---

## 🆘 Troubleshooting

### Problem: "Clarification flag not saving"

**Cause:** Database function error or RLS blocking

**Solution:**
Check logs:
```python
logger.error(f"[db] save_clarification_flag failed: {e}")
```

Verify RLS allows INSERT for your user.

### Problem: "Orchestrator re-runs on clarification answer"

**Cause:** Clarification check not happening FIRST

**Solution:**
Move `get_clarification_flag()` call to top of `/chat`, before any other logic.

### Problem: "Flag never clears"

**Cause:** `save_clarification_flag(pending=False)` not called

**Solution:**
Ensure flag is cleared AFTER swarm runs successfully.

---

## 📝 What Changed

| File | Change |
|------|--------|
| `api.py` | Clarification check in `/chat` and `/chat/stream` |
| `api.py` | New `_run_swarm_with_clarification()` helper |
| `database.py` | Already has `save_clarification_flag()` and `get_clarification_flag()` |
| `agents/kira.py` | Saves flag when `clarification_needed: true` |

---

## ✅ Checkpoint — DO NOT PROCEED UNTIL

- [ ] Clarification flag saves to database
- [ ] Kira detects ambiguity and returns question
- [ ] Full loop works: ambiguous → question → answer → swarm
- [ ] Flag clears after swarm runs
- [ ] Orchestrator skipped on clarification answer

---

**Next:** Proceed to [STEP_8_verification.md](./STEP_8_verification.md)

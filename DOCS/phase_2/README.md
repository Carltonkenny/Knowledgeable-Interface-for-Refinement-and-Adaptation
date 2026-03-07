# Phase 2 Quick Start & README

**Document Purpose:** Quick reference for Phase 2  
**For:** Developers starting Phase 2 implementation

---

## WHAT IS PHASE 2?

Phase 2 builds the intelligent agent swarm that makes PromptForge work. You're creating:

1. **Kira** — Personality-driven orchestrator (1 LLM call)
2. **4 Agents** — Intent, Context, Domain, Prompt Engineer (parallel execution)
3. **LangGraph Workflow** — Conditional routing and parallel execution
4. **Memory Pipeline** — LangMem for context injection
5. **Multimodal Input** — Voice, images, files
6. **Advanced Endpoints** — SSE streaming, transcription

---

## IMPLEMENTATION ORDER

```
STEP 1: Kira Orchestrator        (3-4 hours)
        ↓
STEP 2: Intent Agent       (2-3 hours)
        ↓
STEP 3-4: Context + Domain       (3-4 hours)
        ↓
STEP 5: Prompt Engineer          (2-3 hours)
        ↓
STEP 6: LangGraph Workflow       (3-4 hours)
        ↓
STEP 7: LangMem Integration      (2-3 hours)
        ↓
STEP 8: Multimodal Processing    (3-4 hours)
        ↓
STEP 9: Advanced Endpoints       (2-3 hours)
        ↓
TESTING (2-3 days)
        ↓
DONE (10-14 days total)
```

---

## KEY FILES TO READ FIRST

1. **PHASE_2_OVERVIEW.md** — High-level architecture + components
2. **AGENT_SPECIFICATIONS.md** — Detailed specs for each of 4 agents
3. **LANGGRAPH_WORKFLOW_GUIDE.md** — How to structure the StateGraph
4. **STEP_1_kira_enhancement.md** — First implementation task

---

## QUICK ARCHITECTURE

```
User Input
  ↓
[Kira Orchestrator] ← 1 LLM call, decides routing
  ↓
[Parallel Agents]
  ├─ Intent (if needed)
  ├─ Context (if needed)
  └─ Domain (if needed)
  ↓
[Prompt Engineer] ← Always runs, full model, synthesizes
  ↓
Output + Cache + LangMem write (background)
```

---

## IMPORTANT CONSTANTS

### Kira (from RULES.md)
- Model: `gpt-4o-mini` (fast)
- Max tokens: 150
- Temperature: 0.1
- Response time: 300-500ms

### Agents (from RULES.md)

| Agent | Model | Tokens | Temp |
|-------|-------|--------|------|
| Intent | gpt-4o-mini | 400 | 0.1 |
| Context | gpt-4o-mini | 400 | 0.1 |
| Domain | gpt-4o-mini | 400 | 0.1 |
| Engineer | gpt-4o | 2048 | 0.3 |

### Performance Targets
- Cache hit: <100ms
- Full swarm: 3-5s
- Kira: <500ms

---

## DIRECTORY STRUCTURE TO CREATE

```
agents/
  ├─ __init__.py
  ├─ autonomous.py       ← Kira (enhance existing)
  ├─ intent.py           ← New
  ├─ context.py          ← New
  ├─ domain.py           ← New
  └─ prompt_engineer.py  ← New

memory/
  └─ langmem.py          ← New

multimodal/
  ├─ __init__.py
  ├─ voice.py
  ├─ image.py
  ├─ files.py
  └─ validators.py

graph/
  └─ workflow.py         ← Extend existing
```

---

## STATE MANAGEMENT

Use `PromptForgeState` TypedDict for all state passing. All agents modify and return state:

```python
state = PromptForgeState(
    user_id="...",
    session_id="...",
    original_prompt="...",
    breakdown={},  # Agent results go here
    agents_used=[],
    agents_skipped=[]
)

# Agent processes it
state = await agent_node(state)

# State modified in-place with agent results
state["breakdown"]["agent_name"] = {...}
state["agents_used"].append("agent_name")
```

---

## KEY PATTERNS

### Pattern 1: LLM Call in Agent
```python
async def agent_node(state: PromptForgeState) -> PromptForgeState:
    try:
        llm = get_fast_llm()  # or get_llm() for engineer
        prompt = format_prompt(...)
        response = llm.invoke(prompt)
        parsed = parse_json(response)
        
        state["breakdown"]["agent"] = parsed
        state["agents_used"].append("agent")
    except Exception as e:
        # Log and store error
        state["breakdown"]["agent"] = {"error": str(e), "confidence": 0}
        state["agents_skipped"].append({"agent": "agent", "reason": str(e)})
    
    return state
```

### Pattern 2: Routing in LangGraph
```python
def route_to_agents(state) -> list:
    """Return list of agents to execute."""
    agents = state["orchestrator_decision"]["agents_to_run"]
    return agents

workflow.add_conditional_edges("orchestrator", route_to_agents)
```

### Pattern 3: Background Task
```python
@app.post("/chat")
async def chat(..., background_tasks: BackgroundTasks):
    # Do work
    result = await process()
    
    # Queue background work
    background_tasks.add_task(write_langgem, user_id, data)
    
    return result  # User gets response immediately
```

---

## TESTING EACH COMPONENT

After each step, test locally:

```bash
# Test Kira
python -c "
import asyncio
from agents.autonomous import orchestrator_node
asyncio.run(orchestrator_node(state))
"

# Test Intent
python -c "
import asyncio
from agents.intent import intent_node
asyncio.run(intent_node(state))
"

# Etc. for each agent
```

---

## DEBUGGING TIPS

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test with Sample Prompts
```python
test_prompts = [
    "Build a REST API",          # Should include Intent
    "Shorter version",           # Should be FOLLOWUP
    "What do you mean?",         # Should ask clarification
    "Hi",                        # Should be CONVERSATION
]
```

### Check JSON Response Format
```python
import json
response = agent_node(state)
print(json.dumps(response["breakdown"], indent=2))
```

---

## COMMON ERRORS & FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `orchestrator_decision` missing | Not set in Kira | Check STEP_1 implementation |
| Agents don't run in parallel | Using edges instead of Send() | Review LANGGRAPH_WORKFLOW_GUIDE.md |
| LangMem context empty | Query not called | Add to orchestrator_node |
| Multimodal file rejected | Size/format validation | Check MULTIMODAL_IMPLEMENTATION.md |
| Performance slow | Missing cache check | Add cache before workflow |

---

## DEPENDENCIES TO INSTALL

```bash
pip install \
  langgraph \
  langchain \
  openai \
  pydantic \
  fastapi \
  supabase \
  redis \
  PyMuPDF \
  python-docx \
  python-multipart
```

---

## VERIFICATION CHECKLIST

After each step, verify:

- [ ] Component implements all required functions
- [ ] Returns correct JSON structure
- [ ] Has comprehensive error handling
- [ ] Includes logging statements
- [ ] Handles edge cases gracefully
- [ ] Tests pass locally
- [ ] Performance meets targets
- [ ] Code follows RULES.md standards

---

## GIT WORKFLOW

```bash
# After each major component
git add agents/new_agent.py
git commit -m "Phase 2 STEP_X: [ComponentName] implementation"

# At the end of Phase 2
git push
```

---

## REFERENCE DOCUMENTS

Keep these handy:

1. `RULES.md` — Source of truth for all specifications
2. `IMPLEMENTATION_PLAN.md` — Phased roadmap
3. `AGENT_SPECIFICATIONS.md` — Agent details
4. `LANGGRAPH_WORKFLOW_GUIDE.md` — Workflow patterns
5. `MEMORY_INTEGRATION_GUIDE.md` — LangMem usage
6. `MULTIMODAL_IMPLEMENTATION.md` — Voice, image, files
7. `PHASE_2_PROGRESS.md` — Track your progress
8. `PHASE_2_VERIFICATION_LOG.md` — Test results

---

## NEED HELP?

If stuck on a step:

1. **Re-read the STEP_X file** — Usually has the answer
2. **Check AGENT_SPECIFICATIONS.md** — For agent-specific questions
3. **Review RULES.md** — For architecture questions
4. **Test locally** — Use test patterns above instead of skipping to prod
5. **Update PHASE_2_PROGRESS.md** — Log blockers for reference

---

## SUCCESS LOOKS LIKE

When Phase 2 is done:
- ✅ All 4 agents implemented and tested
- ✅ LangGraph workflow routing correctly
- ✅ LangMem context injection working
- ✅ Multimodal input processing voice, images, files
- ✅ Advanced endpoints with SSE streaming functional
- ✅ Performance targets met
- ✅ Code reviewed against RULES.md
- ✅ Ready for Phase 3

---

**Start with STEP_1_kira_enhancement.md when ready.**

Good luck! 🚀


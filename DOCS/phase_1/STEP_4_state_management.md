# Step 4: State Management — Full PromptForgeState

**Time:** 30 minutes  
**Status:** Not Started

---

## 🎯 Objective

Replace the minimal `AgentState` with the complete `PromptForgeState` TypedDict from RULES.md.

---

## 📋 What We're Doing and Why

### Current State
Your `state.py` has:
```python
class AgentState(TypedDict):
    raw_prompt:      str
    intent_result:   dict[str, Any]
    context_result:  dict[str, Any]
    domain_result:   dict[str, Any]
    improved_prompt: str
```

This is **5 fields** — enough for basic swarm, but missing:
- User input metadata (session_id, user_id, attachments, modality)
- Memory (user_profile, langmem_context, mcp_trust_level)
- Orchestrator decisions (kira routing, clarification flags)
- Agent outputs (which agents ran, which skipped, latencies)
- Output metadata (diff, quality scores, change explanations)

### What We're Building

Complete `PromptForgeState` from RULES.md (25+ fields):

```python
class PromptForgeState(TypedDict):
    # ═══ INPUT ═══
    message: str                     # User's actual message
    session_id: str                  # From JWT, uniquely identifies conversation
    user_id: str                     # From JWT, extracted via auth.uid()
    attachments: list[dict]          # [{type, content/base64, filename}]
    input_modality: str              # text | file | image | voice
    conversation_history: list[dict] # Last N turns from Supabase

    # ═══ MEMORY ═══
    user_profile: dict               # Loaded from Supabase user_profiles table
    langmem_context: list[dict]      # Top 5 memories from LangMem
    mcp_trust_level: int             # 0 (cold) | 1 (warm) | 2 (tuned)

    # ═══ ORCHESTRATOR ═══
    orchestrator_decision: dict      # Full Kira response JSON
    user_facing_message: str         # User sees this via SSE
    pending_clarification: bool      # True if waiting for answer
    clarification_key: str | None    # Which field is being clarified
    proceed_with_swarm: bool         # Kira's go/no-go decision

    # ═══ AGENT OUTPUTS ═══
    intent_analysis: dict            # From intent agent
    context_analysis: dict           # From context agent
    domain_analysis: dict            # From domain agent
    agents_skipped: list[str]        # Which agents didn't run and why
    agent_latencies: dict[str, int]  # {agent_name: ms}

    # ═══ OUTPUT ═══
    improved_prompt: str             # Final engineered prompt
    original_prompt: str             # User's original input
    prompt_diff: list[dict]          # Changes with annotations
    quality_score: dict              # {specificity: 1-5, clarity: 1-5, actionability: 1-5}
    changes_made: list[str]          # Human-readable change explanations
    breakdown: dict                  # Agent-specific insights
```

### Why This Matters

| Benefit | Explanation |
|---------|-------------|
| **Type safety** | TypeScript-like safety in Python — catches errors early |
| **Kira integration** | Fields for orchestrator decisions and clarification loop |
| **Memory support** | Fields for user_profile, langmem_context |
| **Quality tracking** | Fields for scores, diffs, change explanations |
| **Future-proof** | Ready for Phase 2 (LangMem) and Phase 3 (MCP) |

---

## 🔧 Implementation

### Update `state.py`

**AI Prompt to Replace `state.py`:**

```
You are updating state.py for PromptForge v2.0.

Follow RULES.md exactly. Replace the minimal AgentState with the complete
PromptForgeState TypedDict as specified in RULES.md.

Requirements:
1. Use typing_extensions.TypedDict
2. All fields properly typed (str, dict, list, int, bool, Optional)
3. Organize into sections: INPUT, MEMORY, ORCHESTRATOR, AGENT OUTPUTS, OUTPUT
4. Add docstrings explaining each field
5. Use NotRequired for optional fields (Python 3.11+)

Create the full PromptForgeState with all fields from RULES.md:
- Input: message, session_id, user_id, attachments, input_modality, conversation_history
- Memory: user_profile, langmem_context, mcp_trust_level
- Orchestrator: orchestrator_decision, user_facing_message, pending_clarification, clarification_key, proceed_with_swarm
- Agent Outputs: intent_analysis, context_analysis, domain_analysis, agents_skipped, agent_latencies
- Output: improved_prompt, original_prompt, prompt_diff, quality_score, changes_made, breakdown

File: state.py
```

### Expected `state.py` Structure:

```python
# state.py
# ─────────────────────────────────────────────
# PromptForgeState TypedDict — the "baton" passed between agents.
# Complete schema per RULES.md (March 2026).
# ─────────────────────────────────────────────

from typing import Any, Optional, List, Dict
from typing_extensions import TypedDict, NotRequired


class PromptForgeState(TypedDict):
    """
    Complete state schema for PromptForge v2.0 swarm orchestration.
    Passed between all agents in LangGraph workflow.
    """
    
    # ═══ INPUT ═══
    message: str
    """User's actual message (5-2000 characters)."""
    
    session_id: str
    """From JWT, uniquely identifies conversation."""
    
    user_id: str
    """From JWT, extracted via auth.uid(). Used for RLS."""
    
    attachments: List[Dict[str, Any]]
    """[{type, content/base64, filename}] for multimodal inputs."""
    
    input_modality: str
    """text | file | image | voice"""
    
    conversation_history: List[Dict[str, Any]]
    """Last N turns from Supabase conversations table."""
    
    # ═══ MEMORY ═══
    user_profile: Dict[str, Any]
    """Loaded from Supabase user_profiles table."""
    
    langmem_context: List[Dict[str, Any]]
    """Top 5 memories from LangMem semantic search."""
    
    mcp_trust_level: int
    """0 (cold) | 1 (warm) | 2 (tuned) — for MCP surface only."""
    
    # ═══ ORCHESTRATOR ═══
    orchestrator_decision: Dict[str, Any]
    """Full Kira response JSON with routing decision."""
    
    user_facing_message: str
    """User sees this via SSE — from Kira."""
    
    pending_clarification: bool
    """True if waiting for user's answer to clarification question."""
    
    clarification_key: Optional[str]
    """Which field is being clarified (e.g., 'target_audience')."""
    
    proceed_with_swarm: bool
    """Kira's go/no-go decision."""
    
    # ═══ AGENT OUTPUTS ═══
    intent_analysis: Dict[str, Any]
    """From intent agent — goal analysis."""
    
    context_analysis: Dict[str, Any]
    """From context agent — user context analysis."""
    
    domain_analysis: Dict[str, Any]
    """From domain agent — domain identification."""
    
    agents_skipped: List[str]
    """Which agents didn't run and why (e.g., ['context: no history'])."""
    
    agent_latencies: Dict[str, int]
    """{agent_name: latency_ms} for performance monitoring."""
    
    # ═══ OUTPUT ═══
    improved_prompt: str
    """Final engineered prompt from prompt engineer agent."""
    
    original_prompt: str
    """User's original input (unchanged)."""
    
    prompt_diff: List[Dict[str, Any]]
    """Changes with annotations [{type, old, new, explanation}]."""
    
    quality_score: Dict[str, int]
    """{specificity: 1-5, clarity: 1-5, actionability: 1-5}."""
    
    changes_made: List[str]
    """Human-readable change explanations."""
    
    breakdown: Dict[str, Any]
    """Agent-specific insights for API response."""


# Backward compatibility alias
AgentState = PromptForgeState
```

### Update `workflow.py` to Use New State

Your `graph/workflow.py` imports `AgentState` — update it:

```python
# In graph/workflow.py
from state import PromptForgeState  # Changed from AgentState

# Update build_graph() to use PromptForgeState
def build_graph():
    graph = StateGraph(PromptForgeState)  # ← Changed
    # ... rest stays the same
```

### Update `api.py` to Initialize New Fields

In `_run_swarm()`, initialize all required fields:

```python
def _run_swarm(prompt: str, user_id: str, session_id: str) -> dict:
    """Run swarm with full state initialization."""
    
    # Check cache first
    cached = get_cached_result(prompt)
    if cached:
        return cached
    
    # Initialize ALL required fields
    initial_state = PromptForgeState(
        message=prompt,
        session_id=session_id,
        user_id=user_id,
        attachments=[],
        input_modality="text",
        conversation_history=[],
        user_profile={},
        langmem_context=[],
        mcp_trust_level=0,
        orchestrator_decision={},
        user_facing_message="",
        pending_clarification=False,
        clarification_key=None,
        proceed_with_swarm=True,
        intent_analysis={},
        context_analysis={},
        domain_analysis={},
        agents_skipped=[],
        agent_latencies={},
        improved_prompt="",
        original_prompt=prompt,
        prompt_diff=[],
        quality_score={},
        changes_made=[],
        breakdown={},
    )
    
    # Run workflow
    result = workflow.invoke(initial_state)
    
    # Cache result
    set_cached_result(prompt, result)
    return result
```

---

## ✅ Verification Checklist

### Test 1: State Imports Correctly

```bash
cd C:\Users\user\OneDrive\Desktop\newnew
python -c "from state import PromptForgeState; print('✅ PromptForgeState imported')"
```

**Expected:** `✅ PromptForgeState imported`

### Test 2: All Fields Present

```bash
python -c "
from state import PromptForgeState
import inspect

# Get all fields
sig = inspect.signature(PromptForgeState)
fields = list(sig.parameters.keys()) if sig.parameters else []

# If TypedDict, use __annotations__
if hasattr(PromptForgeState, '__annotations__'):
    fields = list(PromptForgeState.__annotations__.keys())

print(f'Fields ({len(fields)}):')
for f in sorted(fields):
    print(f'  - {f}')
"
```

**Expected:** 25+ fields listed

### Test 3: Workflow Compiles

```bash
python -c "from graph.workflow import workflow; print('✅ Workflow compiled successfully')"
```

**Expected:** `✅ Workflow compiled successfully`

### Test 4: API Starts Without Errors

```bash
python main.py
```

**Expected:** Server starts, no import errors

---

## 🆘 Troubleshooting

### Problem: "TypedDict missing required field"

**Cause:** Not all fields initialized in `_run_swarm()`

**Solution:**
Initialize ALL fields, even with empty defaults:
```python
initial_state = PromptForgeState(
    message=prompt,
    # ... initialize ALL 25+ fields
)
```

### Problem: "ImportError: cannot import name 'NotRequired'"

**Cause:** `typing_extensions` not installed or old version

**Solution:**
```bash
pip install --upgrade typing_extensions
```

### Problem: "Workflow invocation fails"

**Cause:** Agent expects old field names

**Solution:**
Update agents to use new field names:
- `raw_prompt` → `message` (or add alias)
- `intent_result` → `intent_analysis`
- etc.

---

## 📝 What Changed

| File | Change |
|------|--------|
| `state.py` | Replaced with full PromptForgeState (25+ fields) |
| `graph/workflow.py` | Import PromptForgeState instead of AgentState |
| `api.py` | Initialize all fields in `_run_swarm()` |

---

## ✅ Checkpoint — DO NOT PROCEED UNTIL

- [ ] `PromptForgeState` imports without errors
- [ ] All 25+ fields present
- [ ] Workflow compiles successfully
- [ ] API server starts without errors
- [ ] Backward compatibility alias `AgentState = PromptForgeState` exists

---

**Next:** Proceed to [STEP_5_db_migrations.md](./STEP_5_db_migrations.md)

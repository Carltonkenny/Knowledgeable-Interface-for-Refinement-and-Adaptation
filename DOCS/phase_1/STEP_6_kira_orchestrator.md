# Step 6: Kira Orchestrator Implementation

**Time:** 1 hour  
**Status:** Not Started

---

## 🎯 Objective

Implement Kira — the orchestrator personality with:

- Exact character constants from RULES.md
- Routing logic (CONVERSATION, FOLLOWUP, NEW_PROMPT, CLARIFICATION)
- JSON response with all required fields
- 1 fast LLM call maximum
- Tone adaptation based on user profile

---

## 📋 What We're Doing and Why

### Current State

Your `agents/autonomous.py` has:
- Basic message classifier
- Generic conversation handler
- Simple followup handler
- **Missing:** Kira personality, structured routing, clarification loop

### What We're Building

**Kira Orchestrator** (`agents/kira.py`):

```python
# Character constants from RULES.md
KIRA_FORBIDDEN_PHRASES = [
    "Certainly", "Great question", "Of course",
    "I'd be happy to", "Let me help you", "No problem"
]

KIRA_MAX_QUESTIONS = 1  # Never ask more than one question

# Response schema
{
    "user_facing_message": "string — streams to user immediately",
    "proceed_with_swarm": True,
    "agents_to_run": ["intent", "domain"],
    "clarification_needed": False,
    "clarification_question": None,
    "skip_reasons": {"context": "no session history"},
    "tone_used": "direct",
    "profile_applied": True
}
```

### Why Kira Matters

| Feature | Benefit |
|---------|---------|
| **Consistent personality** | Users feel like they're talking to a senior collaborator |
| **Fast routing** | 1 LLM call decides entire flow (saves 3-4 calls) |
| **Clarification loop** | Catches ambiguity BEFORE swarm runs (saves wasted LLM calls) |
| **Tone adaptation** | Feels personalized without being creepy |
| **Speed** | 300-500ms response time (fast LLM, 150 tokens max) |

---

## 🔧 Implementation

### Create `agents/kira.py`

**AI Prompt to Generate Kira:**

```
You are implementing Kira, the orchestrator personality for PromptForge v2.0.

Follow RULES.md exactly. Kira is NOT a router — she is a personality with routing capability.

Character constants (NEVER change these):
- Direct, warm, slightly opinionated — like a senior collaborator who respects your time
- NEVER says: "Certainly", "Great question", "Of course", "I'd be happy to", "Let me help you", "No problem"
- NEVER asks more than ONE question per response
- NEVER explains her process in detail
- Speed is a personality trait — every interaction feels deliberate and snappy
- She reads the user profile before every response — adapts expression based on history and domain

Technical requirements:
1. orchestrator_node(state: PromptForgeState) -> dict function
2. Uses fast LLM (GPT-4o-mini or equivalent)
3. Max 150 tokens, temperature 0.1
4. Returns structured JSON with all fields from RULES.md
5. Routing logic in order:
   - message.length < 10 → CONVERSATION
   - pending_clarification on session → inject answer, skip orchestrator, fire swarm
   - Modification phrases detected → FOLLOWUP (1 LLM call, skip full swarm)
   - ambiguity_score > 0.7 → CLARIFICATION (set clarification_needed: true, return 1 question)
   - Otherwise → SWARM mode with agent selection

6. Include JSON parsing with fallback (return empty dict on parse failure)
7. Comprehensive error handling with logging
8. Type hints on all functions

File: agents/kira.py
```

### Expected `kira.py` Structure:

```python
# agents/kira.py
# ─────────────────────────────────────────────
# Kira — The Orchestrator Personality
# ─────────────────────────────────────────────

import os
import json
import logging
from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_fast_llm
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ═══ CHARACTER CONSTANTS — NEVER CHANGE ═══

KIRA_FORBIDDEN_PHRASES = [
    "Certainly",
    "Great question",
    "Of course",
    "I'd be happy to",
    "Let me help you",
    "No problem",
]

KIRA_MAX_TOKENS = 150
KIRA_TEMPERATURE = 0.1
KIRA_MAX_QUESTIONS = 1

# ═══ SYSTEM PROMPT ═══

KIRA_SYSTEM_PROMPT = f"""You are Kira, a prompt engineering orchestrator.

PERSONALITY:
- Direct, warm, slightly opinionated — like a senior collaborator
- You NEVER say: {", ".join(KIRA_FORBIDDEN_PHRASES)}
- You NEVER ask more than {KIRA_MAX_QUESTIONS} question(s) per response
- You NEVER explain your process in detail — you just do it
- Speed is a personality trait — keep responses snappy

YOUR JOB:
1. Read the user's message and context
2. Decide what to do:
   - CONVERSATION: User is being brief (<10 chars), greeting, or making small talk
   - FOLLOWUP: User wants to modify their last prompt ("make it longer", "add detail")
   - CLARIFICATION: User's request is ambiguous — you need ONE clarifying question
   - SWARM: User wants a new prompt engineered — route to appropriate agents

3. Return structured JSON with your decision

RESPONSE FORMAT (valid JSON only):
{{
  "user_facing_message": "What the user sees immediately (2-4 sentences max)",
  "proceed_with_swarm": true/false,
  "agents_to_run": ["intent", "domain"],  // subset of: intent, context, domain
  "clarification_needed": true/false,
  "clarification_question": "Your one question if clarification needed, else null",
  "skip_reasons": {{"context": "reason or null"}},
  "tone_used": "direct" | "casual" | "technical",
  "profile_applied": true/false
}}

ROUTING RULES (in order):
1. message.length < 10 → CONVERSATION (user is being brief)
2. Modification phrases ("make it longer/shorter/better") → FOLLOWUP
3. Ambiguity detected → CLARIFICATION (ask ONE question)
4. Otherwise → SWARM (select agents based on confidence)

AGENT SELECTION LOGIC:
- Always run "intent" unless message is crystal clear
- Skip "context" if no session history
- Skip "domain" if user profile has domain at >85% confidence
- "prompt_engineer" ALWAYS runs (never skip)
"""

# ═══ ORCHESTRATOR NODE ═══

def orchestrator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kira orchestrator: reads profile + history, decides routing.
    
    Args:
        state: Current PromptForgeState with message and context
        
    Returns:
        Dict with orchestrator_decision and updated state fields
        
    Raises:
        Exception: If LLM call fails after retries (fallback to CONVERSATION)
    """
    try:
        llm = get_fast_llm()
        
        # Extract from state
        message = state.get("message", "")
        user_profile = state.get("user_profile", {})
        conversation_history = state.get("conversation_history", [])
        pending_clarification = state.get("pending_clarification", False)
        
        # Check for pending clarification FIRST
        if pending_clarification:
            logger.info(f"[kira] pending clarification — injecting answer, firing swarm")
            return {
                "orchestrator_decision": {
                    "user_facing_message": "Got it — let me work with that.",
                    "proceed_with_swarm": True,
                    "agents_to_run": ["intent", "domain"],
                    "clarification_needed": False,
                    "clarification_question": None,
                    "skip_reasons": {},
                    "tone_used": "direct",
                    "profile_applied": bool(user_profile),
                },
                "pending_clarification": False,  # Clear flag
                "proceed_with_swarm": True,
            }
        
        # Build context for LLM
        history_context = "\n".join([
            f"{t.get('role', 'USER').upper()}: {t.get('message', '')[:100]}"
            for t in conversation_history[-3:]
        ]) if conversation_history else "No previous conversation"
        
        profile_context = f"User's preferred tone: {user_profile.get('preferred_tone', 'not set')}" if user_profile else "No profile available"
        
        context = f"""
Conversation history:
{history_context}

User profile:
{profile_context}

Current message: {message}

Decide routing and return JSON."""
        
        # Call LLM
        response = llm.invoke([
            SystemMessage(content=KIRA_SYSTEM_PROMPT),
            HumanMessage(content=context)
        ])
        
        # Parse JSON response
        try:
            decision = json.loads(response.content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"[kira] JSON parse failed: {e}")
            # Fallback decision
            decision = {
                "user_facing_message": "Let me help you with that.",
                "proceed_with_swarm": True,
                "agents_to_run": ["intent"],
                "clarification_needed": False,
                "clarification_question": None,
                "skip_reasons": {},
                "tone_used": "direct",
                "profile_applied": False,
            }
        
        # Validate required fields
        required_fields = [
            "user_facing_message",
            "proceed_with_swarm",
            "agents_to_run",
            "clarification_needed",
        ]
        
        for field in required_fields:
            if field not in decision:
                logger.warning(f"[kira] missing field '{field}' — adding default")
                if field == "user_facing_message":
                    decision[field] = "Processing your request..."
                elif field == "proceed_with_swarm":
                    decision[field] = True
                elif field == "agents_to_run":
                    decision[field] = ["intent"]
                elif field == "clarification_needed":
                    decision[field] = False
        
        # Check forbidden phrases in user_facing_message
        for phrase in KIRA_FORBIDDEN_PHRASES:
            if phrase.lower() in decision["user_facing_message"].lower():
                logger.warning(f"[kira] forbidden phrase detected: '{phrase}'")
                # Replace with neutral alternative
                decision["user_facing_message"] = decision["user_facing_message"].replace(phrase, "")
        
        logger.info(f"[kira] routing decision: agents={decision['agents_to_run']}, clarification={decision['clarification_needed']}")
        
        return {
            "orchestrator_decision": decision,
            "user_facing_message": decision["user_facing_message"],
            "proceed_with_swarm": decision["proceed_with_swarm"],
        }
        
    except Exception as e:
        logger.error(f"[kira] orchestrator failed: {e}", exc_info=True)
        # Hard fallback — treat as CONVERSATION
        return {
            "orchestrator_decision": {
                "user_facing_message": "I'm here to help. What would you like to improve?",
                "proceed_with_swarm": False,
                "agents_to_run": [],
                "clarification_needed": False,
                "clarification_question": None,
                "skip_reasons": {"orchestrator": str(e)},
                "tone_used": "direct",
                "profile_applied": False,
            },
            "user_facing_message": "I'm here to help. What would you like to improve?",
            "proceed_with_swarm": False,
        }


# ═══ HELPER FUNCTIONS ═══

def detect_modification_phrases(message: str) -> bool:
    """
    Check if message contains modification phrases.
    Used for FOLLOWUP detection.
    """
    modification_phrases = [
        "make it",
        "change it",
        "adjust",
        "modify",
        "add",
        "remove",
        "shorter",
        "longer",
        "better",
        "different",
        "more detail",
        "less formal",
        "more formal",
    ]
    
    message_lower = message.lower()
    return any(phrase in message_lower for phrase in modification_phrases)


def calculate_ambiguity_score(message: str, history: List[Dict]) -> float:
    """
    Simple heuristic for ambiguity detection.
    Returns 0.0-1.0 (higher = more ambiguous).
    """
    score = 0.0
    
    # Short messages are more ambiguous
    if len(message.strip()) < 20:
        score += 0.3
    
    # Questions are often ambiguous
    if "?" in message:
        score += 0.2
    
    # Vague words
    vague_words = ["something", "thing", "stuff", "whatever", "maybe", "perhaps"]
    if any(word in message.lower() for word in vague_words):
        score += 0.3
    
    # No context (first message)
    if len(history) == 0:
        score += 0.2
    
    return min(score, 1.0)
```

---

## ✅ Verification Checklist

### Test 1: Kira Imports Successfully

```bash
python -c "from agents.kira import orchestrator_node; print('✅ Kira imported')"
```

**Expected:** `✅ Kira imported`

### Test 2: Character Constants Present

```bash
python -c "
from agents.kira import KIRA_FORBIDDEN_PHRASES, KIRA_MAX_TOKENS
print(f'Forbidden phrases: {len(KIRA_FORBIDDEN_PHRASES)}')
print(f'Max tokens: {KIRA_MAX_TOKENS}')
print('✅ Constants present')
"
```

**Expected:** 6 forbidden phrases, 150 max tokens

### Test 3: Orchestrator Returns Valid JSON Structure

```bash
python -c "
from agents.kira import orchestrator_node

# Mock state
state = {
    'message': 'write a story',
    'user_profile': {},
    'conversation_history': [],
    'pending_clarification': False,
}

result = orchestrator_node(state)
print(f'Result keys: {list(result.keys())}')

decision = result.get('orchestrator_decision', {})
required = ['user_facing_message', 'proceed_with_swarm', 'agents_to_run', 'clarification_needed']
missing = [f for f in required if f not in decision]

if missing:
    print(f'❌ Missing fields: {missing}')
else:
    print('✅ All required fields present')
"
```

**Expected:** All 4 required fields present

### Test 4: Forbidden Phrases Not in Output

```bash
python -c "
from agents.kira import orchestrator_node, KIRA_FORBIDDEN_PHRASES

state = {
    'message': 'hello there',
    'user_profile': {},
    'conversation_history': [],
    'pending_clarification': False,
}

result = orchestrator_node(state)
message = result['user_facing_message']

found = [p for p in KIRA_FORBIDDEN_PHRASES if p.lower() in message.lower()]
if found:
    print(f'❌ Forbidden phrases found: {found}')
else:
    print('✅ No forbidden phrases')
"
```

**Expected:** `✅ No forbidden phrases`

---

## 🆘 Troubleshooting

### Problem: "Module not found: agents.kira"

**Cause:** Missing `__init__.py` or import path issue

**Solution:**
```bash
# Ensure __init__.py exists
type nul > agents\__init__.py

# Check import
python -c "import sys; sys.path.insert(0, '.'); from agents.kira import orchestrator_node"
```

### Problem: "LLM call times out"

**Cause:** Pollinations API slow or down

**Solution:**
1. Check API key in `.env`
2. Increase timeout in `config.py`
3. Add retry logic with `max_retries=3`

### Problem: "JSON parse fails every time"

**Cause:** LLM not returning valid JSON

**Solution:**
Check the raw response:
```python
print(f"Raw response: {response.content[:500]}")
```

Add more robust parsing or adjust system prompt.

---

## 📝 What Changed

| File | Change |
|------|--------|
| `agents/kira.py` | Created (new file) |
| `agents/kira.py` | Orchestrator node, constants, helpers |

---

## ✅ Checkpoint — DO NOT PROCEED UNTIL

- [ ] Kira imports without errors
- [ ] All character constants present
- [ ] Orchestrator returns all required fields
- [ ] No forbidden phrases in output
- [ ] Fallback works when LLM fails

---

**Next:** Proceed to [STEP_7_clarification_loop.md](./STEP_7_clarification_loop.md)

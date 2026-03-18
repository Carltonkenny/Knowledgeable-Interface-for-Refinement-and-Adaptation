# agents/intent.py
# ─────────────────────────────────────────────
# Intent Agent — First agent in the swarm
#
# Analyzes WHAT the user wants to accomplish.
# Goes beyond literal words to extract the real goal and emotional intent.
#
# Input:  state['raw_prompt'] (user's original prompt)
# Output: state['intent_analysis'] with fields:
#   - primary_intent   → The deep actual goal
#   - secondary_intents → Supporting goals
#   - goal_clarity     → "low" | "medium" | "high"
#   - missing_info     → Specific details that would make the prompt better
#
# Skip Condition: Simple direct command with no ambiguity detected
# Uses fast LLM (nova-fast, 400 tokens, temp 0.1)
# ─────────────────────────────────────────────

import time
import logging
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_fast_llm
from state import AgentState
from utils import parse_json_response

logger = logging.getLogger(__name__)

# ═══ SYSTEM PROMPT ════════════════════════════

SYSTEM_PROMPT = """You are an expert Intent Analyzer specializing in understanding what people truly want to accomplish.

Go beyond the literal words — extract the real goal, emotional intent, and success criteria.

Always respond with ONLY this JSON:
{
  "primary_intent": "the deep actual goal, not just surface request",
  "secondary_intents": ["supporting goals that matter"],
  "goal_clarity": "low or medium or high",
  "missing_info": ["specific missing details that would make this prompt significantly better"]
}

Think deeply:
- "write a story" → primary_intent: "create an emotionally engaging narrative that resonates with readers"
- "fix my code" → primary_intent: "understand why code fails and learn to prevent it"
- "help me with python" → primary_intent: "build confidence and competence in Python programming"
"""


# ═══ INTENT AGENT NODE ═══════════════════════

def intent_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes user's true goal beyond literal words.
    
    Skip Condition: Simple direct command with no ambiguity detected.
    
    Args:
        state: Current AgentState with raw_prompt and orchestrator_decision
        
    Returns:
        Dict with intent_analysis, was_skipped, skip_reason, latency_ms
        
    Example:
        result = intent_agent(state)
        # result["intent_analysis"]["primary_intent"] = "create engaging narrative"
    """
    start_time = time.time()
    
    # ═══ CHECK SKIP CONDITION ═══
    orchestrator = state.get("orchestrator_decision", {})
    
    # Check if orchestrator marked intent for skipping
    if orchestrator.get("skip_intent", False):
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[intent] skipped — {orchestrator.get('intent_skip_reason', 'not specified')}")
        return {
            "intent_analysis": None,  # None for skipped/failed, merge_dict will ignore
            "was_skipped": True,
            "skip_reason": orchestrator.get("intent_skip_reason", "simple direct command"),
            "latency_ms": latency_ms,
        }
    
    # ═══ RUN INTENT ANALYSIS ═══
    try:
        llm = get_fast_llm()
        
        # Support both 'raw_prompt' and 'message' field names
        prompt = state.get('raw_prompt', state.get('message', ''))
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Analyze this prompt: {prompt}")
        ]
        
        response = llm.invoke(messages)
        result = parse_json_response(response.content, agent_name="intent")
        
        latency_ms = int((time.time() - start_time) * 1000)
        result["latency_ms"] = latency_ms
        logger.info(f"[intent] clarity={result.get('goal_clarity', 'unknown')} latency={latency_ms}ms")
        
        return {
            "intent_analysis": result,
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
            "agents_run": ["intent"],
            "agent_latencies": {"intent": latency_ms}
        }
        
    except Exception as e:
        logger.error(f"[intent] failed: {e}", exc_info=True)
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "intent_analysis": None,  # None signals failure, merge_dict will ignore
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
        }


# ═══ VALIDATION FUNCTION ═════════════════════

def validate_intent_output(result: Dict[str, Any]) -> bool:
    """
    Validate intent agent output meets quality gates.
    
    Quality Gates:
    1. primary_intent is non-empty
    2. goal_clarity is valid enum (low/medium/high)
    3. Confidence >= 0.6
    
    Args:
        result: Intent agent output dict
        
    Returns:
        True if passes quality gates, False otherwise
    """
    # Gate 1: Primary intent is non-empty
    primary_intent = result.get("primary_intent", "")
    has_intent = bool(primary_intent.strip())
    
    # Gate 2: Goal clarity is valid
    valid_clarities = ["low", "medium", "high"]
    clarity_valid = result.get("goal_clarity", "") in valid_clarities
    
    # Gate 3: Reasonable confidence (if provided)
    confidence = result.get("confidence", 0.6)
    confidence_ok = confidence >= 0.6
    
    passes = sum([has_intent, clarity_valid, confidence_ok]) >= 2
    
    if not passes:
        logger.warning(f"[intent] quality gate failed — intent={has_intent}, clarity={clarity_valid}, confidence={confidence:.2f}")
    
    return passes

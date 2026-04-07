# agents/context.py
# ─────────────────────────────────────────────
# Context Agent — Second agent in the swarm
#
# Analyzes WHO is asking and their constraints.
# Reads between the lines to identify skill level, tone, and implicit preferences.
#
# Input:  state['raw_prompt'] (user's original prompt)
# Output: state['context_analysis'] with fields:
#   - skill_level          → "beginner" | "intermediate" | "expert"
#   - tone                 → "casual" | "formal" | "technical" | "creative"
#   - constraints          → Real limitations mentioned or strongly implied
#   - implicit_preferences → What the person values based on how they wrote the prompt
#
# Skip Condition: First message in session (zero conversation history)
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

# ── OpenTelemetry Tracing ────────────────────
try:
    from middleware.otel_tracing import get_tracer
except ImportError:
    def get_tracer(name="promptforge"):
        class _NoopSpan:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def set_attribute(self, k, v): pass
        class _NoopTracer:
            def start_as_current_span(self, name): return _NoopSpan()
        return _NoopTracer()

# ═══ SYSTEM PROMPT ════════════════════════════

SYSTEM_PROMPT = """You are an expert Context Extractor who reads between the lines.

Identify not just what is stated but what the person reveals about themselves through word choice, specificity, and framing.

Always respond with ONLY this JSON:
{
  "skill_level": "beginner or intermediate or expert",
  "tone": "casual or formal or technical or creative",
  "constraints": ["real limitations mentioned or strongly implied"],
  "implicit_preferences": ["what this person clearly values based on how they wrote the prompt"],
  "confidence": 0.0-1.0
}

Think deeply:
- Word choice reveals expertise — "thing" vs "module" vs "microservice"
- Specificity reveals clarity of thinking
- "Write a 300-word opening scene with atmosphere" → expert, creative, values craft
"""


# ═══ CONTEXT AGENT NODE ══════════════════════

def context_agent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes WHO the user is and their constraints.
    
    Skip Condition: First message in session (zero conversation history).
    
    Args:
        state: Current AgentState with raw_prompt and conversation_history
        
    Returns:
        Dict with context_analysis, was_skipped, skip_reason, latency_ms
    """
    start_time = time.time()

    # ═══ CONTEXT AGENT RUNS ON EVERY MESSAGE (with or without history) ═══
    # The context agent analyzes the CURRENT MESSAGE even without history.
    # The system prompt is designed for single-message analysis:
    # "Word choice reveals expertise", "Specificity reveals clarity of thinking"
    # History is helpful but NOT required.

    conversation_history = state.get("conversation_history", [])
    prompt = state.get('raw_prompt', state.get('message', ''))

    if len(conversation_history) > 0:
        history_context = "\n".join([
            f"{t.get('role', 'USER').upper()}: {t.get('message', '')[:100]}"
            for t in conversation_history[-3:]
        ])
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Conversation history:\n{history_context}\n\nExtract context from: {prompt}")
        ]
    else:
        # Single-message context extraction
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Extract context from this message alone: {prompt}")
        ]

    # ═══ RUN CONTEXT ANALYSIS ═══
    try:
        tracer = get_tracer("promptforge.agent")
        with tracer.start_as_current_span("agent.context") as span:
            span.set_attribute("agent.skip_checked", True)

            llm = get_fast_llm()

            response = llm.invoke(
                messages,
                config={
                    "tags": ["context_agent", "swarm"],
                    "metadata": {"agent": "context"},
                },
            )
            result = parse_json_response(response.content, agent_name="context")

            latency_ms = int((time.time() - start_time) * 1000)
            result["latency_ms"] = latency_ms
            logger.info(f"[context] skill={result.get('skill_level', 'unknown')} tone={result.get('tone', 'unknown')} latency={latency_ms}ms")

            return {
                "context_analysis": result,
                "was_skipped": False,
                "skip_reason": None,
                "latency_ms": latency_ms,
                "agents_run": ["context"],
                "agent_latencies": {"context": latency_ms}
            }

    except Exception as e:
        logger.error(f"[context] failed: {e}", exc_info=True)
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "context_analysis": None,  # None signals failure, merge_dict will ignore
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
        }


# ═══ VALIDATION FUNCTION ═════════════════════

def validate_context_output(result: Dict[str, Any]) -> bool:
    """
    Validate context agent output meets quality gates.
    
    Quality Gates:
    1. skill_level is valid enum (beginner/intermediate/expert)
    2. tone is valid enum (casual/formal/technical/creative)
    3. Confidence >= 0.6
    
    Args:
        result: Context agent output dict
        
    Returns:
        True if passes quality gates, False otherwise
    """
    valid_skills = ["beginner", "intermediate", "expert"]
    valid_tones = ["casual", "formal", "technical", "creative"]
    
    # Gate 1: Skill level is valid
    skill_valid = result.get("skill_level", "") in valid_skills
    
    # Gate 2: Tone is valid
    tone_valid = result.get("tone", "") in valid_tones
    
    # Gate 3: Reasonable confidence
    confidence = result.get("confidence", 0.6)
    confidence_ok = confidence >= 0.6
    
    passes = sum([skill_valid, tone_valid, confidence_ok]) >= 2
    
    if not passes:
        logger.warning(f"[context] quality gate failed — skill={skill_valid}, tone={tone_valid}, confidence={confidence:.2f}")
    
    return passes

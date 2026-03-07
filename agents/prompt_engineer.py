# agents/prompt_engineer.py
# ─────────────────────────────────────────────
# Prompt Engineer Agent — Final agent in the swarm
#
# Rewrites the original prompt using all upstream analysis.
# Reads intent_analysis, context_analysis, and domain_analysis to produce a dramatically better prompt.
#
# Input:  state['raw_prompt'] + state['intent_analysis'] + state['context_analysis'] + state['domain_analysis']
# Output: state['improved_prompt'] (the rewritten, enhanced prompt)
#
# CRITICAL: This agent NEVER skips — always runs last.
# Uses FULL LLM (nova, 2048 tokens, temp 0.3)
# Quality gate: Retries once if output is empty, shorter than input, or identical.
# ─────────────────────────────────────────────

import json
import time
import logging
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm
from state import AgentState
from utils import parse_json_response
from memory.langmem import get_style_reference

logger = logging.getLogger(__name__)

# ═══ SYSTEM PROMPT ════════════════════════════

SYSTEM_PROMPT = """You are a world-class Prompt Engineer. Your rewrites are specific, purposeful, and dramatically better than the original.

Rules:
1. Match the domain — creative writing gets creative language, technical gets precise language
2. Add a role that fits perfectly — not generic "you are an assistant"
3. Preserve the person's voice and intent — don't sanitize their idea
4. Add only constraints that genuinely improve quality
5. Never make it longer than needed — precision beats length

Always respond with ONLY this JSON:
{
  "improved_prompt": "the full rewritten prompt — specific, purposeful, domain-matched",
  "quality_score": {
    "specificity": 1-5,
    "clarity": 1-5,
    "actionability": 1-5
  },
  "changes_made": ["exactly what you changed and why"]
}"""


# ═══ PROMPT ENGINEER AGENT ═══════════════════

def prompt_engineer_agent(state: AgentState) -> Dict[str, Any]:
    """
    Rewrites raw prompt using swarm analysis.
    
    CRITICAL: This agent NEVER skips — always runs last.
    Uses full LLM (nova, 2048 tokens, temp 0.3).
    
    Quality Gate: Retries once if output is:
    - Empty
    - Shorter than input
    - Identical to input
    
    Args:
        state: Current AgentState with all upstream analysis
        
    Returns:
        Dict with improved_prompt, quality_score, changes_made, was_skipped, latency_ms
    """
    start_time = time.time()
    
    # ═══ GUARD: CHECK UPSTREAM RESULTS ═══
    # Support both 'raw_prompt' and 'message' field names
    prompt = state.get('raw_prompt', state.get('message', ''))
    
    if not any([
        state.get('intent_analysis', {}),
        state.get('context_analysis', {}),
        state.get('domain_analysis', {})
    ]):
        logger.warning("[prompt_engineer] all swarm results empty - returning fallback")
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "improved_prompt": f"[Analysis failed] Original: {prompt}",
            "quality_score": {"specificity": 1, "clarity": 1, "actionability": 1},
            "changes_made": ["No analysis available - returning original"],
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
        }

    # ═══ PREPARE CONTEXT FOR LLM ═══
    try:
        llm = get_llm()
        
        # Get user's best past prompts for style reference
        domain = state.get('domain_analysis', {}).get('primary_domain', 'general')
        style_reference = get_style_reference(
            user_id=state.get('user_id', ''),
            domain=domain,
            count=5
        )
        
        style_context = f"\n\nUser's best past prompts (for style reference):\n{json.dumps(style_reference, indent=2)}" if style_reference else ""

        # Format all upstream analysis
        analysis_context = f"""Original prompt: {prompt}

Intent analysis: {json.dumps(state.get('intent_analysis', {}), indent=2)}

Context analysis: {json.dumps(state.get('context_analysis', {}), indent=2)}

Domain analysis: {json.dumps(state.get('domain_analysis', {}), indent=2)}{style_context}

Rewrite the prompt based on this comprehensive analysis. Match the user's established style and quality bar from their past prompts."""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=analysis_context)
        ]
        
        # ═══ FIRST LLM CALL ═══
        response = llm.invoke(messages)
        result = parse_json_response(response.content, agent_name="prompt_engineer")
        
        improved = result.get("improved_prompt", "")
        
        # ═══ QUALITY GATE ═══
        # Retry once if output is clearly worse than input
        if not improved.strip() or len(improved) < len(prompt) or improved.strip() == prompt.strip():
            logger.warning(f"[prompt_engineer] quality gate failed - output empty/short/identical, retrying once")

            retry_context = f"""Your previous output was inadequate. The improved_prompt must be:
1. Longer and more detailed than the original
2. Significantly different from the original
3. Include specific role, constraints, and quality gates

Original prompt: {prompt}

Analysis context: {analysis_context}

Rewrite the prompt with substantially more detail and specificity."""
            
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=retry_context)
            ]
            
            response = llm.invoke(messages)
            result = parse_json_response(response.content, agent_name="prompt_engineer")
            improved = result.get("improved_prompt", "")
        
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[prompt_engineer] output: {len(improved)} chars, latency={latency_ms}ms")
        
        return {
            "improved_prompt": improved,
            "quality_score": result.get("quality_score", {"specificity": 3, "clarity": 3, "actionability": 3}),
            "changes_made": result.get("changes_made", ["Improved prompt structure"]),
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
        }
        
    except Exception as e:
        logger.error(f"[prompt_engineer] failed: {e}", exc_info=True)
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "improved_prompt": state["raw_prompt"],
            "quality_score": {"specificity": 1, "clarity": 1, "actionability": 1},
            "changes_made": [f"Error: {str(e)}"],
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
        }


# ═══ VALIDATION FUNCTION ═════════════════════

def validate_engineer_output(result: Dict[str, Any], original_prompt: str) -> bool:
    """
    Validate prompt engineer output meets quality gates.
    
    Quality Gates:
    1. improved_prompt differs from original
    2. At least 3 changes_made documented
    3. Quality score average >= 3.0
    
    Args:
        result: Prompt engineer output dict
        original_prompt: User's original prompt
        
    Returns:
        True if passes quality gates, False otherwise
    """
    improved = result.get("improved_prompt", "")
    changes = result.get("changes_made", [])
    quality = result.get("quality_score", {})
    
    # Gate 1: Differs from original
    differs = improved.strip() != original_prompt.strip() and len(improved) > len(original_prompt)
    
    # Gate 2: Has changes documented
    has_changes = len(changes) >= 3
    
    # Gate 3: Quality score acceptable
    avg_quality = sum([
        quality.get("specificity", 0),
        quality.get("clarity", 0),
        quality.get("actionability", 0)
    ]) / 3
    acceptable_quality = avg_quality >= 3.0
    
    passes = differs and has_changes and acceptable_quality
    
    if not passes:
        logger.warning(f"[prompt_engineer] validation failed — differs={differs}, changes={has_changes}, quality={avg_quality:.1f}")
    
    return passes

# agents/domain.py
# ─────────────────────────────────────────────
# Domain Agent — Third agent in the swarm
#
# Classifies WHAT field/domain the prompt belongs to.
# Identifies the specific craft, discipline, and prompt engineering patterns that apply.
#
# Input:  state['raw_prompt'] (user's original prompt)
# Output: state['domain_analysis'] with fields:
#   - primary_domain    → Precise field name
#   - sub_domain        → Specific discipline within that field
#   - relevant_patterns → Prompt engineering patterns to apply
#   - complexity        → "simple" | "moderate" | "complex"
#
# Skip Condition: User profile has domain at >85% confidence
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

SYSTEM_PROMPT = """You are an expert Domain Identifier who classifies requests with precision.

Go beyond obvious labels — identify the specific craft, discipline, and patterns that apply.

Always respond with ONLY this JSON:
{
  "primary_domain": "precise field name",
  "sub_domain": "specific discipline within that field",
  "relevant_patterns": ["the prompt engineering patterns that will make this better"],
  "complexity": "simple or moderate or complex",
  "confidence": 0.0-1.0
}

Relevant patterns to consider:
- role_assignment: give the AI a specific expert persona
- output_format: specify exactly how the response should look
- constraints: add quality guardrails
- examples: include what good looks like
- chain_of_thought: ask for reasoning steps
- tone_matching: match the creative/technical register

Example:
- "sci-fi mystery story" → primary_domain: creative writing, patterns: [role_assignment, tone_matching, output_format]
"""


# ═══ DOMAIN AGENT NODE ═══════════════════════

def domain_agent(state: AgentState) -> Dict[str, Any]:
    """
    Identifies user's domain expertise and relevant patterns.
    
    Skip Condition: User profile has domain confidence > 85%
    
    Args:
        state: Current AgentState with raw_prompt and user_profile
        
    Returns:
        Dict with domain_analysis, was_skipped, skip_reason, latency_ms
    """
    start_time = time.time()
    
    # ═══ CHECK SKIP CONDITION ═══
    user_profile = state.get("user_profile", {})
    domain_confidence = user_profile.get("domain_confidence", 0.0)
    
    if domain_confidence > 0.85:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[domain] skipped — high confidence ({domain_confidence:.2f})")
        return {
            "domain_analysis": {},
            "was_skipped": True,
            "skip_reason": f"domain confidence {domain_confidence:.2f} > 0.85",
            "latency_ms": latency_ms,
        }
    
    # ═══ RUN DOMAIN ANALYSIS ═══
    try:
        llm = get_fast_llm()
        
        # Support both 'raw_prompt' and 'message' field names
        prompt = state.get('raw_prompt', state.get('message', ''))
        
        # Extract dominant domains from profile for context
        dominant_domains = user_profile.get("dominant_domains", [])
        domains_context = f"User's past domains: {', '.join(dominant_domains)}" if dominant_domains else "No domain history available"
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"{domains_context}\n\nIdentify the domain of: {prompt}")
        ]
        
        response = llm.invoke(messages)
        result = parse_json_response(response.content, agent_name="domain")
        
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[domain] domain={result.get('primary_domain', 'unknown')} confidence={result.get('confidence', 0):.2f} latency={latency_ms}ms")
        
        return {
            "domain_analysis": result,
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
        }
        
    except Exception as e:
        logger.error(f"[domain] failed: {e}", exc_info=True)
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "domain_analysis": {},
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
        }


# ═══ VALIDATION FUNCTION ═════════════════════

def validate_domain_output(result: Dict[str, Any]) -> bool:
    """
    Validate domain agent output meets quality gates.
    
    Quality Gates:
    1. primary_domain is non-empty and not generic
    2. At least 1 relevant pattern identified
    3. Confidence >= 0.6
    
    Args:
        result: Domain agent output dict
        
    Returns:
        True if passes quality gates, False otherwise
    """
    generic_domains = ["tech", "software", "coding", "programming", "general"]
    
    # Gate 1: Domain is specific
    primary_domain = result.get("primary_domain", "").lower()
    is_specific = primary_domain and primary_domain not in generic_domains
    
    # Gate 2: Has patterns
    patterns = result.get("relevant_patterns", [])
    has_patterns = len(patterns) >= 1
    
    # Gate 3: Reasonable confidence
    confidence = result.get("confidence", 0.0)
    reasonable_confidence = confidence >= 0.6
    
    passes = sum([is_specific, has_patterns, reasonable_confidence]) >= 2
    
    if not passes:
        logger.warning(f"[domain] quality gate failed — specific={is_specific}, patterns={has_patterns}, confidence={confidence:.2f}")
    
    return passes

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
from agents.quality_gate import evaluate_prompt_quality

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
    "actionability": 1-5,
    "overall": 1-5
  },
  "changes_made": ["exactly what you changed and why"]
}"""


# ═══ PROMPT ENGINEER AGENT ═══════════════════

def generate_diff(original: str, improved: str) -> list:
    """
    Generate a simple diff between original and improved prompts.
    Returns array of {type: 'add'|'remove'|'keep', text: str}
    
    This is a simplified diff - just marks added/removed sentences.
    """
    # Simple sentence-level diff
    original_sentences = [s.strip() for s in original.replace('\n', ' ').split('.') if s.strip()]
    improved_sentences = [s.strip() for s in improved.replace('\n', ' ').split('.') if s.strip()]
    
    diff = []
    
    # Mark removed sentences
    for sent in original_sentences:
        if sent not in improved_sentences and sent:
            diff.append({'type': 'remove', 'text': sent + '. '})
    
    # Mark added sentences
    for sent in improved_sentences:
        if sent not in original_sentences and sent:
            diff.append({'type': 'add', 'text': sent + '. '})
    
    # If no changes detected, mark as keep
    if not diff:
        diff = [{'type': 'keep', 'text': improved}]
    
    return diff


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

        # Generate diff showing no changes
        prompt_diff = generate_diff(prompt, f"[Analysis failed] Original: {prompt}")

        return {
            "improved_prompt": f"[Analysis failed] Original: {prompt}",
            "quality_score": {"specificity": 1, "clarity": 1, "actionability": 1},
            "changes_made": ["No analysis available - returning original"],
            "prompt_diff": prompt_diff,
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
            "agent_latencies": {"prompt_engineer": latency_ms},
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

        # ═══ FR-1: AI FRUSTRATION CONSTRAINT (SPEC V1) ═══
        # Add user-specific constraints based on their onboarding frustration
        user_profile = state.get('user_profile', {})
        frustration = user_profile.get('ai_frustration', '')
        frustration_detail = user_profile.get('frustration_detail', '')

        frustration_constraint = ""
        if frustration == 'too_vague':
            frustration_constraint = "\n\nUSER PREFERENCE: AI responses are too vague. Be extremely specific with concrete examples. Avoid generic statements."
        elif frustration == 'too_wordy':
            frustration_constraint = "\n\nUSER PREFERENCE: AI responses are too wordy. Be concise and direct. Get to the point quickly."
        elif frustration == 'too_brief':
            frustration_constraint = "\n\nUSER PREFERENCE: AI responses are too brief. Provide detailed explanations with context. Don't skip steps."
        elif frustration == 'wrong_tone':
            frustration_constraint = "\n\nUSER PREFERENCE: AI uses wrong tone. Match the tone carefully to the audience and purpose."
        elif frustration == 'repeats':
            frustration_constraint = "\n\nUSER PREFERENCE: AI repeats itself. Don't say the same thing multiple times. Each sentence should add value."
        elif frustration == 'misses_context':
            frustration_constraint = "\n\nUSER PREFERENCE: AI misses context. Consider the full situation. Ask clarifying questions if needed."

        if frustration_constraint:
            logger.debug(f"[prompt_engineer] frustration constraint added: {frustration}")

        # ═══ FR-4: AUDIENCE CONSTRAINT (SPEC V1) ═══
        # Add audience-specific style constraints
        audience = user_profile.get('audience', '')

        audience_constraint = ""
        if audience == 'technical':
            audience_constraint = "\n\nAUDIENCE: Technical experts (developers, engineers, data scientists). Use precise terminology, assume domain knowledge, skip basic explanations."
        elif audience == 'business':
            audience_constraint = "\n\nAUDIENCE: Business professionals (managers, executives, stakeholders). Focus on ROI, efficiency, and practical outcomes. Avoid overly technical jargon."
        elif audience == 'general':
            audience_constraint = "\n\nAUDIENCE: General public (non-specialists, broad audience). Explain concepts clearly, avoid jargon, use relatable examples."
        elif audience == 'academic':
            audience_constraint = "\n\nAUDIENCE: Academic (researchers, students, educators). Use formal tone, emphasize evidence and methodology, cite sources when applicable."
        elif audience == 'creative':
            audience_constraint = "\n\nAUDIENCE: Creative community (artists, writers, designers). Use evocative language, embrace ambiguity, prioritize inspiration over precision."

        if audience_constraint:
            logger.debug(f"[prompt_engineer] audience constraint added: {audience}")

        # Combine all context
        personalization_context = frustration_constraint + audience_constraint

        # Format all upstream analysis
        analysis_context = f"""Original prompt: {prompt}

Intent analysis: {json.dumps(state.get('intent_analysis', {}), indent=2)}

Context analysis: {json.dumps(state.get('context_analysis', {}), indent=2)}

Domain analysis: {json.dumps(state.get('domain_analysis', {}), indent=2)}{style_context}{personalization_context}

Rewrite the prompt based on this comprehensive analysis. Match the user's established style and quality bar from their past prompts. Honor their frustration preferences and audience needs."""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=analysis_context)
        ]
        
        # ═══ FIRST LLM CALL ═══
        response = llm.invoke(messages)
        result = parse_json_response(response.content, agent_name="prompt_engineer")

        # Debug: Log what LLM returned for quality_score
        logger.info(f"[prompt_engineer] LLM returned quality_score: {result.get('quality_score', 'MISSING')}")

        improved = result.get("improved_prompt", "")

        # ═══ MULTI-CRITERIA QUALITY GATE (Phase 2.2) ═══
        # Evaluate with 5 dimensions: similarity, density, constraints, specificity, LLM judge
        quality_report = evaluate_prompt_quality(
            original=prompt,
            improved=improved,
            context={
                'required_constraints': ['role', 'audience', 'format'],  # Default constraints
                'domain': state.get('domain_analysis', {}).get('primary_domain', 'general'),
            }
        )
        
        logger.info(
            f"[prompt_engineer] quality gate: overall={quality_report.overall:.2f}, "
            f"retry={quality_report.should_retry}, reason={quality_report.retry_reason or 'none'}"
        )
        
        # Retry if quality gate fails
        if quality_report.should_retry:
            logger.warning(f"[prompt_engineer] quality gate failed - {quality_report.retry_reason}, retrying once")
            
            retry_context = f"""Your previous output did not meet quality standards.

QUALITY FEEDBACK:
{chr(10).join(quality_report.feedback)}

REQUIRED IMPROVEMENTS:
1. Add specific role assignment (expert persona)
2. Include concrete constraints (length, format, tone)
3. Add measurable success criteria
4. Include examples or patterns to follow
5. Be more specific - add numbers, details, examples

Original prompt: {prompt}

Analysis context: {analysis_context}

Rewrite the prompt with substantially higher quality addressing all feedback above."""

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=retry_context)
            ]

            response = llm.invoke(messages)
            result = parse_json_response(response.content, agent_name="prompt_engineer")
            improved = result.get("improved_prompt", "")
            
            # Re-evaluate after retry (for logging)
            quality_report_retry = evaluate_prompt_quality(
                original=prompt,
                improved=improved,
                context={'required_constraints': ['role', 'audience', 'format']}
            )
            logger.info(f"[prompt_engineer] after retry: overall={quality_report_retry.overall:.2f}")

        # Fallback to simple quality checks if multi-criteria passed
        if not improved.strip() or len(improved) < len(prompt) or improved.strip() == prompt.strip():
            logger.warning(f"[prompt_engineer] simple quality gate failed - output empty/short/identical, retrying once")

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

        # Generate diff between original and improved
        prompt_diff = generate_diff(prompt, improved)

        # Calculate overall score if missing or 0
        qs = result.get("quality_score", {"specificity": 3, "clarity": 3, "actionability": 3})
        if not qs.get("overall"):
            qs["overall"] = round((qs.get("specificity", 3) + qs.get("clarity", 3) + qs.get("actionability", 3)) / 3, 1)

        # ═══ SECTION 3: AGENT LATENCIES ═══
        logger.info(f"[prompt_engineer] self_latency={latency_ms}ms")

        return {
            "improved_prompt": improved,
            "quality_score": qs,
            "changes_made": result.get("changes_made", ["Improved prompt structure"]),
            "prompt_diff": prompt_diff,
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
            "agent_latencies": {"prompt_engineer": latency_ms},
            "agents_run": ["prompt_engineer"],
        }
        
    except Exception as e:
        logger.error(f"[prompt_engineer] failed: {e}", exc_info=True)
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "improved_prompt": state.get("raw_prompt", state.get("message", "")),
            "quality_score": {"specificity": 1, "clarity": 1, "actionability": 1},
            "changes_made": [f"Error: {str(e)}"],
            "prompt_diff": [{"type": "keep", "text": state.get("raw_prompt", state.get("message", ""))}],
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
            "agent_latencies": {"prompt_engineer": latency_ms},
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

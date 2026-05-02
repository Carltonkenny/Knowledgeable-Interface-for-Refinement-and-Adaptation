# agents/handlers/unified.py
"""
Unified Kira Handler.

CONTAINS:
    1. kira_unified_handler() — Intent detection + response in ONE LLM call
    2. build_kira_context() — Build context for unified handler
    3. fallback_unified_response() — Fallback when unified handler fails

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
"""

from typing import Dict, Any, List, Optional
import logging
import time
import os

logger = logging.getLogger(__name__)

# Configurable memory recall limit
TOP_K_MEMORIES = int(os.getenv("TOP_K_MEMORIES", "5"))

# Import prompts from modular location
from agents.prompts.shared import FORBIDDEN_PHRASES


def kira_unified_handler(
    message: str,
    history: List[Dict[str, Any]],
    user_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Unified intent detection + response with full context.
    
    ONE LLM call instead of two (classify + respond).
    Handles CONVERSATION, FOLLOWUP, and NEW_PROMPT routing.
    
    RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
    
    Args:
        message: User's message
        history: Last 4 conversation turns
        user_profile: User's profile from Supabase
        
    Returns:
        Dict with:
            - intent: "conversation" | "followup" | "new_prompt"
            - response: Personality-driven reply
            - improved_prompt: Full improved prompt (if followup/new_prompt)
            - changes_made: List of changes
            - confidence: 0.0-1.0
            - confidence_reason: Brief explanation
            - clarification_needed: True/False
            - personality_adaptation: Dict with formality/technical scores
            - metadata: Additional context
        
    Example:
        >>> result = kira_unified_handler(
        ...     message="make it async",
        ...     history=[...],
        ...     user_profile={"primary_use": "coding", ...}
        ... )
        >>> result["intent"]
        "followup"
    """
    from config import get_fast_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    from utils import parse_json_response
    from agents.context.builder import build_context_block
    from agents.context.scorer import score_input_quality
    
    start_time = time.time()
    
    try:
        llm = get_fast_llm()  # Fast model for latency

        # Query LangMem for user's relevant memories (RULES.md: Memory system integration)
        from memory.langmem import query_langmem
        langmem_context = []  # Default to empty if user_id not available
        user_id = user_profile.get("user_id")
        if user_id:
            langmem_context = query_langmem(
                user_id=user_id,
                query=message,
                top_k=TOP_K_MEMORIES
            )
        else:
            logger.debug("[kira_unified] user_id not in profile, skipping LangMem query")

        # Summarize memories for metadata (NEW: Specific recall for thought transparency)
        memory_summary = None
        if langmem_context:
            # Create a specific summary of top 3 memory domains or snippets
            topics = list(set([m.get("domain", "general") for m in langmem_context[:3]]))
            topic_str = " and ".join(topics)
            memory_summary = f"Recalled {len(langmem_context)} memories, focusing on your work in {topic_str}."

        # Build rich context AFTER fetching memories
        quality = score_input_quality(message, len(history) > 0)
        context = build_kira_context(message, history, user_profile, langmem_context)

        # Get Kira system prompt with personality
        system_prompt = _get_kira_unified_prompt()

        # Single LLM call with unified prompt
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])

        # Parse JSON response
        result = parse_json_response(response.content, "kira_unified")

        # Validate response structure
        if not result.get("intent") or not result.get("response"):
            logger.warning(f"[kira_unified] invalid response structure → fallback")
            return fallback_unified_response(message, history, user_profile)

        # Log success with latency
        latency_ms = int((time.time() - start_time) * 1000)
        result["latency_ms"] = latency_ms
        result["input_quality"] = quality.score
        result["memories_applied"] = len(langmem_context) if langmem_context else 0
        result["memory_summary"] = memory_summary # Inject for thought stream extraction

        # ═══ PERSONALITY ADAPTATION & VALIDATION ═══
        # Adapt Kira's tone to user's communication style
        try:
            from agents.orchestration.personality import adapt_kira_personality
            
            adaptation = adapt_kira_personality(
                message=message,
                user_profile=user_profile,
                response_text=result["response"]
            )
            
            # Add adaptation data to result for frontend/analytics
            result["personality_adaptation"] = {
                "detected_formality": adaptation.detected_user_style.get("formality", 0.5),
                "detected_technical": adaptation.detected_user_style.get("technical", 0.5),
                "adaptation_notes": adaptation.adaptation_guidance,
                "violations": adaptation.forbidden_phrases_detected,
            }
            
            # Log violations if any (for monitoring personality consistency)
            if adaptation.forbidden_phrases_detected:
                logger.warning(f"[kira_unified] forbidden phrases detected: {adaptation.forbidden_phrases_detected}")
                
        except Exception as e:
            logger.debug(f"[kira_unified] personality adaptation skipped: {e}")
            result["personality_adaptation"] = None

        logger.info(f"[kira_unified] intent={result['intent']} latency={latency_ms}ms memories={result['memories_applied']}")

        return result

    except Exception as e:
        logger.error(f"[kira_unified] failed: {e}")
        # Fallback to existing handlers
        return fallback_unified_response(message, history, user_profile)


def build_kira_context(
    message: str,
    history: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    langmem_context: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Build rich context string for unified Kira call.

    Args:
        message: Current user message
        history: Last 4 conversation turns
        user_profile: User's profile from Supabase
        langmem_context: User's relevant long-term memories


    Returns:
        Formatted context string for LLM

    Example:
        >>> context = build_kira_context(
        ...     message="make it async",
        ...     history=[...],
        ...     user_profile={"primary_use": "coding", ...}
        ... )
    """
    try:
        # Extract last improved prompt
        last_improved = None
        for turn in reversed(history):
            if turn.get('improved_prompt'):
                last_improved = turn['improved_prompt'][:500]
                break

        # Build rich user context from profile
        job_title = user_profile.get('job_title', '')
        company = user_profile.get('company', '')
        bio = user_profile.get('bio', '')
        location = user_profile.get('location', '')
        preferred_tone = user_profile.get('preferred_tone', 'direct')

        # Build user context header
        context_parts = []
        context_parts.append("User Context:")
        if job_title or company:
            role_str = f"{job_title} at {company}" if job_title and company else (job_title or company)
            context_parts.append(f"- Role: {role_str}")
        if bio:
            context_parts.append(f"- Bio: {bio[:200]}")
        if location:
            context_parts.append(f"- Location: {location}")
        context_parts.append(f"- Preferred tone: {preferred_tone}")

        # Infer experience level from profile fields
        xp_total = user_profile.get('xp_total', 0)
        if xp_total > 5000:
            experience_level = "expert"
        elif xp_total > 1000:
            experience_level = "intermediate"
        else:
            experience_level = "beginner"
        context_parts.append(f"- Experience level: {experience_level}")

        # Add active domains from profile
        dominant_domains = user_profile.get('dominant_domains', [])
        if dominant_domains:
            domain_str = ", ".join(str(d) for d in dominant_domains[:3])
            context_parts.append(f"- Active domains: {domain_str}")

        # Add relevant memories
        if langmem_context:
            context_parts.append("\nRelevant Past Memories:")
            for m in langmem_context:
                domain = m.get('domain', 'general').upper()
                content = m.get('content', '')
                if content:
                    context_parts.append(f"  [{domain}] {content}")

        # Add conversation history
        context_parts.append(f"\nLast {min(4, len(history))} conversation turns:")
        for turn in history[-4:]:
            role = turn.get('role', 'USER').upper()
            msg = turn.get('message', '')[:100]
            context_parts.append(f"  {role}: {msg}")

        if last_improved:
            context_parts.append(f"\nLast improved prompt: {last_improved}")

        # Add current message
        context_parts.insert(0, f"User's message: {message}")

        return "\n".join(context_parts)

    except Exception as e:
        logger.error(f"[build_kira_context] failed: {e}")
        return f"User's message: {message}"


def _get_kira_unified_prompt() -> str:
    """
    Get Kira unified system prompt with personality.

    Returns:
        Full system prompt string
    """
    return """You are Kira — a sharp, witty, genuinely useful AI prompt engineer.

PERSONALITY:
- Warm but not sycophantic — never say "great question!" or "certainly!"
- Direct and confident — opinions, not just options
- Occasionally playful — well-placed emoji or light humor
- Expert but not arrogant — explain clearly without talking down

FORBIDDEN PHRASES (NEVER USE):
"Certainly", "Great question", "Of course", "I'd be happy to", "Let me help you", "No problem", "Sure!", "Absolutely", "Happy to help"

INTENT ROUTING RULES (CRITICAL):
- "conversation": Use this for ANY greeting ("hi", "hello"), gratitude or acknowledgments ("thanks", "ok cool", "got it"), questions about your capabilities ("what can you do?"), general advice, or small talk. DO NOT trigger 'new_prompt' for these!
- "followup": Use this ONLY if the user is asking to modify or tweak the PREVIOUSLY generated prompt shown in the history.
- "new_prompt": Use this EXCLUSIVELY when the user explicitly provides a rough idea, task, or concept that they want engineered into a pristine, structured prompt (e.g. "Create a blog post calendar", "Draft an email to my boss"). If they are just asking a question about *you*, it is NOT a new_prompt!

RESPONSE FORMAT (JSON):
{
  "intent": "conversation|followup|new_prompt",
  "response": "Your personality-driven reply (2-4 sentences)",
  "improved_prompt": "Full improved prompt (if followup/new_prompt)",
  "changes_made": ["Specific changes and why"],
  "confidence": 0.0-1.0,
  "confidence_reason": "Brief explanation",
  "clarification_needed": true/false,
  "personality_adaptation": {
    "detected_formality": 0.0-1.0,
    "detected_technical": 0.0-1.0,
    "adaptation_notes": "Brief explanation"
  }
}

IMPORTANT: Output ONLY valid JSON. No markdown, no code blocks, no extra text. Start with { and end with }.
"""


def fallback_unified_response(
    message: str,
    history: List[Dict[str, Any]],
    user_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fallback when unified handler fails.
    
    Uses existing handle_conversation() and handle_followup().
    
    RULES.md: Graceful degradation, never expose errors to user.
    
    Args:
        message: User's message
        history: Last 4 conversation turns
        user_profile: User's profile
        
    Returns:
        Dict with intent, response, improved_prompt, confidence
    """
    try:
        # Try to detect intent from message
        if len(message.strip()) < 10:
            intent = "conversation"
        elif any(word in message.lower() for word in ["make", "change", "add", "remove", "more", "less"]):
            intent = "followup"
        else:
            intent = "new_prompt"
        
        if intent == "conversation":
            from .conversation import handle_conversation
            reply = handle_conversation(message, history)
            return {
                "intent": "conversation",
                "response": reply,
                "improved_prompt": None,
                "changes_made": [],
                "confidence": 0.5,
                "confidence_reason": "Using fallback handler",
                "clarification_needed": False,
                "metadata": {"fallback": True}
            }
        elif intent == "followup":
            from .followup import handle_followup
            result = handle_followup(message, history)
            if result:
                return {
                    "intent": "followup",
                    "response": "Updated! Here's your refined prompt ✨",
                    "improved_prompt": result.get("improved_prompt", ""),
                    "changes_made": result.get("changes_made", []),
                    "confidence": 0.5,
                    "confidence_reason": "Using fallback handler",
                    "clarification_needed": False,
                    "metadata": {"fallback": True}
                }
        
        # Default to new_prompt
        return {
            "intent": "new_prompt",
            "response": "Let me craft something precise for you.",
            "improved_prompt": None,
            "changes_made": [],
            "confidence": 0.5,
            "confidence_reason": "Using fallback handler",
            "clarification_needed": False,
            "metadata": {"fallback": True}
        }
        
    except Exception as e:
        logger.error(f"[fallback_unified_response] failed: {e}")
        # Ultimate fallback
        return {
            "intent": "conversation",
            "response": "I'm here to help. What would you like to improve?",
            "improved_prompt": None,
            "changes_made": [],
            "confidence": 0.3,
            "confidence_reason": "Ultimate fallback",
            "clarification_needed": False,
            "metadata": {"fallback": True, "error": str(e)}
        }

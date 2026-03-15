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

logger = logging.getLogger(__name__)

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
        
        # Build rich context
        context = build_kira_context(message, history, user_profile)
        
        # Score input quality
        quality = score_input_quality(message, len(history) > 0)
        
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
        
        logger.info(f"[kira_unified] intent={result['intent']} latency={latency_ms}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"[kira_unified] failed: {e}")
        # Fallback to existing handlers
        return fallback_unified_response(message, history, user_profile)


def build_kira_context(
    message: str,
    history: List[Dict[str, Any]],
    user_profile: Dict[str, Any]
) -> str:
    """
    Build rich context string for unified Kira call.
    
    Args:
        message: Current user message
        history: Last 4 conversation turns
        user_profile: User's profile from Supabase
        
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
        
        # Build context parts
        context_parts = [
            f"User's message: {message}",
            f"User's primary use: {user_profile.get('primary_use', 'general')}",
            f"User's audience: {user_profile.get('audience', 'general')}",
            f"User's preferred tone: {user_profile.get('preferred_tone', 'direct')}",
            f"\nLast {min(4, len(history))} conversation turns:",
        ]
        
        for turn in history[-4:]:
            role = turn.get('role', 'USER').upper()
            msg = turn.get('message', '')[:100]
            context_parts.append(f"  {role}: {msg}")
        
        if last_improved:
            context_parts.append(f"\nLast improved prompt: {last_improved}")
        
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

YOUR TASK:
1. Read the user's message and conversation history
2. Understand their intent (conversation/followup/new_prompt)
3. Respond naturally with your personality
4. If they want a prompt improved, provide the improved version

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

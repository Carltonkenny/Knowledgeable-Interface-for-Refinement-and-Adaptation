# agents/handlers/followup.py
"""
Followup Handler.

CONTAINS:
    1. handle_followup() — Refine last improved prompt based on modification request

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling with fallback
    - Logging contextual
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

FOLLOWUP_PROMPT = """You are refining a prompt based on user feedback.

Read the original improved prompt and apply the user's modification request.
Return the complete updated prompt.

Be precise — apply exactly what they asked for, no more, no less."""


def handle_followup(
    message: str,
    history: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Refine last improved prompt based on modification request.
    
    Skips full swarm — 1 LLM call only.
    Returns None if no previous prompt found — caller treats as NEW_PROMPT.
    
    Args:
        message: User's modification request
        history: Last 4 conversation turns
        
    Returns:
        Dict with improved_prompt and changes_made, or None if no previous prompt
        
    Example:
        >>> handle_followup("make it shorter", [{"improved_prompt": "Write a long story..."}])
        {'improved_prompt': 'Write a concise story...', 'changes_made': ['Shortened length']}
    """
    from config import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    from utils import parse_json_response
    
    try:
        # Find last improved prompt
        last_improved = None
        last_raw = None
        
        for turn in reversed(history):
            if turn.get("improved_prompt") and not last_improved:
                last_improved = turn["improved_prompt"]
            if turn.get("role") == "user" and not last_raw:
                last_raw = turn["message"]
        
        if not last_improved:
            logger.warning("[followup] no previous prompt found → NEW_PROMPT")
            return None
        
        llm = get_llm()
        
        context = f"""Original raw prompt: {last_raw or 'Not available'}

Previously improved prompt:
{last_improved}

User's modification request: {message}

Apply the changes and return the complete updated prompt."""
        
        response = llm.invoke([
            SystemMessage(content=FOLLOWUP_PROMPT),
            HumanMessage(content=context)
        ])
        
        result = parse_json_response(response.content, agent_name="followup")
        
        if not result.get("improved_prompt"):
            logger.warning("[followup] empty result → NEW_PROMPT")
            return None
        
        logger.info("[followup] refined successfully")
        return result
        
    except Exception as e:
        logger.error(f"[followup] failed: {e}")
        return None

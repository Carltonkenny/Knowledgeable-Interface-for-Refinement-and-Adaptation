# agents/handlers/conversation.py
"""
Conversation Handler.

CONTAINS:
    1. handle_conversation() — Generate engaging conversational reply

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling with fallback
    - Logging contextual
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

CONVERSATION_PROMPT = """You are Kira having a natural conversation.

Respond warmly and conversationally. End with an invitation to use PromptForge.

Keep it brief (1-3 sentences). Be genuinely helpful, not robotic."""


def handle_conversation(
    message: str,
    history: List[Dict[str, Any]]
) -> str:
    """
    Generate engaging personality-driven conversational reply.
    
    Always guides back toward prompt improvement.
    Returns hardcoded fallback if LLM fails — never exposes errors to user.
    
    Args:
        message: User's message
        history: Last 4 conversation turns
        
    Returns:
        Conversational reply string
        
    Example:
        >>> handle_conversation("hi", [])
        "Hey! I'm Kira — I turn messy prompts into precise ones. What are you working on?"
    """
    from config import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    from utils import format_history
    
    try:
        llm = get_llm()
        history_text = format_history(history)
        
        context = f"""Conversation history:
{history_text}

User just said: {message}

Respond naturally and engagingly. End with an invitation."""
        
        response = llm.invoke([
            SystemMessage(content=CONVERSATION_PROMPT),
            HumanMessage(content=context)
        ])
        
        reply = response.content.strip()
        logger.info(f"[conversation] reply: {len(reply)} chars")
        return reply
        
    except Exception as e:
        logger.error(f"[conversation] failed: {e}")
        return (
            "Hey! I'm PromptForge — I turn rough prompts into precise, powerful ones. "
            "What would you like to improve today? 🚀"
        )

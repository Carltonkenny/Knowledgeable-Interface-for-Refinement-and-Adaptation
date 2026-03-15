# agents/context/builder.py
"""
Context Building Utilities.

CONTAINS:
    1. build_context_block() — Dynamic user context injection
    2. format_session_level() — Session experience formatting
    3. format_domains() — Domain expertise formatting
    4. format_tone_preference() — Tone preference formatting
    5. format_quality_trend() — Quality trend formatting
    6. format_memories() — LangMem memory formatting

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def build_context_block(
    user_profile: Dict[str, Any],
    langmem_memories: List[Dict[str, Any]],
    session_count: int,
    recent_quality_trend: Optional[List[float]] = None
) -> str:
    """
    Build dynamic context block injected into every Kira prompt.
    
    This is the memory injection point. All user profile data and LangMem
    memories are formatted here and prepended to the orchestrator prompt.
    
    Args:
        user_profile: Dict from user_profiles table. Keys: dominant_domains,
                      preferred_tone, clarification_patterns, avg_quality_score.
        langmem_memories: List of dicts from LangMem semantic search.
                          Each has: content, domain, quality_score, created_at.
        session_count: Total sessions this user has had.
        recent_quality_trend: Optional list of last 5 quality scores (float 1-5).
                               Used to detect improving/declining trajectory.
    
    Returns:
        Formatted string to prepend to system prompt as context block.
    
    Example:
        >>> profile = {"dominant_domains": ["coding"], "preferred_tone": "technical"}
        >>> memories = [{"content": "User prefers concise prompts", "domain": "coding"}]
        >>> block = build_context_block(profile, memories, 23, [2.1, 2.8, 3.2, 3.6, 4.1])
        >>> print(block[:100])
        "## USER CONTEXT — READ BEFORE RESPONDING\n\nSESSION: Power user (23 sessions)..."
    """
    try:
        lines = ["## USER CONTEXT — READ BEFORE RESPONDING\n"]
        
        # Session experience level
        lines.append(format_session_level(session_count))
        
        # Domain profile
        lines.append(format_domains(user_profile.get("dominant_domains", [])))
        
        # Tone preference
        lines.append(format_tone_preference(user_profile.get("preferred_tone")))
        
        # Quality trajectory
        if recent_quality_trend:
            lines.append(format_quality_trend(recent_quality_trend))
        
        # Relevant memories
        if langmem_memories:
            lines.append(format_memories(langmem_memories[:4]))
        
        lines.append("\n--- END USER CONTEXT ---\n")
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"[context_builder] failed: {e}")
        return "## USER CONTEXT — Error loading context\n"


def format_session_level(session_count: int) -> str:
    """
    Format session experience level message.
    
    Args:
        session_count: Total number of user sessions
        
    Returns:
        Formatted session level string
        
    Example:
        >>> format_session_level(0)
        'SESSION: First time user. Be a bit more welcoming.'
        >>> format_session_level(50)
        'SESSION: Power user (50 sessions). Treat as peer.'
    """
    if session_count == 0:
        return "SESSION: First time user. Be a bit more welcoming."
    elif session_count < 5:
        return f"SESSION: Early user ({session_count} sessions). Still building familiarity."
    elif session_count < 20:
        return f"SESSION: Regular user ({session_count} sessions). They know how this works."
    else:
        return f"SESSION: Power user ({session_count} sessions). Treat as peer."


def format_domains(domains: List[str]) -> str:
    """
    Format domain expertise message.
    
    Args:
        domains: List of domain names from user profile
        
    Returns:
        Formatted domain expertise string
        
    Example:
        >>> format_domains(["coding", "marketing"])
        'DOMAINS: Strong in coding, marketing. Adjust depth accordingly.'
        >>> format_domains([])
        'DOMAINS: No domain history yet. Adapt as you learn from this session.'
    """
    if domains:
        return f"DOMAINS: Strong in {', '.join(domains[:3])}. Adjust depth accordingly."
    return "DOMAINS: No domain history yet. Adapt as you learn from this session."


def format_tone_preference(tone: Optional[str]) -> str:
    """
    Format tone preference message.
    
    Args:
        tone: User's preferred tone from profile
        
    Returns:
        Formatted tone preference string or empty string
        
    Example:
        >>> format_tone_preference("technical")
        'TONE PREFERENCE: User responds well to technical tone.'
        >>> format_tone_preference(None)
        ''
    """
    if tone:
        return f"TONE PREFERENCE: User responds well to {tone} tone."
    return ""


def format_quality_trend(trend: List[float]) -> str:
    """
    Format quality trend message.
    
    Args:
        trend: List of quality scores (1-5 scale)
        
    Returns:
        Formatted quality trend string
        
    Example:
        >>> format_quality_trend([2.1, 2.8, 3.2, 3.6, 4.1])
        'QUALITY TREND: Improving — avg 3.2/5.'
        >>> format_quality_trend([4.0, 3.8, 3.5])
        'QUALITY TREND: Stable — avg 3.8/5.'
    """
    if len(trend) >= 3:
        direction = "improving" if trend[-1] > trend[0] else "stable"
        avg = sum(trend) / len(trend)
        return f"QUALITY TREND: {direction} — avg {avg:.1f}/5."
    return ""


def format_memories(memories: List[Dict[str, Any]]) -> str:
    """
    Format LangMem memories for context.
    
    Args:
        memories: List of memory dicts from LangMem semantic search
        
    Returns:
        Formatted memories string
        
    Example:
        >>> memories = [
        ...     {"content": "User prefers concise prompts", "domain": "coding"},
        ...     {"content": "User likes technical examples", "domain": "coding"}
        ... ]
        >>> print(format_memories(memories))
        "RELEVANT MEMORIES FROM PAST SESSIONS:
          [coding] User prefers concise prompts
          [coding] User likes technical examples"
    """
    lines = ["\nRELEVANT MEMORIES FROM PAST SESSIONS:"]
    for mem in memories:
        domain = mem.get("domain", "general")
        content = mem.get("content", "")
        lines.append(f"  [{domain}] {content}")
    return "\n".join(lines)

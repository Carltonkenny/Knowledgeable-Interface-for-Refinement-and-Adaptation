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
    7. format_user_facts() — Verified facts formatting (v2.5)
    8. format_session_context() — Session context formatting (v2.5)

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
    - Forward-compatible: v2.5 fields ready
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def build_context_block(
    user_profile: Dict[str, Any],
    langmem_memories: List[Dict[str, Any]],
    session_count: int,
    recent_quality_trend: Optional[List[float]] = None,
    # v2.5 — Fact extractor / self-learning system
    user_facts: Optional[List[Dict[str, Any]]] = None,
    session_level_context: Optional[str] = None,
) -> str:
    """
    Build dynamic context block injected into every Kira/prompt engineer prompt.

    This is the memory injection point. All user profile data and LangMem
    memories are formatted here and prepended to the orchestrator prompt.

    RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
    - Forward-compatible: v2.5 fields ready

    Args:
        user_profile: Dict from user_profiles table. Keys: dominant_domains,
                      preferred_tone, clarification_patterns, prompt_quality_score.
        langmem_memories: List of dicts from LangMem semantic search.
                          Each has: content, domain, quality_score, created_at.
        session_count: Total sessions this user has had.
        recent_quality_trend: Optional list of last 5 quality scores (float 1-5).
                               Used to detect improving/declining trajectory.
        user_facts: Optional verified facts from fact_extractor.py (v2.5).
                    Format: [{fact, confidence, source, verified_at}]
        session_level_context: Optional project context for current session (v2.5).
                               Short-term context that doesn't persist.

    Returns:
        Formatted string to prepend to system prompt as context block.

    Example:
        >>> profile = {"dominant_domains": ["coding"], "preferred_tone": "technical"}
        >>> memories = [{"content": "User prefers concise prompts", "domain": "coding"}]
        >>> block = build_context_block(profile, memories, 23, [2.1, 2.8, 3.2, 3.6, 4.1])
        >>> print(block[:100])
        "## USER CONTEXT — READ BEFORE RESPONDING\n\nSESSION: Power user (23 sessions)..."
        
        >>> # v2.5: With user facts
        >>> facts = [{"fact": "Prefers FastAPI", "confidence": 0.95}]
        >>> block = build_context_block(profile, memories, 23, user_facts=facts)
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

        # v2.5: Verified user facts (Character.ai pattern)
        if user_facts:
            lines.append(format_user_facts(user_facts))

        # v2.5: Session-level project context
        if session_level_context:
            lines.append(format_session_context(session_level_context))

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


# ═══ V2.5 FORMATTERS — FACTS + SESSION CONTEXT ═══════════════════════════════

def format_user_facts(facts: List[Dict[str, Any]]) -> str:
    """
    Format verified user facts (Character.ai pattern).

    These are facts verified across multiple sessions, injected into
    every session for consistent personalization.

    v2.5: Called by build_context_block() when fact_extractor.py runs.

    Args:
        facts: List of verified fact dicts
               Format: [{fact, confidence, source, verified_at}]

    Returns:
        Formatted facts string

    Example:
        >>> facts = [
        ...     {"fact": "Prefers FastAPI for backend", "confidence": 0.95},
        ...     {"fact": "Uses TypeScript over Python", "confidence": 0.87}
        ... ]
        >>> print(format_user_facts(facts))
        "VERIFIED USER FACTS:
          • Prefers FastAPI for backend (95% confidence)
          • Uses TypeScript over Python (87% confidence)"
    """
    lines = ["\nVERIFIED USER FACTS:"]
    for fact in facts:
        fact_text = fact.get("fact", "")
        confidence = fact.get("confidence", 0.0)
        confidence_str = f" ({int(confidence * 100)}% confidence)" if confidence > 0 else ""
        lines.append(f"  • {fact_text}{confidence_str}")
    return "\n".join(lines)


def format_session_context(context: str) -> str:
    """
    Format session-level project context.

    Temporary context for current session only (doesn't persist to LangMem).
    Used for active project context that's relevant now but not long-term.

    v2.5: Called by build_context_block() when session has project context.

    Args:
        context: Session-level project context string

    Returns:
        Formatted session context string

    Example:
        >>> context = "Refactoring authentication module to use JWT"
        >>> print(format_session_context(context))
        "CURRENT SESSION CONTEXT:
          Refactoring authentication module to use JWT"
    """
    return f"\nCURRENT SESSION CONTEXT:\n  {context}"

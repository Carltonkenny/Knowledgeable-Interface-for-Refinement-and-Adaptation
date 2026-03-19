# agents/orchestration/personality.py
"""
Kira Personality Adaptation Logic.

CONTAINS:
    1. PersonalityAdaptation dataclass — Type-safe adaptation result
    2. adapt_kira_personality() — Adapt Kira's response personality to user
    3. check_forbidden_phrases() — Validate response doesn't contain forbidden phrases

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Pure functions (testable)

RENAMED (v2.0):
    - adapt_personality() → adapt_kira_personality()
    Reason: Distinguish from analyze_user_personality() in context/adapters.py
    This function adapts KIRA'S output, not analyzes user's input.
"""

from typing import Dict, Any, List
from dataclasses import dataclass

# Import shared constants
from agents.prompts.shared import FORBIDDEN_PHRASES


@dataclass
class PersonalityAdaptation:
    """Type-safe personality adaptation result."""
    detected_user_style: Dict[str, float]
    blended_style: Dict[str, float]
    adaptation_guidance: str
    forbidden_phrases_detected: List[str]


def adapt_kira_personality(
    message: str,
    user_profile: Dict[str, Any],
    response_text: str
) -> PersonalityAdaptation:
    """
    Adapt Kira's personality/response style to user.

    This function adjusts HOW KIRA RESPONDS based on:
    - User's communication style (formality, technical depth)
    - User's profile baseline (preferred tone, domains)
    - Generated response text (for forbidden phrase checking)

    RULES.md:
    - Kira is direct, warm, slightly opinionated
    - Never says: "Certainly", "Great question", etc.
    - Adapts expression based on user style

    Args:
        message: User's message
        user_profile: User profile from Supabase
        response_text: Generated response text to validate

    Returns:
        PersonalityAdaptation dataclass with:
        - detected_user_style: formality/technical scores
        - blended_style: 70% profile + 30% message blend
        - adaptation_guidance: How Kira should express response
        - forbidden_phrases_detected: Any violations found

    Example:
        >>> result = adapt_kira_personality(
        ...     message="hey can u help me with some code",
        ...     user_profile={"preferred_tone": "direct", "dominant_domains": ["coding"]},
        ...     response_text="Sure! I'd be happy to help."
        ... )
        >>> result.adaptation_guidance
        "Use contractions, friendly tone; Use precise terminology"
        >>> result.forbidden_phrases_detected
        ["I'd be happy to"]
    """
    # Detect user style
    detected = _detect_user_style(message)
    
    # Blend with profile
    blended = _blend_with_profile(detected, user_profile)
    
    # Generate guidance
    guidance = _get_adaptation_guidance(blended)
    
    # Check forbidden phrases
    forbidden = check_forbidden_phrases(response_text)
    
    return PersonalityAdaptation(
        detected_user_style=detected,
        blended_style=blended,
        adaptation_guidance=guidance,
        forbidden_phrases_detected=forbidden
    )


def _detect_user_style(message: str) -> Dict[str, float]:
    """Detect user's communication style."""
    message_lower = message.lower()
    
    # Formality detection
    casual_signals = ["u ", "pls", "thx", "gonna", "wanna", "hey", "lol"]
    formal_signals = ["please", "thank you", "could you", "kindly", "regards"]
    
    casual_count = sum(1 for s in casual_signals if s in message_lower)
    formal_count = sum(1 for s in formal_signals if s in message_lower)
    
    total = casual_count + formal_count
    formality = formal_count / total if total > 0 else 0.5
    
    # Technical detection
    tech_signals = ["api", "function", "async", "database", "query", "code"]
    general_signals = ["thing", "stuff", "something", "maybe"]
    
    tech_count = sum(1 for s in tech_signals if s in message_lower)
    general_count = sum(1 for s in general_signals if s in message_lower)
    
    total_tech = tech_count + general_count
    technical = tech_count / total_tech if total_tech > 0 else 0.5
    
    return {
        "formality": round(formality, 2),
        "technical": round(technical, 2)
    }


def _blend_with_profile(
    detected: Dict[str, float],
    user_profile: Dict[str, Any]
) -> Dict[str, float]:
    """Blend detected style with profile baseline."""
    # Profile baseline
    profile_tone = user_profile.get("preferred_tone", "direct")
    profile_domains = user_profile.get("dominant_domains", [])
    
    profile_formality = 0.7 if profile_tone == "formal" else 0.5
    profile_technical = 0.8 if any(d in profile_domains for d in ["coding", "technical"]) else 0.5
    
    # Blend: 70% profile, 30% message
    blended_formality = (0.7 * profile_formality) + (0.3 * detected["formality"])
    blended_technical = (0.7 * profile_technical) + (0.3 * detected["technical"])
    
    return {
        "formality": round(blended_formality, 2),
        "technical": round(blended_technical, 2)
    }


def _get_adaptation_guidance(blended: Dict[str, float]) -> str:
    """Get response guidance from blended style."""
    formality = blended["formality"]
    technical = blended["technical"]
    
    parts = []
    
    if formality < 0.4:
        parts.append("Use contractions, friendly tone")
    elif formality > 0.7:
        parts.append("Use professional register")
    else:
        parts.append("Balanced tone")
    
    if technical > 0.7:
        parts.append("Use precise terminology")
    elif technical < 0.4:
        parts.append("Avoid jargon")
    else:
        parts.append("Mix technical and accessible")
    
    return "; ".join(parts)


def check_forbidden_phrases(text: str) -> List[str]:
    """
    Check if response contains forbidden phrases.
    
    Args:
        text: Response text to check
        
    Returns:
        List of forbidden phrases found (empty if none)
        
    Example:
        >>> check_forbidden_phrases("Certainly! I'd be happy to help.")
        ['Certainly', "I'd be happy to"]
    """
    text_lower = text.lower()
    found = []
    
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in text_lower:
            found.append(phrase)

    return found


# ═══ BACKWARD COMPATIBILITY ═══════════════════════════════════
# (No deprecated functions - clean codebase)

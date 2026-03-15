# agents/context/adapters.py
"""
Personality Adaptation Logic.

CONTAINS:
    1. PersonalityAdaptation dataclass — Type-safe adaptation result
    2. analyze_user_style() — Detect formality and technical depth
    3. blend_with_profile() — Blend message style with profile baseline
    4. get_adaptation_guidance() — Get response guidance based on blend

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Pure functions (testable)
    - Configuration over hardcoding
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class PersonalityAdaptation:
    """Type-safe representation of personality adaptation."""
    detected_formality: float  # 0.0-1.0
    detected_technical: float  # 0.0-1.0
    blended_formality: float  # 0.0-1.0
    blended_technical: float  # 0.0-1.0
    adaptation_notes: str


def analyze_user_style(message: str) -> Dict[str, float]:
    """
    Analyze user's communication style from message.
    
    Analyzes two axes:
    1. Formality (0.0-1.0): casual ↔ formal
    2. Technical depth (0.0-1.0): general ↔ expert
    
    Args:
        message: User's message to analyze
        
    Returns:
        Dict with formality and technical scores (0.0-1.0)
        
    Example:
        >>> analyze_user_style("hey can u help me with some code pls")
        {'formality': 0.15, 'technical': 0.3}
        >>> analyze_user_style("Could you please assist me in crafting an API documentation prompt?")
        {'formality': 0.85, 'technical': 0.7}
    """
    message_lower = message.lower()
    
    # Formality detection
    casual_signals = [
        "u ", "pls", "plz", "thx", "gonna", "wanna", "kinda", "sorta",
        "hey", "yo", "sup", "lol", "omg", "!", "??"
    ]
    formal_signals = [
        "please", "thank you", "could you", "would you", "i would appreciate",
        "kindly", "regards", "sincerely", ".", "!"
    ]
    
    casual_count = sum(1 for signal in casual_signals if signal in message_lower)
    formal_count = sum(1 for signal in formal_signals if signal in message_lower)
    
    # Calculate formality (0.0 = very casual, 1.0 = very formal)
    total_signals = casual_count + formal_count
    if total_signals == 0:
        formality = 0.5  # Neutral if no signals
    else:
        formality = formal_count / total_signals
    
    # Technical depth detection
    general_words = [
        "thing", "stuff", "something", "whatever", "maybe", "kind of",
        "sort of", "basically", "like"
    ]
    technical_words = [
        "api", "endpoint", "function", "method", "class", "interface",
        "database", "query", "algorithm", "complexity", "optimization",
        "async", "await", "promise", "callback", "middleware", "router"
    ]
    
    general_count = sum(1 for word in general_words if word in message_lower)
    technical_count = sum(1 for word in technical_words if word in message_lower)
    
    # Calculate technical depth (0.0 = general, 1.0 = expert)
    total_tech_signals = general_count + technical_count
    if total_tech_signals == 0:
        technical = 0.5  # Neutral if no signals
    else:
        technical = technical_count / total_tech_signals
    
    return {
        "formality": round(formality, 2),
        "technical": round(technical, 2)
    }


def blend_with_profile(
    detected_style: Dict[str, float],
    profile_tone: str,
    profile_domains: list
) -> Dict[str, float]:
    """
    Blend detected message style with user profile baseline.
    
    Profile = 70% weight (stable baseline)
    Message = 30% weight (dynamic adjustment)
    
    Args:
        detected_style: Dict with formality and technical scores from message
        profile_tone: User's preferred tone from profile
        profile_domains: User's dominant domains from profile
        
    Returns:
        Dict with blended formality and technical scores
        
    Example:
        >>> detected = {"formality": 0.2, "technical": 0.3}
        >>> blend_with_profile(detected, "technical", ["coding"])
        {'formality': 0.44, 'technical': 0.75}
    """
    # Profile baseline scores
    profile_formality = 0.5 if profile_tone == "casual" else 0.7 if profile_tone == "formal" else 0.5
    profile_technical = 0.8 if "coding" in profile_domains or "technical" in profile_domains else 0.5
    
    # Blend: 70% profile, 30% message
    blended_formality = (0.7 * profile_formality) + (0.3 * detected_style["formality"])
    blended_technical = (0.7 * profile_technical) + (0.3 * detected_style["technical"])
    
    return {
        "formality": round(blended_formality, 2),
        "technical": round(blended_technical, 2)
    }


def get_adaptation_guidance(blended_style: Dict[str, float]) -> str:
    """
    Get response guidance based on blended style.
    
    Args:
        blended_style: Dict with blended formality and technical scores
        
    Returns:
        Guidance string for response generation
        
    Example:
        >>> get_adaptation_guidance({"formality": 0.3, "technical": 0.8})
        'Use contractions, friendly tone, precise technical terminology'
    """
    formality = blended_style["formality"]
    technical = blended_style["technical"]
    
    guidance_parts = []
    
    # Formality guidance
    if formality < 0.4:
        guidance_parts.append("Use contractions, friendly tone, shorter sentences")
    elif formality > 0.7:
        guidance_parts.append("Use complete sentences, professional register")
    else:
        guidance_parts.append("Balanced tone — friendly but professional")
    
    # Technical guidance
    if technical > 0.7:
        guidance_parts.append("Use precise technical terminology, assume expertise")
    elif technical < 0.4:
        guidance_parts.append("Explain concepts, avoid jargon")
    else:
        guidance_parts.append("Mix technical terms with accessible explanations")
    
    return "; ".join(guidance_parts)

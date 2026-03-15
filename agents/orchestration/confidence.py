# agents/orchestration/confidence.py
"""
Confidence Scoring Logic.

CONTAINS:
    1. ConfidenceScore dataclass — Type-safe confidence result
    2. calculate_confidence() — Main confidence calculation
    3. get_confidence_guidance() — Behavior guidance based on confidence

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Pure functions (testable)
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ConfidenceScore:
    """Type-safe confidence score."""
    score: float  # 0.0-1.0
    level: str  # "high" | "medium" | "low" | "very_low"
    clarification_recommended: bool
    reason: str


def calculate_confidence(
    message: str,
    history: List[Dict[str, Any]],
    user_profile: Dict[str, Any]
) -> ConfidenceScore:
    """
    Calculate confidence score for user request.
    
    Args:
        message: User's message
        history: Conversation history
        user_profile: User profile
        
    Returns:
        ConfidenceScore dataclass
        
    Confidence Guidelines:
        - Request is specific and actionable → 0.8-1.0
        - Request has context from history → +0.1-0.2
        - Request is vague ("write something") → 0.3-0.5
        - Request lacks domain/context AND is vague → 0.2-0.4
        - Request is extremely vague (<10 chars) → 0.1-0.3
    """
    score = 0.5  # Start neutral
    
    reasons = []
    
    # Specific and actionable
    if len(message.split()) > 10:
        score += 0.2
        reasons.append("specific and actionable")
    
    # Has context from history
    if len(history) > 0:
        score += 0.15
        reasons.append("has conversation context")
    
    # Has domain signals
    domain_signals = ["python", "api", "marketing", "email", "code"]
    if any(signal in message.lower() for signal in domain_signals):
        score += 0.15
        reasons.append("domain identified")
    
    # Has constraints
    constraint_signals = ["word", "tone", "length", "format", "audience"]
    if any(signal in message.lower() for signal in constraint_signals):
        score += 0.1
        reasons.append("constraints specified")
    
    # Vague words penalty
    vague_words = ["something", "thing", "stuff", "whatever", "anything"]
    if any(word in message.lower() for word in vague_words):
        score -= 0.2
        reasons.append("vague language detected")
    
    # Very short penalty
    if len(message.strip()) < 10:
        score -= 0.3
        reasons.append("very short message")
    
    # Clamp to 0.0-1.0
    score = max(0.0, min(1.0, score))
    
    # Determine level
    if score >= 0.8:
        level = "high"
        clarification = False
    elif score >= 0.5:
        level = "medium"
        clarification = False
    elif score >= 0.3:
        level = "low"
        clarification = True
    else:
        level = "very_low"
        clarification = True
    
    return ConfidenceScore(
        score=round(score, 2),
        level=level,
        clarification_recommended=clarification,
        reason="; ".join(reasons) if reasons else "neutral"
    )


def get_confidence_guidance(confidence: ConfidenceScore) -> str:
    """
    Get behavior guidance based on confidence level.
    
    Args:
        confidence: ConfidenceScore from calculate_confidence()
        
    Returns:
        Guidance string for response generation
    """
    if confidence.level == "high":
        return "Proceed directly without questions"
    elif confidence.level == "medium":
        return "Proceed, but add one clarifying note if relevant"
    elif confidence.level == "low":
        return "Add one clarifying question in response"
    else:  # very_low
        return "Cannot proceed without clarification — ask specific question"

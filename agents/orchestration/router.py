# agents/orchestration/router.py
"""
Routing Decision Logic.

CONTAINS:
    1. RoutingDecision dataclass — Type-safe routing result
    2. RouteType enum — Type-safe route values
    3. RoutingConfig — Configurable routing thresholds
    4. decide_route() — Main routing logic
    5. detect_modification_phrases() — FOLLOWUP detection
    6. calculate_ambiguity_score() — CLARIFICATION detection

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Pure functions (testable)
    - Configuration over hardcoding
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class RouteType(str, Enum):
    """Type-safe routing decisions."""
    CONVERSATION = "CONVERSATION"
    SWARM = "SWARM"
    FOLLOWUP = "FOLLOWUP"
    CLARIFICATION = "CLARIFICATION"


@dataclass
class RoutingDecision:
    """Type-safe routing decision result."""
    route: RouteType
    proceed_with_swarm: bool
    agents_to_run: List[str]
    clarification_needed: bool
    clarification_question: Optional[str]
    skip_reasons: Dict[str, Optional[str]]
    tone_used: str
    profile_applied: bool
    ambiguity_score: float


class RoutingConfig:
    """Configurable routing thresholds."""

    MESSAGE_LENGTH_CONVERSATION: int = 10
    AMBIGUITY_THRESHOLD: float = 0.6
    
    MODIFICATION_PHRASES: List[str] = None
    
    def __init__(self):
        self.MODIFICATION_PHRASES = [
            "make it", "change it", "change the", "adjust", "modify",
            "add", "remove", "shorter", "longer", "better", "different",
            "more detail", "less formal", "simplify", "expand", "redo",
            "try again", "different version", "rewrite", "tweak"
        ]


def decide_route(
    message: str,
    history: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    pending_clarification: bool,
    config: RoutingConfig = None
) -> RoutingDecision:
    """
    Make routing decision based on message and context.

    RULES.md Routing Logic (in order):
    1. message.length < 10 → CONVERSATION
    2. pending_clarification → SWARM (direct)
    3. Modification phrases → FOLLOWUP
    4. ambiguity_score > 0.6 → CLARIFICATION
    5. Otherwise → SWARM
    
    Args:
        message: User's message
        history: Conversation history
        user_profile: User profile from Supabase
        pending_clarification: Whether waiting for clarification answer
        config: Optional RoutingConfig instance
        
    Returns:
        RoutingDecision dataclass with routing details
        
    Example:
        >>> decision = decide_route("hi", [], {}, False)
        >>> decision.route
        RouteType.CONVERSATION
    """
    if config is None:
        config = RoutingConfig()
    
    # Rule 1: Short message
    if len(message.strip()) < config.MESSAGE_LENGTH_CONVERSATION:
        return _route_conversation()
    
    # Rule 2: Pending clarification
    if pending_clarification:
        return _route_swarm_direct()
    
    # Rule 3: Modification phrases
    if detect_modification_phrases(message, config):
        return _route_followup()
    
    # Rule 4: Ambiguity
    ambiguity = calculate_ambiguity_score(message, history)
    if ambiguity > config.AMBIGUITY_THRESHOLD:
        return _route_clarification(ambiguity)
    
    # Rule 5: Default to swarm
    return _route_swarm(message, history, user_profile)


def _route_conversation() -> RoutingDecision:
    """Route to CONVERSATION handler."""
    return RoutingDecision(
        route=RouteType.CONVERSATION,
        proceed_with_swarm=False,
        agents_to_run=[],
        clarification_needed=False,
        clarification_question=None,
        skip_reasons={"context": None, "domain": None, "intent": None},
        tone_used="casual",
        profile_applied=False,
        ambiguity_score=0.1
    )


def _route_swarm_direct() -> RoutingDecision:
    """Route to SWARM (direct, after clarification)."""
    return RoutingDecision(
        route=RouteType.SWARM,
        proceed_with_swarm=True,
        agents_to_run=["intent", "context", "domain"],
        clarification_needed=False,
        clarification_question=None,
        skip_reasons={"context": None, "domain": None, "intent": None},
        tone_used="direct",
        profile_applied=True,
        ambiguity_score=0.3
    )


def _route_followup() -> RoutingDecision:
    """Route to FOLLOWUP handler."""
    return RoutingDecision(
        route=RouteType.FOLLOWUP,
        proceed_with_swarm=False,
        agents_to_run=[],
        clarification_needed=False,
        clarification_question=None,
        skip_reasons={"context": None, "domain": None, "intent": None},
        tone_used="direct",
        profile_applied=False,
        ambiguity_score=0.2
    )


def _route_clarification(ambiguity: float) -> RoutingDecision:
    """Route to CLARIFICATION."""
    return RoutingDecision(
        route=RouteType.CLARIFICATION,
        proceed_with_swarm=False,
        agents_to_run=[],
        clarification_needed=True,
        clarification_question="Could you clarify what you're looking for?",
        skip_reasons={"context": None, "domain": None, "intent": None},
        tone_used="casual",
        profile_applied=False,
        ambiguity_score=ambiguity
    )


def _route_swarm(
    message: str,
    history: List[Dict[str, Any]],
    user_profile: Dict[str, Any]
) -> RoutingDecision:
    """Route to SWARM with agent selection."""
    agents_to_run = ["intent"]  # Always run intent
    
    # Skip context if no history
    if len(history) == 0:
        context_skip = "no session history"
    else:
        agents_to_run.append("context")
        context_skip = None
    
    # Skip domain if profile confidence > 0.85
    domain_confidence = user_profile.get("domain_confidence", 0.0)
    if domain_confidence > 0.85:
        domain_skip = f"profile confidence {domain_confidence:.2f} > 0.85"
    else:
        agents_to_run.append("domain")
        domain_skip = None
    
    return RoutingDecision(
        route=RouteType.SWARM,
        proceed_with_swarm=True,
        agents_to_run=agents_to_run,
        clarification_needed=False,
        clarification_question=None,
        skip_reasons={"context": context_skip, "domain": domain_skip, "intent": None},
        tone_used=user_profile.get("preferred_tone", "direct"),
        profile_applied=bool(user_profile),
        ambiguity_score=0.3
    )


def detect_modification_phrases(message: str, config: RoutingConfig = None) -> bool:
    """
    Check if message contains modification phrases.
    
    Used for FOLLOWUP detection.
    
    Args:
        message: User's message
        config: Optional RoutingConfig instance
        
    Returns:
        True if modification detected, False otherwise
        
    Example:
        >>> detect_modification_phrases("make it longer")
        True
        >>> detect_modification_phrases("write a story")
        False
    """
    if config is None:
        config = RoutingConfig()
    
    message_lower = message.lower()
    return any(phrase in message_lower for phrase in config.MODIFICATION_PHRASES)


def calculate_ambiguity_score(
    message: str,
    history: List[Dict[str, Any]]
) -> float:
    """
    Simple heuristic for ambiguity detection.
    
    Returns 0.0-1.0 (higher = more ambiguous).
    
    Args:
        message: User's message
        history: Conversation history
        
    Returns:
        Ambiguity score 0.0-1.0
        
    Scoring:
        - Short messages (<20 chars): +0.3
        - Questions (contains "?"): +0.2
        - Vague words: +0.3
        - No context (first message): +0.2
        
    Example:
        >>> calculate_ambiguity_score("write something", [])
        0.8
    """
    score = 0.0
    
    # Short messages are more ambiguous
    if len(message.strip()) < 20:
        score += 0.3
    
    # Questions are often ambiguous
    if "?" in message:
        score += 0.2
    
    # Vague words
    vague_words = ["something", "thing", "stuff", "whatever", "maybe", "perhaps", "anything"]
    if any(word in message.lower() for word in vague_words):
        score += 0.3
    
    # No context (first message)
    if len(history) == 0:
        score += 0.2
    
    return min(score, 1.0)

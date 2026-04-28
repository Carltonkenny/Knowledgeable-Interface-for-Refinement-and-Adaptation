# agents/orchestration/router.py
# ─────────────────────────────────────────────
# Agent Routing Decision Logic
#
# RULES.md Compliance:
# - Type hints mandatory
# - Docstrings complete
# - Error handling comprehensive
# - Logging contextual
# - Pure functions (testable)
# - Configuration over hardcoding
# ─────────────────────────────────────────────

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ═══ ROUTE TYPES ═════════════════════════════

class RouteType(str, Enum):
    """Type-safe routing options for Kira orchestrator."""
    CONVERSATION = "CONVERSATION"   # Greeting / off-topic → short reply
    SWARM        = "SWARM"          # Full 4-agent prompt engineering
    FOLLOWUP     = "FOLLOWUP"       # Modify previous result
    CLARIFICATION = "CLARIFICATION" # Ask user to clarify before swarm


# ═══ CONFIG ══════════════════════════════════

@dataclass
class RoutingConfig:
    """
    Configurable thresholds for routing decisions.

    Attributes:
        min_message_length: Below this (chars), treat as conversation.
        ambiguity_threshold: Above this score, request clarification.
        modification_phrases: Phrases that signal a FOLLOWUP request.
    """
    min_message_length: int = 10
    ambiguity_threshold: float = 0.65
    modification_phrases: List[str] = field(default_factory=lambda: [
        "make it", "change it", "shorter", "longer", "more formal",
        "less formal", "simplify", "add more", "remove", "rewrite",
        "different tone", "make more", "make less", "adjust",
        "revise", "update", "modify", "tweak",
    ])


# ═══ ROUTING DECISION ════════════════════════

@dataclass
class RoutingDecision:
    """
    Type-safe result of a routing decision.

    Attributes:
        route: The chosen RouteType.
        confidence: Confidence score 0.0–1.0.
        reason: Human-readable explanation for logging/debugging.
        clarification_question: Set when route == CLARIFICATION.
        agents_to_run: Subset of agents if SWARM (all = default).
    """
    route: RouteType
    confidence: float = 1.0
    reason: str = ""
    clarification_question: Optional[str] = None
    agents_to_run: List[str] = field(default_factory=lambda: ["intent", "context", "domain", "prompt_engineer"])


# ═══ DETECTION UTILITIES ═════════════════════

def detect_modification_phrases(
    message: str,
    config: Optional[RoutingConfig] = None,
) -> bool:
    """
    Detect if a message is a follow-up modification request.

    Args:
        message: User's raw message.
        config: Optional routing config with custom phrase list.

    Returns:
        True if message contains modification signals.

    Example:
        >>> detect_modification_phrases("make it shorter")
        True
        >>> detect_modification_phrases("write me a blog post")
        False
    """
    cfg = config or RoutingConfig()
    msg_lower = message.lower().strip()
    return any(phrase in msg_lower for phrase in cfg.modification_phrases)


def calculate_ambiguity_score(
    message: str,
    intent_analysis: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Calculate ambiguity score for a user message (0.0 = clear, 1.0 = very ambiguous).

    Uses heuristics: message length, question words, vague terms.
    If intent_analysis is provided, uses its ambiguity_score directly.

    Args:
        message: User's raw message.
        intent_analysis: Optional output from intent agent.

    Returns:
        Float ambiguity score 0.0–1.0.

    Example:
        >>> calculate_ambiguity_score("write something")
        0.7
        >>> calculate_ambiguity_score("Write a Python decorator that adds retry logic with exponential backoff")
        0.1
    """
    # If intent agent already computed ambiguity, trust it
    if intent_analysis and "ambiguity_score" in intent_analysis:
        score = float(intent_analysis["ambiguity_score"])
        return max(0.0, min(1.0, score))

    # Heuristic fallback
    msg = message.strip()
    score = 0.0

    # Very short messages are more ambiguous
    if len(msg) < 15:
        score += 0.5
    elif len(msg) < 30:
        score += 0.25

    # Vague words signal ambiguity
    vague_words = ["something", "stuff", "things", "help", "write", "make", "do", "create"]
    word_count = sum(1 for w in vague_words if w in msg.lower())
    score += min(0.4, word_count * 0.15)

    # No subject = more ambiguous
    if len(msg.split()) < 4:
        score += 0.2

    return max(0.0, min(1.0, score))


# ═══ MAIN ROUTING FUNCTION ═══════════════════

def decide_route(
    message: str,
    conversation_history: List[Dict[str, Any]],
    orchestrator_decision: Optional[Dict[str, Any]] = None,
    config: Optional[RoutingConfig] = None,
) -> RoutingDecision:
    """
    Main routing decision: map user message + context to a RouteType.

    Decision tree (in priority order):
    1. Very brief input (< min_message_length chars)  → CONVERSATION
    2. Pending clarification in orchestrator           → SWARM (resolve it)
    3. Modification phrases detected + has history     → FOLLOWUP
    4. High ambiguity score (> threshold)              → CLARIFICATION
    5. Default                                          → SWARM

    Args:
        message: User's raw message.
        conversation_history: Last N conversation turns.
        orchestrator_decision: Optional pre-computed orchestrator dict.
                               If present, its 'route' key is trusted directly.
        config: Optional routing config with custom thresholds.

    Returns:
        RoutingDecision with route, confidence, and reason.

    Example:
        >>> decide_route("hi", [])
        RoutingDecision(route=<RouteType.CONVERSATION: 'CONVERSATION'>, ...)
        >>> decide_route("make it shorter", [{"role": "assistant", ...}])
        RoutingDecision(route=<RouteType.FOLLOWUP: 'FOLLOWUP'>, ...)
    """
    cfg = config or RoutingConfig()

    # Trust orchestrator if it already made a decision
    if orchestrator_decision:
        raw_route = orchestrator_decision.get("route", "")
        if raw_route in RouteType.__members__:
            route = RouteType(raw_route)
            logger.debug(f"[router] trusting orchestrator route: {route}")
            return RoutingDecision(
                route=route,
                confidence=orchestrator_decision.get("confidence", 0.9),
                reason="Orchestrator decision trusted",
                clarification_question=orchestrator_decision.get("clarification_question"),
                agents_to_run=orchestrator_decision.get("agents_to_run", ["intent", "context", "domain", "prompt_engineer"]),
            )

    msg_stripped = message.strip()

    # 1. Very brief → CONVERSATION
    if len(msg_stripped) < cfg.min_message_length:
        logger.debug(f"[router] message too short ({len(msg_stripped)} chars) → CONVERSATION")
        return RoutingDecision(
            route=RouteType.CONVERSATION,
            confidence=0.95,
            reason=f"Message too short ({len(msg_stripped)} chars)",
        )

    # 2. Modification phrases + has history → FOLLOWUP
    has_history = bool(conversation_history)
    if has_history and detect_modification_phrases(msg_stripped, cfg):
        logger.debug(f"[router] modification phrase detected with history → FOLLOWUP")
        return RoutingDecision(
            route=RouteType.FOLLOWUP,
            confidence=0.85,
            reason="Modification phrase detected with conversation history",
            agents_to_run=["intent", "prompt_engineer"],  # Skip context/domain on followup
        )

    # 3. High ambiguity → CLARIFICATION
    ambiguity = calculate_ambiguity_score(msg_stripped)
    if ambiguity > cfg.ambiguity_threshold:
        logger.debug(f"[router] high ambiguity ({ambiguity:.2f}) → CLARIFICATION")
        return RoutingDecision(
            route=RouteType.CLARIFICATION,
            confidence=0.8,
            reason=f"Ambiguity score {ambiguity:.2f} > threshold {cfg.ambiguity_threshold}",
        )

    # 4. Default → SWARM
    logger.debug(f"[router] default → SWARM (ambiguity={ambiguity:.2f})")
    return RoutingDecision(
        route=RouteType.SWARM,
        confidence=0.9,
        reason="Standard prompt engineering request",
    )


__all__ = [
    "decide_route",
    "RoutingDecision",
    "RouteType",
    "RoutingConfig",
    "detect_modification_phrases",
    "calculate_ambiguity_score",
]
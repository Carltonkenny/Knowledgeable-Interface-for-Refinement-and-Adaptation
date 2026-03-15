"""
Orchestration Logic.

EXPORTS:
    - decide_route() — Main routing decision logic
    - RoutingDecision dataclass — Type-safe routing result
    - RouteType enum — Type-safe route values
    - detect_modification_phrases() — FOLLOWUP detection
    - calculate_ambiguity_score() — CLARIFICATION detection

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Pure functions (testable)
    - Configuration over hardcoding
"""

from .router import (
    decide_route,
    RoutingDecision,
    RouteType,
    RoutingConfig,
    detect_modification_phrases,
    calculate_ambiguity_score,
)

__all__ = [
    "decide_route",
    "RoutingDecision",
    "RouteType",
    "RoutingConfig",
    "detect_modification_phrases",
    "calculate_ambiguity_score",
]

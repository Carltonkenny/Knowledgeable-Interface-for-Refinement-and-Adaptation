"""
PromptForge Agent System — Modular Architecture (2027 Ready).

VERSION: 2.0.0

ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────┐
    │  agents/                                                     │
    │  ├── prompts/        — System prompts + few-shot examples   │
    │  │   ├── orchestrator.py  — KIRA_ORCHESTRATOR_SYSTEM        │
    │  │   ├── engineer.py        — PROMPT_ENGINEER_SYSTEM        │
    │  │   └── shared.py          — Shared constants              │
    │  ├── context/        — Context building utilities           │
    │  │   ├── builder.py         — build_context_block()         │
    │  │   ├── scorer.py          — score_input_quality()         │
    │  │   └── adapters.py        — Personality adaptation        │
    │  ├── handlers/       — Request handlers                     │
    │  │   ├── conversation.py    — handle_conversation()         │
    │  │   ├── followup.py        — handle_followup()             │
    │  │   ├── swarm.py           — handle_swarm_routing()        │
    │  │   └── unified.py         — kira_unified_handler()        │
    │  ├── orchestration/  — Routing + decision logic             │
    │  │   ├── router.py          — decide_route()                │
    │  │   ├── confidence.py      — calculate_confidence()        │
    │  │   └── personality.py     — adapt_kira_personality()      │
    │  └── utils/          — Shared utilities                     │
    └─────────────────────────────────────────────────────────────┘

RULES.md Compliance:
    - Type hints on all exports
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
    - DRY principles followed
    - Modular architecture (single responsibility)

EXPORTS:
    All public functions and constants from submodules.

Example:
    >>> from agents import (
    ...     kira_unified_handler,
    ...     build_context_block,
    ...     score_input_quality,
    ...     decide_route,
    ... )
    >>> result = kira_unified_handler(message, history, profile)
"""

__version__ = "2.0.0"

# Prompts
from agents.prompts import (
    KIRA_ORCHESTRATOR_SYSTEM,
    ORCHESTRATOR_FEW_SHOT_EXAMPLES,
    ORCHESTRATOR_RESPONSE_SCHEMA,
    PROMPT_ENGINEER_SYSTEM,
    ENGINEER_FEW_SHOT_EXAMPLES,
    ENGINEER_RESPONSE_SCHEMA,
    FORBIDDEN_PHRASES,
    ROUTING_RULES,
    TEMPERATURE,
    MAX_TOKENS,
)

# Context
from agents.context import (
    build_context_block,
    format_session_level,
    format_domains,
    format_tone_preference,
    format_quality_trend,
    format_memories,
)

from agents.context.scorer import (
    score_input_quality,
    QualityScore,
    QualityThresholds,
)

from agents.context.adapters import (
    analyze_user_style,
    blend_with_profile,
    get_adaptation_guidance,
    PersonalityAdaptation,
)

# Handlers
from agents.handlers import (
    handle_conversation,
    handle_followup,
    handle_swarm_routing,
    kira_unified_handler,
)

# Orchestration
from agents.orchestration import (
    decide_route,
    RoutingDecision,
    RouteType,
    RoutingConfig,
    detect_modification_phrases,
    calculate_ambiguity_score,
)

from agents.orchestration.confidence import (
    calculate_confidence,
    ConfidenceScore,
    get_confidence_guidance,
)

from agents.orchestration.personality import (
    adapt_kira_personality,
    check_forbidden_phrases,
    PersonalityAdaptation,
)

# Backward compatibility — re-export old names for existing code
from agents.handlers.unified import fallback_unified_response
from agents.handlers.conversation import CONVERSATION_PROMPT
from agents.handlers.followup import FOLLOWUP_PROMPT

__all__ = [
    # Version
    "__version__",
    
    # Prompts
    "KIRA_ORCHESTRATOR_SYSTEM",
    "ORCHESTRATOR_FEW_SHOT_EXAMPLES",
    "ORCHESTRATOR_RESPONSE_SCHEMA",
    "PROMPT_ENGINEER_SYSTEM",
    "ENGINEER_FEW_SHOT_EXAMPLES",
    "ENGINEER_RESPONSE_SCHEMA",
    "FORBIDDEN_PHRASES",
    "ROUTING_RULES",
    "TEMPERATURE",
    "MAX_TOKENS",
    
    # Context
    "build_context_block",
    "format_session_level",
    "format_domains",
    "format_tone_preference",
    "format_quality_trend",
    "format_memories",
    "score_input_quality",
    "QualityScore",
    "QualityThresholds",
    "analyze_user_style",
    "blend_with_profile",
    "get_adaptation_guidance",
    "PersonalityAdaptation",
    
    # Handlers
    "handle_conversation",
    "handle_followup",
    "handle_swarm_routing",
    "kira_unified_handler",
    "fallback_unified_response",
    "CONVERSATION_PROMPT",
    "FOLLOWUP_PROMPT",
    
    # Orchestration
    "decide_route",
    "RoutingDecision",
    "RouteType",
    "RoutingConfig",
    "detect_modification_phrases",
    "calculate_ambiguity_score",
    "calculate_confidence",
    "ConfidenceScore",
    "get_confidence_guidance",
    "adapt_kira_personality",
    "check_forbidden_phrases",
]

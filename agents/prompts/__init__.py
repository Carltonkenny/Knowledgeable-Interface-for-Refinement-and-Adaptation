"""
PromptForge Agent Prompts.

EXPORTS:
    - KIRA_ORCHESTRATOR_SYSTEM — Full orchestrator personality + routing
    - ORCHESTRATOR_FEW_SHOT_EXAMPLES — 8 detailed examples
    - PROMPT_ENGINEER_SYSTEM — Quality engineering with examples
    - ENGINEER_FEW_SHOT_EXAMPLES — 8 before/after examples

RULES.md Compliance:
    - Type hints on all exports
    - Docstrings with purpose
    - Constants in uppercase
    - Prompts only (no logic)
"""

__version__ = "2.0.0"

from .orchestrator import (
    KIRA_ORCHESTRATOR_SYSTEM,
    ORCHESTRATOR_FEW_SHOT_EXAMPLES,
    ORCHESTRATOR_RESPONSE_SCHEMA,
)

from .engineer import (
    PROMPT_ENGINEER_SYSTEM,
    ENGINEER_FEW_SHOT_EXAMPLES,
    ENGINEER_RESPONSE_SCHEMA,
)

from .shared import (
    FORBIDDEN_PHRASES,
    ROUTING_RULES,
    TEMPERATURE,
    MAX_TOKENS,
)

__all__ = [
    "__version__",
    "KIRA_ORCHESTRATOR_SYSTEM",
    "ORCHESTRATOR_FEW_SHOT_EXAMPLES",
    "ORCHESTRATOR_RESPONSE_SCHEMA",
    "PROMPT_ENGINEER_SYSTEM",
    "ENGINEER_FEW_SHOT_EXAMPLES",
    "ENGINEER_RESPONSE_SCHEMA",
    "FORBIDDEN_PHRASES",
    "ROUTING_RULES",
]

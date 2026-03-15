"""
Context Building Utilities.

EXPORTS:
    - build_context_block() — Dynamic user context injection
    - format_user_profile() — Profile formatting
    - format_memories() — LangMem memory formatting

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
"""

from .builder import (
    build_context_block,
    format_session_level,
    format_domains,
    format_tone_preference,
    format_quality_trend,
    format_memories,
)

__all__ = [
    "build_context_block",
    "format_session_level",
    "format_domains",
    "format_tone_preference",
    "format_quality_trend",
    "format_memories",
]

"""
Context Building Utilities.

EXPORTS:
    - build_context_block() — Dynamic user context injection
    - format_user_profile() — Profile formatting
    - format_memories() — LangMem memory formatting
    - context_agent() — Context analysis agent (re-exported for backward compat)

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

# Re-export context_agent from old monolithic file for backward compatibility
# This bridges the old single-file structure with the new package structure
import sys
import os
old_context_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "context.py")
if os.path.exists(old_context_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("agents.context_old", old_context_path)
    old_context = importlib.util.module_from_spec(spec)
    sys.modules["agents.context_old"] = old_context
    spec.loader.exec_module(old_context)
    context_agent = old_context.context_agent
else:
    # Fallback: try direct import (may work if old file not present)
    try:
        from agents import context as context_old
        context_agent = context_old.context_agent
    except (ImportError, AttributeError):
        def context_agent(state):
            """Stub fallback when context_agent is unavailable."""
            raise RuntimeError("context_agent not available - old context.py not found")

__all__ = [
    "build_context_block",
    "format_session_level",
    "format_domains",
    "format_tone_preference",
    "format_quality_trend",
    "format_memories",
    "context_agent",
]

# agents/utils/parsing.py
"""
Agent-level JSON parsing utilities.

Re-exports parse_json_response and format_history from root utils.py
to provide agents/ submodule access without circular imports.

RULES.md Compliance:
    - DRY Rule 1: Extract common patterns into functions
    - DRY Rule 2: Single source of truth (root utils.py)
"""

from utils import parse_json_response, format_history

__all__ = ["parse_json_response", "format_history"]

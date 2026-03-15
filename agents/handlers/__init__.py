"""
Request Handlers.

EXPORTS:
    - handle_conversation() — Conversation handler
    - handle_followup() — Followup refinement handler
    - handle_swarm_routing() — Swarm routing handler
    - kira_unified_handler() — Unified intent + response handler

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
"""

from .conversation import handle_conversation
from .followup import handle_followup
from .swarm import handle_swarm_routing
from .unified import kira_unified_handler

__all__ = [
    "handle_conversation",
    "handle_followup",
    "handle_swarm_routing",
    "kira_unified_handler",
]

# state.py
# ─────────────────────────────────────────────
# The shared data container that flows through
# every agent in the graph.
#
# Think of it as a baton in a relay race —
# each agent reads it, adds their piece, passes it on.
#
# Annotated[list, operator.add] means agents
# APPEND to messages, never overwrite them.
# ─────────────────────────────────────────────

# state.py
from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    raw_prompt:      str
    intent_result:   dict[str, Any]
    context_result:  dict[str, Any]
    domain_result:   dict[str, Any]
    improved_prompt: str
    final_response:  dict[str, Any]   # ← added
    messages:        Annotated[list[BaseMessage], operator.add]
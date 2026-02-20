# state.py
# ─────────────────────────────────────────────
# TypedDict schema for LangGraph state — the "baton" passed between agents.
# Each agent reads this, writes its results, passes it to the next node.
# Fields:
#   raw_prompt      → User's original input (never modified)
#   intent_result   → Output from intent_agent (goal_clarity, primary_intent, etc.)
#   context_result  → Output from context_agent (skill_level, tone, constraints)
#   domain_result   → Output from domain_agent (primary_domain, relevant_patterns)
#   improved_prompt → Final output from prompt_engineer_agent
# Note: messages field removed — swarm agents don't use conversation history.
# ─────────────────────────────────────────────

from typing import Any
from typing_extensions import TypedDict


class AgentState(TypedDict):
    raw_prompt:      str
    intent_result:   dict[str, Any]
    context_result:  dict[str, Any]
    domain_result:   dict[str, Any]
    improved_prompt: str
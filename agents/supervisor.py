# agents/supervisor.py
# ─────────────────────────────────────────────
# Orchestrator for the swarm — entry and exit points, no analysis logic.
#
# Two functions:
#   supervisor_entry  → Entry node, passes raw_prompt through so LangGraph has state to write.
#   supervisor_collect → Exit node, writes improved_prompt to satisfy LangGraph's requirement
#                        that every node must write to state. api.py reads full state directly.
#
# The supervisor does NOT do any analysis itself.
# It only orchestrates the flow and packages the final output for api.py to return.
#
# Flow in workflow.py:
#   supervisor_entry → intent_agent → context_agent → domain_agent → prompt_engineer → supervisor_collect → END
# ─────────────────────────────────────────────
from state import AgentState


def supervisor_entry(state: AgentState) -> dict:
    """
    Entry node — passes raw_prompt through so LangGraph
    has something to write to state.
    """
    return {"raw_prompt": state["raw_prompt"]}


def supervisor_collect(state: AgentState) -> dict:
    """
    Collection node — final step before returning to api.py.
    Writes to improved_prompt to satisfy LangGraph's requirement that every node writes something.
    api.py reads the full state directly, so no packaging needed here.
    """
    # LangGraph requires every node to write to at least one state field
    # improved_prompt already contains the final result from prompt_engineer
    return {"improved_prompt": state["improved_prompt"]}
# agents/supervisor.py
# ─────────────────────────────────────────────
# Supervisor Agent
#
# Job: Entry point and exit point of the system.
#      - Receives raw prompt from the user
#      - Fans out to swarm agents in parallel
#      - Collects swarm results
#      - Passes everything to Prompt Engineer
#      - Returns final response to user
#
# The Supervisor does NOT do any analysis itself.
# It only orchestrates and packages.
# ─────────────────────────────────────────────

# agents/supervisor.py
from state import AgentState


def supervisor_entry(state: AgentState) -> dict:
    """
    Entry node — passes raw_prompt through so LangGraph
    has something to write to state.
    """
    return {"raw_prompt": state["raw_prompt"]}


def supervisor_collect(state: AgentState) -> dict:
    """
    Collection node — packages final response.
    """
    return {
        "final_response": {
            "original_prompt": state["raw_prompt"],
            "improved_prompt": state.get("improved_prompt", ""),
            "breakdown": {
                "intent":  state.get("intent_result", {}),
                "context": state.get("context_result", {}),
                "domain":  state.get("domain_result", {}),
            }
        }
    }
# graph/workflow.py
# ─────────────────────────────────────────────
# Wires all 6 LangGraph nodes together and compiles the workflow.
#
# PARALLEL_MODE flag at top — flip to True when upgrading API key for 3x speedup.
# Currently sequential (False): intent → context → domain → prompt_engineer
# Parallel (True): all 3 swarm agents run simultaneously, then prompt_engineer.
#
# Node order matters:
#   1. supervisor_entry   → Initializes state with raw_prompt
#   2. intent_agent       → Analyzes WHAT user wants (goal_clarity, primary_intent)
#   3. context_agent      → Analyzes WHO is asking (skill_level, tone, constraints)
#   4. domain_agent       → Identifies domain + relevant patterns
#   5. prompt_engineer    → Rewrites prompt using all 3 upstream results
#   6. supervisor_collect → Packages final_response for api.py
#
# Exports: workflow (compiled StateGraph) — imported by api.py _run_swarm() only.
# ─────────────────────────────────────────────

from langgraph.graph import StateGraph, END
from state import AgentState
from agents.supervisor import supervisor_entry, supervisor_collect
from agents.intent import intent_agent
from agents.context import context_agent
from agents.domain import domain_agent
from agents.prompt_engineer import prompt_engineer_agent

# ── Switch this when you upgrade your API key ─
PARALLEL_MODE = False


def build_graph():
    graph = StateGraph(AgentState)

    # ── Register nodes (same for both modes) ──
    graph.add_node("supervisor_entry",   supervisor_entry)
    graph.add_node("intent_agent",       intent_agent)
    graph.add_node("context_agent",      context_agent)
    graph.add_node("domain_agent",       domain_agent)
    graph.add_node("prompt_engineer",    prompt_engineer_agent)
    graph.add_node("supervisor_collect", supervisor_collect)

    graph.set_entry_point("supervisor_entry")

    if PARALLEL_MODE:
        # ── Parallel: all 3 swarm agents run simultaneously
        graph.add_edge("supervisor_entry", "intent_agent")
        graph.add_edge("supervisor_entry", "context_agent")
        graph.add_edge("supervisor_entry", "domain_agent")
        graph.add_edge("intent_agent",     "prompt_engineer")
        graph.add_edge("context_agent",    "prompt_engineer")
        graph.add_edge("domain_agent",     "prompt_engineer")
    else:
        # ── Sequential: one after another
        graph.add_edge("supervisor_entry", "intent_agent")
        graph.add_edge("intent_agent",     "context_agent")
        graph.add_edge("context_agent",    "domain_agent")
        graph.add_edge("domain_agent",     "prompt_engineer")

    graph.add_edge("prompt_engineer",    "supervisor_collect")
    graph.add_edge("supervisor_collect", END)

    return graph.compile()


workflow = build_graph()
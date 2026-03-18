# graph/workflow.py
# ─────────────────────────────────────────────
# LangGraph StateGraph with TRUE Parallel Execution via Send()
#
# STEP 6 IMPLEMENTATION (per RULES.md):
# - Conditional edges from Kira orchestrator
# - TRUE parallel execution via LangGraph Send() API
# - Join node: prompt_engineer waits for all selected agents
# - Expected latency: 2-5s with Pollinations paid tier
#
# Flow (PARALLEL):
#   1. kira_orchestrator → Returns routing decision
#   2. route_to_agents() → Returns Send() objects for parallel execution
#   3. Parallel execution → intent, context, domain run simultaneously
#   4. Join at prompt_engineer → Waits for all, then synthesizes
#   5. END → Return final state
#
# Exports: workflow (compiled StateGraph)
# ─────────────────────────────────────────────

from typing import List, Optional
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from state import AgentState
from agents.orchestrator import orchestrator_node as kira_orchestrator
from agents.intent import intent_agent
from agents.context import context_agent
from agents.domain import domain_agent
from agents.prompt_engineer import prompt_engineer_agent

# ═══ PARALLEL MODE — ENABLED ═══════════════════
# Set to True for TRUE parallel execution via Send() API
# With Pollinations paid tier: expected latency 2-5s
PARALLEL_MODE = True


# ═══ ROUTING FUNCTION WITH Send() ══════════════

def route_to_agents(state: AgentState) -> List[Optional[Send]]:
    """
    Reads Kira's routing decision and returns Send() objects for TRUE parallel execution.
    
    This function is called by add_conditional_edges().
    It reads orchestrator_decision["agents_to_run"] and returns
    a list of Send() objects that LangGraph executes in parallel.
    
    Args:
        state: Current AgentState with orchestrator_decision
        
    Returns:
        List of Send() objects for parallel execution, or empty list
        
    Example:
        If orchestrator_decision["agents_to_run"] = ["intent", "domain"]
        Returns: [Send("intent_agent", state), Send("domain_agent", state)]
        
    Per RULES.md:
    - Intent: Always run unless simple direct command
    - Context: Skip if no session history (orchestrator handles this)
    - Domain: Skip if profile confidence > 85% (orchestrator handles this)
    - Prompt Engineer: ALWAYS runs (handled separately, never skipped)
    """
    decision = state.get("orchestrator_decision", {})
    agents_to_run = decision.get("agents_to_run", [])
    proceed_with_swarm = decision.get("proceed_with_swarm", False)
    
    # If no swarm or no agents, go straight to prompt engineer
    if not proceed_with_swarm or not agents_to_run:
        return ["prompt_engineer"]
    
    # Map agent names to node names
    node_map = {
        "intent": "intent_agent",
        "context": "context_agent",
        "domain": "domain_agent",
    }
    
    # Return Send() objects for TRUE parallel execution
    # LangGraph executes all Send() objects simultaneously
    return [
        Send(node_map[agent], state)
        for agent in agents_to_run
        if agent in node_map
    ]


# ═══ BUILD GRAPH ═══════════════════════════════

def build_graph() -> StateGraph:
    """
    Builds LangGraph StateGraph with TRUE parallel execution via Send().
    
    Node Order:
    1. kira_orchestrator → Routing decision (1 fast LLM call, ~500ms)
    2. Conditional edges → Returns Send() objects for parallel execution
    3. intent/context/domain → Run in PARALLEL via Send() API
    4. prompt_engineer → Join node, waits for all, synthesizes (1 full LLM call)
    5. END → Return final state
    
    Expected Latency (Pollinations paid tier):
    - Kira: ~500ms
    - Parallel agents: ~500-1000ms (max of parallel calls)
    - Prompt engineer: ~1-2s
    - TOTAL: 2-5s
    
    Returns:
        Compiled StateGraph ready for invocation
    """
    graph = StateGraph(AgentState)
    
    # ═══ REGISTER NODES ═══
    graph.add_node("kira_orchestrator", kira_orchestrator)
    graph.add_node("intent_agent", intent_agent)
    graph.add_node("context_agent", context_agent)
    graph.add_node("domain_agent", domain_agent)
    graph.add_node("prompt_engineer", prompt_engineer_agent)
    
    # Set entry point
    graph.set_entry_point("kira_orchestrator")
    
    # ═══ CONDITIONAL EDGES FROM KIRA ═══
    # Returns Send() objects for TRUE parallel execution
    graph.add_conditional_edges(
        "kira_orchestrator",
        route_to_agents,
        {
            "intent_agent": "intent_agent",
            "context_agent": "context_agent",
            "domain_agent": "domain_agent",
            "prompt_engineer": "prompt_engineer"
        }
    )
    
    # ═══ JOIN NODE ═══
    # Prompt engineer ALWAYS runs (never skipped)
    # It waits for ALL selected agents to complete (LangGraph handles this automatically)
    # When Send() is used, LangGraph automatically joins at the next common node
    graph.add_edge("intent_agent", "prompt_engineer")
    graph.add_edge("context_agent", "prompt_engineer")
    graph.add_edge("domain_agent", "prompt_engineer")
    
    # ═══ EXIT ═══
    graph.add_edge("prompt_engineer", END)
    
    return graph.compile()


# ═══ COMPILED WORKFLOW ═════════════════════════

workflow = build_graph()

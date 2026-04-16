# state.py
# ─────────────────────────────────────────────
# PromptForgeState TypedDict — Complete Schema (26 fields)
#
# This is the "baton" passed between all agents in LangGraph workflow.
# Organized in 5 sections per RULES.md:
#   1. INPUT (6 fields) — What comes in from user/request
#   2. MEMORY (3 fields) — Loaded from database before processing
#   3. ORCHESTRATOR (5 fields) — Kira's routing decisions
#   4. AGENT OUTPUTS (5 fields) — Results from each agent
#   5. OUTPUT (7 fields) — Final engineered result
#
# Modularity: This file is INDEPENDENT.
# - Imports ONLY from typing (no project dependencies)
# - Other modules import this, not vice versa (no circular deps)
# - Easy to test in isolation
# ─────────────────────────────────────────────

from typing import Any, Optional, List, Dict, Annotated
from operator import add
from typing_extensions import TypedDict


def merge_dict(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer for merging dictionaries from parallel agents — non-empty wins."""
    if left is None or left == {}:
        return right
    if right is None or right == {}:
        return left
    return {**left, **right}


class PromptForgeState(TypedDict):
    """
    Complete state schema for PromptForge v2.0 swarm orchestration.
    Passed between all agents in LangGraph workflow.

    Total: 27 fields organized in 5 sections.
    All fields must be initialized before use (use empty defaults if needed).
    """

    # ═══ SECTION 1: INPUT (6 fields) ═══

    message: str
    """User's actual message (5-2000 characters)."""

    session_id: str
    """From request, uniquely identifies conversation session."""

    user_id: str
    """From JWT, extracted via auth.uid(). Used for RLS database queries."""

    attachments: List[Dict[str, Any]]
    """Multimodal attachments: [{type, content/base64, filename}]."""

    input_modality: str
    """Type of input: 'text' | 'file' | 'image' | 'voice'."""

    conversation_history: List[Dict[str, Any]]
    """Last N turns from Supabase conversations table.
    Format: [{role: 'user'|'assistant', message: str, message_type: str}]"""

    # ═══ SECTION 2: MEMORY (3 fields) ═══

    user_profile: Dict[str, Any]
    """Loaded from Supabase user_profiles table.
    Keys: dominant_domains, preferred_tone, clarification_rate, etc."""

    langmem_context: List[Dict[str, Any]]
    """Top 5 memories from LangMem semantic search.
    Used in Phase 2 for pipeline memory."""

    mcp_trust_level: int
    """MCP surface trust level: 0 (cold) | 1 (warm) | 2 (tuned).
    Only used for MCP requests, always 0 for web app."""

    # ═══ SECTION 3: ORCHESTRATOR (5 fields) ═══

    orchestrator_decision: Dict[str, Any]
    """Full Kira orchestrator response JSON.
    Keys: user_facing_message, agents_to_run, clarification_needed, etc."""

    user_facing_message: str
    """Message user sees immediately via SSE (from Kira)."""

    pending_clarification: bool
    """True if waiting for user's answer to clarification question."""

    clarification_key: Optional[str]
    """Which field is being clarified (e.g., 'target_audience').
    None if no clarification pending."""

    proceed_with_swarm: bool
    """Kira's go/no-go decision. False if clarification needed first."""

    # ═══ SECTION 4: AGENT OUTPUTS (5 fields) ═══

    intent_analysis: Annotated[Dict[str, Any], merge_dict]
    """From intent agent — analyzes user's true goal.
    Keys: primary_intent, goal_clarity, missing_info."""

    context_analysis: Annotated[Dict[str, Any], merge_dict]
    """From context agent — analyzes user context.
    Keys: skill_level, tone, constraints, implicit_preferences."""

    domain_analysis: Annotated[Dict[str, Any], merge_dict]
    """From domain agent — identifies domain/patterns.
    Keys: primary_domain, sub_domain, relevant_patterns, complexity."""

    agents_skipped: Annotated[List[str], add]
    """Which agents didn't run and why.
    Example: ['context: no session history', 'domain: profile has 90% confidence']"""

    agents_run: Annotated[List[str], add]
    """List of agent names that successfully completed execution."""

    agent_latencies: Annotated[Dict[str, int], merge_dict]
    """Execution time per agent in milliseconds.
    Format: {agent_name: latency_ms} for performance monitoring."""

    latency_ms: Annotated[int, add]
    """Aggregate execution time for the entire swarm."""

    memories_applied: Annotated[int, add]
    """Number of LangMem memories retrieved and used for context."""

    # ═══ SECTION 5: OUTPUT (7 fields) ═══

    improved_prompt: str
    """Final engineered prompt from prompt engineer agent."""

    original_prompt: str
    """User's original input (unchanged, for reference)."""

    prompt_diff: List[Dict[str, Any]]
    """Changes with annotations.
    Format: [{type: 'add'|'remove'|'modify', old: str, new: str, explanation: str}]"""

    quality_score: Dict[str, int]
    """Prompt quality scores (1-5).
    Keys: specificity, clarity, actionability."""

    changes_made: List[str]
    """Human-readable change explanations.
    Example: ['Added role assignment', 'Specified output format', 'Included tone guidance']"""

    breakdown: Dict[str, Any]
    """Agent-specific insights for API response.
    Format: {intent: {...}, context: {...}, domain: {...}}"""


# ═══ Backward Compatibility ═══

# Keep old name for existing code that imports AgentState
# This avoids breaking changes during migration
AgentState = PromptForgeState

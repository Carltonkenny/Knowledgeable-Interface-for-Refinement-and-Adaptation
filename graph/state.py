# graph/state.py
"""
PromptForge LangGraph State Schema — Single Source of Truth.

VERSION: 2.0.0
STATUS: Production Ready (2026-2028 Standards)

RULES.md Compliance:
    - All fields typed with Optional[] for accumulative state
    - total=False: fields optional by default (LangGraph pattern)
    - Single source of truth — all nodes read/write this shape
    - Forward-compatible: v2.5/v3 fields included as Optional

State Flow:
    1. API endpoint initializes INPUT fields
    2. Orchestrator loads MEMORY fields (once, shared)
    3. Agents read MEMORY, write AGENT_OUTPUTS
    4. Prompt engineer synthesizes FINAL_OUTPUT

ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────┐
    │  PromptForgeState (26 fields across 8 sections)             │
    │                                                              │
    │  SECTION 1: INPUT (6 fields)                                 │
    │    — Initialized by API endpoint before workflow invocation  │
    │                                                              │
    │  SECTION 2: MEMORY (6 fields)                                │
    │    — Loaded ONCE by orchestrator, shared by all agents       │
    │    — Includes v2.5: user_facts, quality_trend                │
    │                                                              │
    │  SECTION 3: ROUTING (5 fields)                               │
    │    — Set by orchestrator node                                │
    │    — Includes v3: mode field for Mode 1/2 routing            │
    │                                                              │
    │  SECTION 4: AGENT OUTPUTS (5 fields)                         │
    │    — Set by individual agents (None if skipped)              │
    │                                                              │
    │  SECTION 5: FINAL OUTPUT (8 fields)                          │
    │    — Set by prompt_engineer node                             │
    │                                                              │
    │  SECTION 6: CLARIFICATION (4 fields)                         │
    │    — Set by orchestrator when clarification needed           │
    │                                                              │
    │  SECTION 7: V3 ERROR DIAGNOSIS (4 fields)                    │
    │    — Future-proofing for error diagnosis mode                │
    │                                                              │
    │  SECTION 8: V3 PROJECT CONTEXT (2 fields)                    │
    │    — Future-proofing for project-aware prompts               │
    └─────────────────────────────────────────────────────────────┘

Example:
    >>> from graph.state import PromptForgeState
    >>> state: PromptForgeState = {
    ...     "message": "write a function",
    ...     "user_id": "uuid-123",
    ...     "session_id": "session-456",
    ...     # ... other required fields
    ... }
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal


class PromptForgeState(TypedDict, total=False):
    """
    Complete state schema for PromptForge v2.0 swarm orchestration.
    
    total=False means all fields are optional by default.
    This is the LangGraph pattern for accumulative state:
    - Early nodes haven't populated output fields yet
    - Late nodes read what previous nodes wrote
    - Required fields (message, user_id) should be checked at runtime
    
    RULES.md:
    - Type hints mandatory on all fields
    - Docstrings complete for all fields
    - Optional fields use Optional[] type annotation
    - Forward-compatible: v2.5/v3 fields included now
    """
    
    # ═══ SECTION 1: INPUT (6 fields) — Initialized by API ═══
    
    message: str
    """
    User's actual message (5-2000 characters).
    
    Example: "write a FastAPI endpoint for user authentication"
    """
    
    session_id: str
    """
    From JWT, uniquely identifies conversation session.
    
    Format: UUID or nanoid, e.g., "session-abc123"
    Used for: Loading conversation history, saving requests
    """
    
    user_id: str
    """
    From JWT, extracted via auth.uid(). Used for RLS queries.
    
    Format: UUID, e.g., "user-xyz789"
    Used for: Loading user_profile, LangMem, all database queries
    """
    
    attachments: List[Dict[str, Any]]
    """
    Multimodal attachments from user's message.
    
    Format: [{type, content/base64, filename}]
    Types: 'image', 'file', 'audio'
    Example: [{"type": "image", "base64": "...", "filename": "screenshot.png"}]
    """
    
    input_modality: str
    """
    Type of input received from user.
    
    Values: 'text' | 'file' | 'image' | 'voice'
    Default: 'text' (web app)
    """
    
    conversation_history: List[Dict[str, Any]]
    """
    Last N turns from Supabase conversations table.
    
    Format: [{role: 'user'|'assistant', message: str, message_type: str}]
    message_type: 'text' | 'image' | 'file' | 'voice'
    Example: [
        {"role": "user", "message": "write a function", "message_type": "text"},
        {"role": "assistant", "message": "Got it — writing...", "message_type": "text"}
    ]
    """
    
    # ═══ SECTION 2: MEMORY (6 fields) — Loaded ONCE by orchestrator ═══
    
    user_profile: Dict[str, Any]
    """
    From Supabase user_profiles table.
    
    Keys:
    - dominant_domains: List[str] — Top 3 domains user works in
    - preferred_tone: str — "casual" | "formal" | "technical"
    - clarification_rate: float — 0.0-1.0 (how often user needs clarification)
    - prompt_quality_trend: List[float] — Last 5 quality scores
    - total_sessions: int — Total sessions for this user
    - domain_confidence: float — 0.0-1.0 confidence in domain classification
    
    Example: {
        "dominant_domains": ["coding", "marketing"],
        "preferred_tone": "technical",
        "clarification_rate": 0.15,
        "total_sessions": 23
    }
    """
    
    langmem_context: List[Dict[str, Any]]
    """
    Top 5 memories from LangMem semantic search.
    
    Format: [{content, domain, quality_score, created_at}]
    Example: [
        {
            "content": "User prefers concise prompts with examples",
            "domain": "coding",
            "quality_score": 4.2,
            "created_at": "2026-03-10T14:30:00Z"
        }
    ]
    """
    
    mcp_trust_level: int
    """
    MCP surface trust level. Only used for MCP requests.
    
    Values:
    - 0 (cold) — First interaction, no context
    - 1 (warm) — Some context from Supermemory
    - 2 (tuned) — Rich context, established relationship
    
    Web app always uses 0.
    """
    
    session_count: int
    """
    Total sessions for this user (for experience level formatting).
    
    From user_profile.total_sessions or counted from conversation_history.
    Used by format_session_level() to determine user experience level.
    
    Example: 23 → "Power user (23 sessions). Treat as peer."
    """
    
    # ─── V2.5 FIELDS — Fact Extractor / Self-Learning System ───
    
    user_facts: Optional[List[Dict[str, Any]]]
    """
    Verified facts from fact_extractor.py background job (v2.5).
    
    Character.ai pattern: Facts verified across multiple sessions,
    injected into every session for consistent personalization.
    
    Format: [{fact, confidence, source, verified_at}]
    Example: [
        {"fact": "User prefers FastAPI for backend", "confidence": 0.95, "source": "session-123"},
        {"fact": "User likes TypeScript over Python", "confidence": 0.87, "source": "session-456"}
    ]
    
    When populated: After fact_extractor.py runs (background task)
    Until then: None
    """
    
    quality_trend: Optional[List[float]]
    """
    Last 5 quality scores (1-5 scale) for trend detection (v2.5).
    
    Used by format_quality_trend() to show improving/declining trajectory.
    Updated after each session completes (background task).
    
    Example: [2.1, 2.8, 3.2, 3.6, 4.1] → "Improving — avg 3.2/5"
    
    When populated: After quality_trend updater runs
    Until then: None or from user_profile.prompt_quality_trend
    """
    
    # ═══ SECTION 3: ROUTING (5 fields) — Set by orchestrator ═══
    
    # ─── V3 FIELD — Mode Detection for Mode 1 vs Mode 2 ───
    
    mode: Literal["REFINE", "ARCHITECT", "ERROR_DIAGNOSIS"]
    """
    Request mode for Mode 1 vs Mode 2 routing (v3).
    
    Values:
    - REFINE — Standard prompt refinement (Mode 1)
    - ARCHITECT — System design, architecture decisions (Mode 2)
    - ERROR_DIAGNOSIS — Debugging, error analysis (Mode 2)
    
    When populated: By mode detection logic in orchestrator
    Until then: "REFINE" (default Mode 1)
    """
    
    route: Literal["CONVERSATION", "SWARM", "FOLLOWUP", "CLARIFICATION"]
    """
    Kira's routing decision.
    
    Values:
    - CONVERSATION — User is being brief, greeting, or small talk
    - SWARM — Full 4-agent prompt engineering pipeline
    - FOLLOWUP — User wants to modify previous prompt
    - CLARIFICATION — Need to ask user a question first
    
    Set by: orchestrator_node based on message analysis
    """
    
    input_quality: Dict[str, Any]
    """
    From score_input_quality() — structural quality assessment.
    
    Keys:
    - score: int (1-3) — thin, moderate, or rich
    - word_count: int — Number of words in message
    - has_context: bool — Has audience/purpose definition
    - has_constraints: bool — Has format/quality constraints
    - recommendation: str — "light" | "standard" | "full"
    
    Example: {
        "score": 3,
        "word_count": 45,
        "has_context": True,
        "has_constraints": True,
        "recommendation": "full"
    }
    """
    
    agents_to_run: List[str]
    """
    Which agents to execute in swarm mode.
    
    Values: Subset of ["intent", "context", "domain"]
    prompt_engineer ALWAYS runs (never skipped).
    
    Example: ["intent", "domain"] — skip context (no history)
    Set by: orchestrator_node based on skip conditions
    """
    
    orchestrator_decision: Dict[str, Any]
    """
    Full Kira orchestrator response JSON.
    
    Keys:
    - user_facing_message: str — Message to stream via SSE
    - proceed_with_swarm: bool — Whether to run swarm
    - agents_to_run: List[str] — Which agents to execute
    - clarification_needed: bool — Whether clarification needed
    - clarification_question: Optional[str] — The question to ask
    - skip_reasons: Dict[str, str] — Why agents were skipped
    - tone_used: str — Which tone Kira used
    - profile_applied: bool — Whether user profile was applied
    
    Example: {
        "user_facing_message": "Got it — engineering your prompt...",
        "proceed_with_swarm": True,
        "agents_to_run": ["intent", "domain"],
        "clarification_needed": False
    }
    """
    
    # ═══ SECTION 4: AGENT OUTPUTS (5 fields) — Set by each agent ═══
    
    intent_analysis: Optional[Dict[str, Any]]
    """
    From intent_agent — analyzes user's true goal.
    
    Keys:
    - primary_intent: str — The deep actual goal
    - secondary_intents: List[str] — Supporting goals
    - goal_clarity: str — "low" | "medium" | "high"
    - missing_info: List[str] — Specific missing details
    
    Example: {
        "primary_intent": "create secure authentication endpoint",
        "secondary_intents": ["learn FastAPI best practices"],
        "goal_clarity": "high",
        "missing_info": ["database choice", "auth method preference"]
    }
    
    None if: Agent was skipped (simple direct command)
    """
    
    context_analysis: Optional[Dict[str, Any]]
    """
    From context_agent — analyzes WHO the user is.
    
    Keys:
    - skill_level: str — "beginner" | "intermediate" | "expert"
    - tone: str — "casual" | "formal" | "technical" | "creative"
    - constraints: List[str] — Real limitations mentioned
    - implicit_preferences: List[str] — What user values
    - confidence: float — 0.0-1.0 confidence in analysis
    
    Example: {
        "skill_level": "intermediate",
        "tone": "technical",
        "constraints": ["must use existing database schema"],
        "implicit_preferences": ["values security", "prefers async code"],
        "confidence": 0.87
    }
    
    None if: Agent was skipped (no conversation history)
    """
    
    domain_analysis: Optional[Dict[str, Any]]
    """
    From domain_agent — identifies domain/patterns.
    
    Keys:
    - primary_domain: str — Precise field name
    - sub_domain: str — Specific discipline within field
    - relevant_patterns: List[str] — Prompt engineering patterns
    - complexity: str — "simple" | "moderate" | "complex"
    - confidence: float — 0.0-1.0 confidence
    
    Example: {
        "primary_domain": "coding",
        "sub_domain": "backend API development",
        "relevant_patterns": ["role_assignment", "output_format", "constraints"],
        "complexity": "moderate",
        "confidence": 0.92
    }
    
    None if: Agent was skipped (profile confidence >85%)
    """
    
    agents_skipped: List[str]
    """
    Which agents didn't run and why.
    
    Format: ["agent_name: reason"]
    Example: [
        "context: no conversation history",
        "domain: profile confidence 0.94 > 0.85 threshold"
    ]
    
    Empty list if: All agents ran
    """
    
    agent_latencies: Dict[str, int]
    """
    Agent execution times for performance tracking.
    
    Format: {agent_name: latency_ms}
    Example: {
        "intent_agent": 423,
        "context_agent": 387,
        "domain_agent": 456,
        "prompt_engineer": 1834
    }
    """
    
    # ═══ SECTION 5: FINAL OUTPUT (8 fields) — Set by prompt_engineer ═══
    
    improved_prompt: Optional[str]
    """
    Final engineered prompt from prompt_engineer.
    
    Full prompt ready to send to target LLM.
    Includes: role assignment, context, constraints, examples, output format.
    
    Example: "You are a FastAPI expert. Create a secure authentication endpoint..."
    
    None if: Swarm didn't run (CONVERSATION or CLARIFICATION route)
    """
    
    original_prompt: Optional[str]
    """
    User's original input (for diff generation).
    
    Same as state.message but preserved for comparison.
    Used to generate prompt_diff showing what changed.
    """
    
    prompt_diff: List[Dict[str, Any]]
    """
    Changes made with annotations.
    
    Format: [{type, before, after, reason}]
    type: "added" | "removed" | "modified" | "reordered"
    
    Example: [
        {
            "type": "added",
            "before": None,
            "after": "You are a FastAPI expert with 10 years experience",
            "reason": "role_assignment pattern for better output quality"
        }
    ]
    """
    
    quality_score: Dict[str, Any]
    """
    Quality scores for engineered prompt.
    
    Keys:
    - specificity: int (1-5) — How specific is the prompt
    - clarity: int (1-5) — How clear is the intent
    - actionability: int (1-5) — How actionable are the instructions
    - overall: float (1-5) — Weighted average
    
    Example: {
        "specificity": 4,
        "clarity": 5,
        "actionability": 4,
        "overall": 4.3
    }
    """
    
    changes_made: List[str]
    """
    Human-readable change explanations.
    
    Example: [
        "Added expert persona for better output quality",
        "Specified JSON output format for consistency",
        "Added security constraints for production readiness"
    ]
    """
    
    breakdown: Dict[str, Any]
    """
    Agent-specific insights for transparency.
    
    Keys:
    - intent: str — Summary of intent analysis
    - context: str — Summary of context analysis
    - domain: str — Summary of domain analysis
    - patterns_applied: List[str] — Which patterns were used
    
    Example: {
        "intent": "User wants secure authentication endpoint",
        "context": "Intermediate developer, prefers technical tone",
        "domain": "Backend API development",
        "patterns_applied": ["role_assignment", "output_format", "constraints"]
    }
    """
    
    user_facing_message: str
    """
    Message user sees via SSE stream (from Kira).
    
    Personality-driven response that streams immediately.
    Example: "Got it — making this production-ready with proper auth..."
    """
    
    # ═══ SECTION 6: CLARIFICATION (4 fields) — Set by orchestrator ═══
    
    clarification_needed: bool
    """
    True if Kira needs user answer before proceeding.
    
    Set when: ambiguity_score > 0.7 or critical info missing
    """
    
    clarification_question: Optional[str]
    """
    The actual question Kira asked user.
    
    Example: "What database are you using — PostgreSQL or MySQL?"
    
    None if: No clarification needed
    """
    
    clarification_key: Optional[str]
    """
    Which field is being clarified.
    
    Example: "database_type" or "target_audience"
    Used to inject answer into state when user responds.
    
    None if: No clarification needed
    """
    
    pending_clarification: bool
    """
    True if waiting for user's answer to clarification question.
    
    Saved to session in Supabase.
    On next request: Check this flag FIRST, inject answer, clear flag.
    """
    
    # ═══ SECTION 7: V3 ERROR DIAGNOSIS (4 fields) — Future-proofing ═══
    
    error_text: Optional[str]
    """
    Pasted error from downstream tool (v3).
    
    When mode="ERROR_DIAGNOSIS", this contains the actual error message.
    Example: "TypeError: Cannot read property 'map' of undefined"
    
    When populated: When error diagnosis mode is implemented
    Until then: None
    """
    
    original_tool: Optional[Literal["cursor", "claude_code", "replit", "other"]]
    """
    Which tool the error came from (v3).
    
    Values: "cursor" | "claude_code" | "replit" | "other"
    Used to tailor error diagnosis to tool's context.
    
    When populated: When MCP integration expands to error diagnosis
    Until then: None
    """
    
    error_category: Optional[str]
    """
    Classified error type (v3).
    
    From classify_redo() or error classifier agent.
    Example: "syntax" | "logic" | "config" | "dependency" | "runtime"
    
    When populated: When error diagnosis agent is built
    Until then: None
    """
    
    error_fix_suggestion: Optional[str]
    """
    Suggested fix from error diagnosis agent (v3).
    
    Example: "Add optional chaining: data?.map() instead of data.map()"
    
    When populated: When error diagnosis agent is built
    Until then: None
    """
    
    # ═══ SECTION 8: V3 PROJECT CONTEXT (2 fields) — Future-proofing ═══
    
    project_context: Optional[str]
    """
    From kira.context.md or project analysis (v3).
    
    Project-level context that persists across sessions.
    Example: "Building a SaaS platform with Next.js + Supabase"
    
    When populated: When project-aware prompts are implemented
    Until then: None
    """
    
    session_level_context: Optional[str]
    """
    Project context specific to current session (v2.5/v3).
    
    Temporary context for this session only.
    Example: "Refactoring authentication module to use JWT"
    
    When populated: When session-level context tracking is added
    Until then: None
    """


# ═══ STATE INITIALIZATION HELPER ═══════════════════════════════

def create_initial_state(
    message: str,
    user_id: str,
    session_id: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    input_modality: str = "text",
) -> PromptForgeState:
    """
    Create initial state with required INPUT fields.
    
    All other fields will be populated by orchestrator and agents.
    
    Args:
        message: User's message
        user_id: From JWT token
        session_id: From JWT token
        conversation_history: Optional, loaded by API before invocation
        attachments: Optional, parsed from multipart request
        input_modality: "text" | "file" | "image" | "voice"
    
    Returns:
        PromptForgeState with INPUT fields initialized
    
    Example:
        >>> state = create_initial_state(
        ...     message="write a function",
        ...     user_id="user-123",
        ...     session_id="session-456"
        ... )
        >>> state["message"]
        "write a function"
    """
    state: PromptForgeState = {
        "message": message,
        "user_id": user_id,
        "session_id": session_id,
        "conversation_history": conversation_history or [],
        "attachments": attachments or [],
        "input_modality": input_modality,
        # MEMORY fields loaded by orchestrator
        "user_profile": {},
        "langmem_context": [],
        "mcp_trust_level": 0,
        "session_count": 0,
        # ROUTING fields set by orchestrator
        "mode": "REFINE",
        "route": "SWARM",
        "input_quality": {},
        "agents_to_run": [],
        "orchestrator_decision": {},
        # AGENT_OUTPUTS fields (None until agents run)
        "intent_analysis": None,
        "context_analysis": None,
        "domain_analysis": None,
        "agents_skipped": [],
        "agent_latencies": {},
        # FINAL OUTPUT fields (set by prompt_engineer)
        "improved_prompt": None,
        "original_prompt": None,
        "prompt_diff": [],
        "quality_score": {},
        "changes_made": [],
        "breakdown": {},
        "user_facing_message": "",
        # CLARIFICATION fields
        "clarification_needed": False,
        "clarification_question": None,
        "clarification_key": None,
        "pending_clarification": False,
        # V3 ERROR DIAGNOSIS fields (future-proofing)
        "error_text": None,
        "original_tool": None,
        "error_category": None,
        "error_fix_suggestion": None,
        # V3 PROJECT CONTEXT fields (future-proofing)
        "project_context": None,
        "session_level_context": None,
    }
    
    return state

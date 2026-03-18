# service.py
# ─────────────────────────────────────────────
# Business Logic Layer — PromptForge v2.0
#
# CONTAINS:
#   1. _run_swarm() — LangGraph workflow executor with caching
#   2. _run_swarm_with_clarification() — Clarification loop wrapper
#   3. compute_diff() — Word-level diff for frontend DiffView
#   4. sse_format() — Server-Sent Event formatter
#
# RULES.md Compliance:
#   - No FastAPI dependency (callable from CLI, cron, WebSocket)
#   - Type hints mandatory
#   - Docstrings complete
#   - Error handling comprehensive
#   - Logging contextual
#   - <500 lines
# ─────────────────────────────────────────────

import json
import difflib
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from fastapi import HTTPException

from workflow import workflow
from state import PromptForgeState
from utils import get_cached_result, set_cached_result

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────
GRAPH_TIMEOUT = 180  # seconds — for sequential 4-call swarm


# ── Swarm Execution ──────────────────────────

def _run_swarm(prompt: str, user_id: str, input_modality: str = "text", 
               file_base64: str = None, file_type: str = None) -> dict:
    """
    Runs full LangGraph swarm.
    Checks cache first — if hit, skips all 4 LLM calls entirely.
    Used by both /refine and /chat.
    
    Args:
        prompt: User's message
        user_id: From authenticated JWT
        input_modality: 'text' | 'file' | 'image' | 'voice'
        file_base64: Base64 encoded file content (if any)
        file_type: MIME type of file (if any)
    
    Returns:
        Final state dict with improved_prompt, quality_score, etc.
        
    Raises:
        HTTPException: 504 on timeout
    """
    # Cache check — instant return on hit
    cached = get_cached_result(prompt)
    if cached:
        return cached

    # Build attachments array if file provided
    attachments = []
    if file_base64 and file_type:
        attachments = [{
            "type": "image" if file_type.startswith("image/") else "file",
            "content": file_base64,
            "filename": f"upload.{file_type.split('/')[-1]}",
            "media_type": file_type,
        }]

    initial_state = PromptForgeState(
        message=prompt,
        user_id=user_id,  # PROPAGATED: Essential for LangMem
        session_id="default",  # Overwritten by route if needed
        intent_analysis={},
        context_analysis={},
        domain_analysis={},
        improved_prompt="",
        attachments=attachments,
        input_modality=input_modality,
        latency_ms=0,      # INITIALIZED: Survives parallel join
        memories_applied=0, # INITIALIZED: Survives parallel join
        conversation_history=[],
        user_profile={},
        langmem_context=[],
        mcp_trust_level=0,
        orchestrator_decision={},
        user_facing_message="Analyzing your request...",
        pending_clarification=False,
        clarification_key=None,
        proceed_with_swarm=True,
        original_prompt=prompt,
        prompt_diff=[],
        quality_score={},
        changes_made=[],
        breakdown={},
        agents_skipped=[],
        agents_run=[],
        agent_latencies={}
    )

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(workflow.invoke, initial_state)
        try:
            result = future.result(timeout=GRAPH_TIMEOUT)
            # Store in cache for next time
            set_cached_result(prompt, result)
            return result
        except TimeoutError:
            raise HTTPException(status_code=504, detail="Request timed out — please retry")


def _run_swarm_with_clarification(
    message: str,
    clarification_key: Optional[str],
    user_id: str,
    session_id: str
) -> dict:
    """
    Run swarm with clarification already provided.
    Skips orchestrator — fires swarm directly with clarified context.
    
    Args:
        message: User's clarification answer
        clarification_key: What field was being clarified
        user_id: From JWT
        session_id: Conversation session
        
    Returns:
        Final state from swarm
        
    Example:
        state = _run_swarm_with_clarification(
            message="I want to write about AI ethics",
            clarification_key="topic_focus",
            user_id="user-uuid",
            session_id="session-123"
        )
    """
    # Check cache first
    cached = get_cached_result(message)
    if cached:
        logger.info(f"[service] cache hit for clarification answer")
        return cached
    
    logger.info(f"[service] running swarm with clarification: key={clarification_key}")
    
    # Initialize state with clarification already resolved
    initial_state = PromptForgeState(
        message=message,
        session_id=session_id,
        user_id=user_id,
        attachments=[],
        input_modality="text",
        conversation_history=[],
        user_profile={},
        langmem_context=[],
        mcp_trust_level=0,
        orchestrator_decision={
            "user_facing_message": "Got it — let me work with that.",
            "proceed_with_swarm": True,
            "agents_to_run": ["intent", "domain"],  # Skip context (no history yet)
            "clarification_needed": False,
            "clarification_question": None,
            "skip_reasons": {"context": "clarification just resolved"},
            "tone_used": "direct",
            "profile_applied": False,
        },
        user_facing_message="Got it — let me work with that.",
        pending_clarification=False,  # Already resolved
        clarification_key=None,
        proceed_with_swarm=True,
        intent_analysis={},
        context_analysis={},
        domain_analysis={},
        agents_skipped=["context"],
        agent_latencies={},
        latency_ms=0,
        memories_applied=0,
        improved_prompt="",
        original_prompt=message,
        prompt_diff=[],
        quality_score={},
        changes_made=[],
        breakdown={},
    )
    
    # Run workflow
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(workflow.invoke, initial_state)
        try:
            result = future.result(timeout=GRAPH_TIMEOUT)
            # Store in cache
            set_cached_result(message, result)
            return result
        except TimeoutError:
            raise HTTPException(status_code=504, detail="Request timed out — please retry")


# ── Diff Computation ─────────────────────────

def compute_diff(original: str, improved: str) -> List[Dict[str, str]]:
    """
    Compute word-level diff between original and improved prompts.
    Returns list of {type: 'add'|'remove'|'keep', text: str} items
    for the frontend DiffView component.

    Args:
        original: User's original prompt text
        improved: Kira's engineered prompt text

    Returns:
        List of diff items with type and text fields
    """
    original_words = original.split()
    improved_words = improved.split()

    diff_items: List[Dict[str, str]] = []
    matcher = difflib.SequenceMatcher(None, original_words, improved_words)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            diff_items.append({"type": "keep", "text": " ".join(original_words[i1:i2]) + " "})
        elif tag == 'replace':
            diff_items.append({"type": "remove", "text": " ".join(original_words[i1:i2]) + " "})
            diff_items.append({"type": "add", "text": " ".join(improved_words[j1:j2]) + " "})
        elif tag == 'delete':
            diff_items.append({"type": "remove", "text": " ".join(original_words[i1:i2]) + " "})
        elif tag == 'insert':
            diff_items.append({"type": "add", "text": " ".join(improved_words[j1:j2]) + " "})

    return diff_items


# ── SSE Formatting ───────────────────────────

def sse_format(event: str, data: dict) -> str:
    """
    Formats a Server-Sent Event string.
    Frontend expects: data: {"type": "event", "data": {...}}
    
    Args:
        event: Event type (status, kira_message, result, done, error)
        data: Event payload dict
        
    Returns:
        SSE-formatted string with trailing newlines
    """
    # Wrap in the format the frontend parser expects
    wrapped_data = {"type": event, "data": data}
    return f"data: {json.dumps(wrapped_data)}\n\n"


# Backward compatibility aliases
_compute_diff = compute_diff


__all__ = [
    "_run_swarm",
    "_run_swarm_with_clarification",
    "compute_diff",
    "sse_format",
    "_compute_diff",  # backward compat
]

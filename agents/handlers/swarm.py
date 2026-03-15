# agents/handlers/swarm.py
"""
Swarm Routing Handler.

CONTAINS:
    1. handle_swarm_routing() — Route to 4-agent swarm

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Error handling comprehensive
    - Logging contextual
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def handle_swarm_routing(
    message: str,
    session_id: str,
    user_id: str,
    user_profile: Dict[str, Any],
    conversation_history: List[Dict[str, Any]],
    langmem_context: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Route to 4-agent swarm for full prompt engineering.
    
    Uses LangGraph StateGraph with parallel execution via Send() API.
    
    Args:
        message: User's message
        session_id: Conversation session ID
        user_id: User UUID from JWT
        user_profile: User profile from Supabase
        conversation_history: Last 6 conversation turns
        langmem_context: Top 5 memories from LangMem
        
    Returns:
        Dict with improved_prompt, breakdown, quality_score, latency_ms
        
    Example:
        >>> result = handle_swarm_routing("write a story", "session-123", "user-uuid", ...)
        >>> result["improved_prompt"]
        "You are a seasoned author..."
    """
    from workflow import workflow
    from state import AgentState
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from fastapi import HTTPException
    
    GRAPH_TIMEOUT = 180  # seconds
    
    try:
        # Build initial state
        initial_state = AgentState(
            message=message,
            session_id=session_id,
            user_id=user_id,
            user_profile=user_profile,
            conversation_history=conversation_history,
            langmem_context=langmem_context,
            intent_analysis={},
            context_analysis={},
            domain_analysis={},
            improved_prompt="",
            attachments=[],
            input_modality="text",
        )
        
        # Execute workflow with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(workflow.invoke, initial_state)
            try:
                result = future.result(timeout=GRAPH_TIMEOUT)
            except TimeoutError:
                raise HTTPException(status_code=504, detail="Request timed out")
        
        logger.info(f"[swarm] completed for user={user_id[:8]}...")
        
        return {
            "improved_prompt": result.get("improved_prompt", ""),
            "breakdown": result.get("breakdown", {}),
            "quality_score": result.get("quality_score", {}),
            "changes_made": result.get("changes_made", []),
            "latency_ms": result.get("agent_latencies", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[swarm] failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Swarm failed: {str(e)}")

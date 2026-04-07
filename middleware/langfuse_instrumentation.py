# middleware/langfuse_instrumentation.py
# ─────────────────────────────────────────────
# LangFuse Instrumentation — Self-hosted LLM Observability
#
# Traces every LLM call across all agents:
# - Orchestrator routing decisions
# - Intent/Context/Domain analysis
# - Prompt Engineer synthesis
# - Quality scores and latencies
# ─────────────────────────────────────────────

import os
import logging
from typing import Any, Dict, List, Optional
from langfuse import Langfuse

logger = logging.getLogger(__name__)

_langfuse_client: Optional[Langfuse] = None


def get_langfuse_client() -> Optional[Langfuse]:
    """Get or create LangFuse client (lazy singleton)."""
    global _langfuse_client

    if _langfuse_client is not None:
        return _langfuse_client

    host = os.getenv("LANGFUSE_HOST", "http://localhost:3001")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        logger.info("[langfuse] disabled — set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        return None

    try:
        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        logger.info(f"[langfuse] initialized — host: {host}")
        return _langfuse_client
    except Exception as e:
        logger.error(f"[langfuse] initialization failed: {e}")
        return None


def trace_llm_call(
    agent_name: str,
    prompt_text: str,
    response_text: str,
    latency_ms: int = 0,
    model_name: str = "",
    quality_score: Optional[Dict[str, Any]] = None,
    session_id: str = "",
    user_id: str = "",
    trace_id: Optional[str] = None,
    is_retry: bool = False,
) -> Optional[str]:
    """
    Trace a single LLM call in LangFuse.

    Args:
        agent_name: Which agent made the call (orchestrator, intent, etc.)
        prompt_text: The prompt sent to the LLM
        response_text: The LLM's response
        latency_ms: How long the call took
        model_name: Which model was used
        quality_score: Quality score dict (if applicable)
        session_id: User session ID
        user_id: User identifier
        trace_id: Parent trace ID (to link multiple agent calls)
        is_retry: Whether this is a retry attempt

    Returns:
        Trace ID if successful, None otherwise
    """
    client = get_langfuse_client()
    if not client:
        return None

    try:
        # Create or get existing trace
        if trace_id:
            trace = client.trace(id=trace_id)
        else:
            trace = client.trace(
                name=f"promptforge_{agent_name}",
                session_id=session_id or "default",
                user_id=user_id or "anonymous",
            )

        # Add generation (LLM call)
        generation = trace.generation(
            name=f"{agent_name}_llm_call",
            input=prompt_text[:4000],  # LangFuse limit
            output=response_text[:4000] if response_text else "empty",
            metadata={
                "agent": agent_name,
                "latency_ms": latency_ms,
                "is_retry": is_retry,
            },
        )

        # Add score if quality data available
        if quality_score and "overall" in quality_score:
            trace.score(
                name="quality",
                value=quality_score["overall"],
                data_type="NUMERIC",
            )

        return trace.id

    except Exception as e:
        logger.error(f"[langfuse] trace_llm_call failed for {agent_name}: {e}")
        return None


def trace_swarm_run(
    original_prompt: str,
    improved_prompt: str,
    agents_run: List[str],
    agents_skipped: List[str],
    agent_latencies: Dict[str, int],
    quality_score: Dict[str, Any],
    domain: str = "general",
    session_id: str = "",
    user_id: str = "",
    trace_id: Optional[str] = None,
) -> Optional[str]:
    """
    Trace a complete swarm execution as a single trace with summary.
    """
    client = get_langfuse_client()
    if not client:
        return None

    try:
        if not trace_id:
            import uuid
            trace_id = str(uuid.uuid4())

        trace = client.trace(
            id=trace_id,
            name="promptforge_swarm",
            session_id=session_id or "default",
            user_id=user_id or "anonymous",
            input={"original_prompt": original_prompt[:2000]},
            output={"improved_prompt": improved_prompt[:2000]} if improved_prompt else None,
            tags=[domain, "swarm"] + [f"agent:{a}" for a in agents_run],
            metadata={
                "agents_run": agents_run,
                "agents_skipped": agents_skipped,
                "agent_latencies": agent_latencies,
                "domain": domain,
            },
        )

        # Overall quality score
        if quality_score and "overall" in quality_score:
            trace.score(
                name="quality_overall",
                value=quality_score["overall"],
                data_type="NUMERIC",
            )

        return trace_id

    except Exception as e:
        logger.error(f"[langfuse] trace_swarm_run failed: {e}")
        return None


def shutdown_langfuse() -> None:
    """Flush all pending LangFuse events before shutdown."""
    global _langfuse_client
    if _langfuse_client:
        try:
            _langfuse_client.flush()
            logger.info("[langfuse] flushed all pending events")
        except Exception as e:
            logger.error(f"[langfuse] shutdown failed: {e}")
        _langfuse_client = None


__all__ = [
    "get_langfuse_client",
    "trace_llm_call",
    "trace_swarm_run",
    "shutdown_langfuse",
]

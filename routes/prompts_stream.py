# routes/prompts_stream.py
# ─────────────────────────────────────────────
# Streaming Chat Endpoint — Extracted from prompts.py
#   POST /chat/stream → SSE streaming version
#
# RULES.md: <500 lines, type hints, docstrings, error handling
# ─────────────────────────────────────────────

import asyncio
import logging
import time
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from service import sse_format, _astream_swarm, compute_diff
from auth import User, get_current_user
from database import (
    save_request, save_conversation,
    get_conversation_history, update_session_activity, get_last_activity,
    get_conversation_count,
)
from memory.langmem import write_to_langmem
from memory.profile_updater import should_trigger_update, update_user_profile
from utils import calculate_overall_quality

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prompts"])


# ── Schemas ───────────────────────────────────

class ChatRequest(BaseModel):
    """Schema for chat/stream request"""
    message: str
    session_id: Optional[str] = None
    input_modality: Optional[str] = "text"
    file_base64: Optional[str] = None
    file_type: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for chat response"""
    type: str
    reply: str
    improved_prompt: Optional[str] = None
    diff: Optional[list] = None
    quality_score: Optional[dict] = None
    kira_message: Optional[str] = None
    memories_applied: int = 0
    latency_ms: int = 0
    agents_run: list = []
    session_id: Optional[str] = None


# ── Streaming Chat Endpoint ──────────────────

@router.post("/chat/stream", response_model=ChatResponse)
async def chat_stream(req: ChatRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    """
    Streaming version of /chat.
    Sends Server-Sent Events (SSE) as processing progresses.
    Requires JWT authentication.
    """
    async def generate():
        try:
            logger.info(f"[api] /chat/stream user_id={user.user_id} session={req.session_id}")

            yield sse_format("status", {"message": "Loading conversation history..."})

            loop = asyncio.get_event_loop()

            history = await loop.run_in_executor(None, lambda: get_conversation_history(req.session_id, limit=6))

            from database import get_user_profile
            user_profile = await loop.run_in_executor(None, lambda: get_user_profile(user.user_id) or {})
            user_profile["user_id"] = user.user_id

            yield sse_format("status", {"message": "Understanding your message..."})

            # Default values in case unified handler fails
            intent = "NEW_PROMPT"
            reply = "Processing your request..."
            confidence = 0.5
            clarification_needed = False
            memories_applied = 0
            latency_ms = 0

            try:
                result = await loop.run_in_executor(
                    None,
                    lambda: kira_unified_handler(
                        message=req.message,
                        history=history,
                        user_profile=user_profile
                    )
                )

                intent = result.get("intent", "NEW_PROMPT")
                reply = result.get("response", reply)
                confidence = result.get("confidence", 0.5)
                clarification_needed = result.get("clarification_needed", False)
                memories_applied = result.get("memories_applied", 0)
                latency_ms = result.get("latency_ms", 0)

                logger.info(f"[api] unified handler complete: intent={intent}, memories={memories_applied}, latency={latency_ms}ms")
            except Exception as e:
                logger.warning(f"[api] unified handler failed: {e}, defaulting to NEW_PROMPT")

            # 🧠 PHASE 1 TRANSPARENCY: Inject Brain findings into Thought Accordion
            intent_map = {
                "CONVERSATION": "Engaging in casual conversation...",
                "FOLLOWUP": "Analyzing your refinement request...",
                "NEW_PROMPT": "New objective detected: Engineering a precise prompt..."
            }
            yield sse_format("status", {"message": f"🧠 {intent_map.get(intent, 'Analyzing intent...')}"})

            if memories_applied > 0:
                summary = result.get("memory_summary", f"Recalled {memories_applied} memories for personalization.")
                yield sse_format("status", {"message": f"📚 {summary}"})
            else:
                yield sse_format("status", {"message": "📚 No relevant past memories found. Processing as a fresh request."})

            if intent in ["CONVERSATION", "FOLLOWUP"]:
                # Word-by-word streaming (natural cadence, ~6x fewer SSE events)
                words = reply.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield sse_format("kira_message", {"message": chunk, "complete": False})
                    await asyncio.sleep(0.02)

            if intent == "CONVERSATION":
                save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="conversation", user_id=user.user_id)
                save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="conversation", user_id=user.user_id)
                yield sse_format("kira_message", {"message": "", "complete": True})
                yield sse_format("result", {"type": "conversation", "reply": reply, "improved_prompt": None, "memories_applied": memories_applied, "latency_ms": latency_ms})
                yield sse_format("done", {"message": "Complete"})
                return

            elif intent == "FOLLOWUP":
                improved = result.get("improved_prompt", "")
                save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="followup", user_id=user.user_id)
                save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="followup_refined", improved_prompt=improved, user_id=user.user_id)
                yield sse_format("kira_message", {"message": "", "complete": True})
                yield sse_format("result", {"type": "followup_refined", "reply": reply, "improved_prompt": improved, "memories_applied": memories_applied, "latency_ms": latency_ms})
                yield sse_format("done", {"message": "Complete"})
                return

            if clarification_needed:
                clarification_key = "topic"
                user_facing_message = reply

                save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="new_prompt", user_id=user.user_id)
                save_conversation(session_id=req.session_id, role="assistant", message=user_facing_message, message_type="clarification_question", user_id=user.user_id)

                yield sse_format("kira_message", {"message": user_facing_message, "complete": True})
                yield sse_format("result", {"type": "clarification_requested", "reply": user_facing_message})
                yield sse_format("done", {"message": "Complete"})
                return

            # NEW_PROMPT (swarm execution)
            yield sse_format("status", {"message": "⚡ Orchestrator: Launching agents..."})

            final_state = {}
            start_time = time.time()

            # Using Native LangGraph Streaming instead of thread-blocking executor
            async for chunk in _astream_swarm(req.message, user.user_id, req.input_modality or "text", req.file_base64, req.file_type):
                if chunk.get("is_cached"):
                    final_state = chunk["final_state"]
                    break

                # ═══ REAL AGENT THINKING: Stream actual agent data ═══
                if "orchestrator_decision" in chunk:
                    decision = chunk["orchestrator_decision"]
                    latency_ms = chunk.get("latency_ms", 0)
                    memories_applied = chunk.get("memories_applied", 0)

                    yield sse_format("agent_update", {
                        "agent": "orchestrator",
                        "state": "complete",
                        "latency_ms": latency_ms,
                        "data": {
                            "agents_to_run": decision.get("agents_to_run", []),
                            "clarification_needed": decision.get("clarification_needed", False),
                            "tone_used": decision.get("tone_used", "direct"),
                            "skip_reasons": decision.get("skip_reasons", {})
                        },
                        "memories_applied": memories_applied
                    })

                if "intent_agent" in chunk:
                    agent_data = chunk["intent_agent"]
                    analysis = agent_data.get("intent_analysis", {})
                    latency_ms = agent_data.get("latency_ms", 0)
                    was_skipped = agent_data.get("was_skipped", False)

                    if was_skipped:
                        yield sse_format("agent_update", {
                            "agent": "intent",
                            "state": "skipped",
                            "latency_ms": latency_ms,
                            "skip_reason": agent_data.get("skip_reason", "skipped"),
                            "data": None
                        })
                    elif analysis and analysis.get("primary_intent"):
                        yield sse_format("agent_update", {
                            "agent": "intent",
                            "state": "complete",
                            "latency_ms": latency_ms,
                            "data": {
                                "primary_intent": analysis.get("primary_intent", ""),
                                "goal_clarity": analysis.get("goal_clarity", "unknown"),
                                "missing_info": analysis.get("missing_info", [])
                            }
                        })

                if "context_agent" in chunk:
                    agent_data = chunk["context_agent"]
                    analysis = agent_data.get("context_analysis", {})
                    latency_ms = agent_data.get("latency_ms", 0)
                    was_skipped = agent_data.get("was_skipped", False)

                    if was_skipped:
                        yield sse_format("agent_update", {
                            "agent": "context",
                            "state": "skipped",
                            "latency_ms": latency_ms,
                            "skip_reason": agent_data.get("skip_reason", "no conversation history"),
                            "data": None
                        })
                    elif analysis and analysis.get("tone"):
                        yield sse_format("agent_update", {
                            "agent": "context",
                            "state": "complete",
                            "latency_ms": latency_ms,
                            "data": {
                                "skill_level": analysis.get("skill_level", "intermediate"),
                                "tone": analysis.get("tone", "direct"),
                                "constraints": analysis.get("constraints", []),
                                "implicit_preferences": analysis.get("implicit_preferences", [])
                            }
                        })

                if "domain_agent" in chunk:
                    agent_data = chunk["domain_agent"]
                    analysis = agent_data.get("domain_analysis", {})
                    latency_ms = agent_data.get("latency_ms", 0)
                    was_skipped = agent_data.get("was_skipped", False)

                    if was_skipped:
                        yield sse_format("agent_update", {
                            "agent": "domain",
                            "state": "skipped",
                            "latency_ms": latency_ms,
                            "skip_reason": agent_data.get("skip_reason", "high domain confidence"),
                            "data": None
                        })
                    elif analysis and analysis.get("primary_domain"):
                        yield sse_format("agent_update", {
                            "agent": "domain",
                            "state": "complete",
                            "latency_ms": latency_ms,
                            "data": {
                                "primary_domain": analysis.get("primary_domain", ""),
                                "sub_domain": analysis.get("sub_domain", "general"),
                                "relevant_patterns": analysis.get("relevant_patterns", []),
                                "complexity": analysis.get("complexity", "medium"),
                                "confidence": analysis.get("confidence", 0)
                            }
                        })

                if "prompt_engineer" in chunk:
                    final_state = chunk["prompt_engineer"]
                    yield sse_format("agent_update", {
                        "agent": "engineer",
                        "state": "complete",
                        "latency_ms": final_state.get("latency_ms", 0),
                        "data": {
                            "quality_score": final_state.get("quality_score", {}),
                            "agents_run": final_state.get("agents_run", []),
                            "agents_skipped": final_state.get("agents_skipped", [])
                        }
                    })

            previous_prompt = ""
            for turn in reversed(history):
                if turn.get("improved_prompt"):
                    previous_prompt = turn["improved_prompt"]
                    break
            if not previous_prompt:
                previous_prompt = req.message

            improved = final_state.get("improved_prompt", "")
            from service import compute_diff
            diff = compute_diff(previous_prompt, improved) if improved else []

            # Word-by-word streaming (natural cadence, ~6x fewer SSE events)
            words = reply.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield sse_format("kira_message", {"message": chunk, "complete": False})
                await asyncio.sleep(0.02)

            yield sse_format("kira_message", {"message": "", "complete": True})

            yield sse_format("result", {
                "type": "prompt_improved",
                "reply": reply,
                "improved_prompt": improved,
                "diff": diff,
                "quality_score": final_state.get("quality_score") or {"specificity": 4, "clarity": 4, "actionability": 4},
                "kira_message": reply,
                "memories_applied": final_state.get("memories_applied", 0),
                "latency_ms": final_state.get("latency_ms", 0),
                "agents_run": final_state.get("agents_run", [])
            })
            yield sse_format("done", {"message": "Complete"})

            save_request(
                raw_prompt=req.message, improved_prompt=improved,
                session_id=req.session_id, user_id=user.user_id,
                quality_score=final_state.get("quality_score"),
                domain_analysis=final_state.get("domain_analysis"),
                agents_used=final_state.get("agents_run"),
                agents_skipped=final_state.get("agents_skipped"),
                prompt_diff=diff
            )
            update_session_activity(user.user_id, req.session_id)

            # ═══ BACKGROUND TASK: Store in Memory Palace ═══
            background_tasks.add_task(
                write_to_langmem,
                user_id=user.user_id,
                session_result=final_state
            )

            # Trigger profile update if threshold reached
            interaction_count = get_conversation_count(req.session_id)
            last_activity = get_last_activity(user_id=user.user_id, session_id=req.session_id)
            if should_trigger_update(interaction_count, last_activity):
                background_tasks.add_task(
                    update_user_profile,
                    user_id=user.user_id,
                    session_data=final_state,
                    interaction_count=interaction_count,
                    last_activity=last_activity
                )

        except Exception as e:
            logger.exception(f"[api] /chat/stream error")
            yield sse_format("error", {"message": "Something went wrong"})
            yield sse_format("done", {"message": "Complete"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

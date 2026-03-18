# routes/prompts.py
# ─────────────────────────────────────────────
# Prompt Engineering Endpoints
#   POST /refine    → Single-shot, no memory
#   POST /chat      → Conversational with memory
#   POST /chat/stream → SSE streaming version
#
# RULES.md: <500 lines, type hints, docstrings, error handling
# ─────────────────────────────────────────────

import asyncio
import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from service import _run_swarm, _run_swarm_with_clarification, compute_diff, sse_format
from auth import User, get_current_user
from database import (
    save_request, save_agent_logs, save_conversation,
    get_conversation_history, update_session_activity, get_last_activity,
    get_conversation_count,
)
from agents.handlers.unified import kira_unified_handler
from memory import write_to_langmem, update_user_profile, should_trigger_update

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prompts"])


# ── Schemas ───────────────────────────────────

class RefineRequest(BaseModel):
    prompt:     str = Field(..., min_length=5, max_length=2000)
    session_id: Optional[str] = Field(default="default")


class RefineResponse(BaseModel):
    original_prompt: str
    improved_prompt: str
    breakdown:       dict[str, Any]
    session_id:      str


class ChatRequest(BaseModel):
    message:    str = Field(..., min_length=1, max_length=5000)
    session_id: str = Field(..., min_length=1)
    # Multimodal support
    input_modality: Optional[str] = "text"  # 'text' | 'file' | 'image' | 'voice'
    file_base64: Optional[str] = None  # Base64 encoded file content
    file_type: Optional[str] = None  # MIME type of the file


class ChatResponse(BaseModel):
    type:            str
    reply:           str
    improved_prompt: Optional[str]
    breakdown:       Optional[dict]
    session_id:      str


# ── Endpoints ─────────────────────────────────

@router.post("/refine", response_model=RefineResponse)
async def refine(req: RefineRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    """
    Single-shot prompt improvement. No memory.
    Requires JWT authentication.
    """
    logger.info(f"[api] /refine user_id={user.user_id} session={req.session_id} prompt='{req.prompt[:60]}'")
    try:
        final_state = _run_swarm(
            prompt=req.prompt,
            user_id=user.user_id,
            input_modality="text"
        )

        request_id = save_request(
            raw_prompt=final_state["message"],
            improved_prompt=final_state.get("improved_prompt", ""),
            session_id=req.session_id,
            user_id=user.user_id,
            quality_score=final_state.get("quality_score"),
            domain_analysis=final_state.get("domain_analysis"),
            agents_used=final_state.get("agents_run"),
            agents_skipped=final_state.get("agents_skipped")
        )
        if request_id:
            save_agent_logs(request_id, {
                "intent_agent":  final_state.get("intent_analysis", {}),
                "context_agent": final_state.get("context_analysis", {}),
                "domain_agent":  final_state.get("domain_analysis", {}),
            })

        # ═══ BACKGROUND TASK: Store in Memory Palace ═══
        background_tasks.add_task(
            write_to_langmem,
            user_id=user.user_id,
            session_result=final_state
        )

        return RefineResponse(
            original_prompt=final_state["message"],
            improved_prompt=final_state.get("improved_prompt", ""),
            breakdown={
                "intent":  final_state.get("intent_analysis", {}),
                "context": final_state.get("context_analysis", {}),
                "domain":  final_state.get("domain_analysis", {}),
            },
            session_id=req.session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] /refine error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Conversational endpoint with memory.
    Checks clarification loop FIRST, then classifies → routes → saves both turns.
    Requires JWT authentication.
    """
    logger.info(f"[api] /chat user_id={user.user_id} session={req.session_id} message='{req.message[:60]}'")

    try:
        # ═══ TRACK SESSION ACTIVITY ═══
        update_session_activity(user_id=user.user_id, session_id=req.session_id)
        last_activity = get_last_activity(user_id=user.user_id, session_id=req.session_id)

        # ═══ STEP 1: CHECK CLARIFICATION FLAG FIRST ═══
        from database import get_clarification_flag, save_clarification_flag

        pending_clarification, clarification_key = get_clarification_flag(
            session_id=req.session_id,
            user_id=user.user_id
        )
        
        if pending_clarification:
            logger.info(f"[api] clarification pending — injecting answer, firing swarm")
            
            final_state = _run_swarm_with_clarification(
                message=req.message,
                clarification_key=clarification_key,
                user_id=user.user_id,
                session_id=req.session_id
            )
            
            save_clarification_flag(
                session_id=req.session_id,
                user_id=user.user_id,
                pending=False,
                clarification_key=None
            )
            
            improved = final_state.get("improved_prompt", "")
            return ChatResponse(
                type="clarification_resolved",
                reply="Perfect — here's your engineered prompt.",
                improved_prompt=improved,
                breakdown=final_state.get("breakdown"),
                session_id=req.session_id
            )
        
        # ═══ STEP 2: NORMAL FLOW ═══
        history = get_conversation_history(req.session_id, limit=6)
        logger.info(f"[api] loaded {len(history)} history turns")
        
        from database import get_user_profile
        user_profile = get_user_profile(user.user_id) or {}
        user_profile["user_id"] = user.user_id

        # ═══ UNIFIED HANDLER ═══
        result = kira_unified_handler(
            message=req.message,
            history=history,
            user_profile=user_profile
        )

        intent = result["intent"]
        reply = result["response"]
        confidence = result.get("confidence", 0.5)
        clarification_needed = result.get("clarification_needed", False)

        if confidence < 0.5 and not clarification_needed:
            logger.info(f"[api] low confidence ({confidence:.2f}) → auto-requesting clarification")
            clarification_needed = True

        if intent == "CONVERSATION":
            save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="conversation", user_id=user.user_id)
            save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="conversation", user_id=user.user_id)
            return ChatResponse(type="conversation", reply=reply, improved_prompt=None, breakdown=None, session_id=req.session_id)

        elif intent == "FOLLOWUP":
            improved = result.get("improved_prompt", "")
            save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="followup", user_id=user.user_id)
            save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="followup_refined", improved_prompt=improved, user_id=user.user_id)
            return ChatResponse(type="followup_refined", reply=reply, improved_prompt=improved, breakdown=None, session_id=req.session_id)

        # Fall through to NEW_PROMPT
        classification = "NEW_PROMPT"

        if classification == "NEW_PROMPT":
            if clarification_needed:
                clarification_key = "topic"
                user_facing_message = reply

                save_clarification_flag(
                    session_id=req.session_id,
                    user_id=user.user_id,
                    pending=True,
                    clarification_key=clarification_key
                )

                save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="new_prompt", user_id=user.user_id)
                save_conversation(session_id=req.session_id, role="assistant", message=user_facing_message, message_type="clarification_question", user_id=user.user_id)

                logger.info(f"[api] clarification requested (confidence={confidence:.2f}): key={clarification_key}")
                return ChatResponse(type="clarification_requested", reply=user_facing_message, improved_prompt=None, breakdown=None, session_id=req.session_id)

            # Normal flow
            final_state = _run_swarm(
                prompt=req.message,
                user_id=user.user_id,
                input_modality=req.input_modality or "text",
                file_base64=req.file_base64,
                file_type=req.file_type
            )
            improved = final_state.get("improved_prompt", "")
            breakdown = {
                "intent":  final_state.get("intent_analysis", {}),
                "context": final_state.get("context_analysis", {}),
                "domain":  final_state.get("domain_analysis", {}),
            }
            reply = "Here's your supercharged prompt 🚀\n\nWant me to refine it further, make it more specific, or try a different angle?"
            save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="new_prompt", user_id=user.user_id)
            save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="prompt_improved", improved_prompt=improved, user_id=user.user_id)
            
            save_request(
                raw_prompt=req.message, 
                improved_prompt=improved, 
                session_id=req.session_id, 
                user_id=user.user_id,
                quality_score=final_state.get("quality_score"),
                domain_analysis=final_state.get("domain_analysis"),
                agents_used=final_state.get("agents_run"),
                agents_skipped=final_state.get("agents_skipped")
            )
            
            background_tasks.add_task(
                write_to_langmem,
                user_id=user.user_id,
                session_result=final_state
            )
            
            interaction_count = get_conversation_count(req.session_id)
            if should_trigger_update(interaction_count, last_activity):
                background_tasks.add_task(
                    update_user_profile,
                    user_id=user.user_id,
                    session_data=final_state,
                    interaction_count=interaction_count,
                    last_activity=last_activity
                )
            
            return ChatResponse(type="prompt_improved", reply=reply, improved_prompt=improved, breakdown=breakdown, session_id=req.session_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] /chat error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
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

            result = await loop.run_in_executor(
                None,
                lambda: kira_unified_handler(
                    message=req.message,
                    history=history,
                    user_profile=user_profile
                )
            )
            
            intent = result["intent"]
            reply = result["response"]
            confidence = result.get("confidence", 0.5)
            clarification_needed = result.get("clarification_needed", False)
            memories_applied = result.get("memories_applied", 0)
            latency_ms = result.get("latency_ms", 0)
            
            logger.info(f"[api] unified handler complete: intent={intent}, memories={memories_applied}, latency={latency_ms}ms")

            if intent in ["CONVERSATION", "FOLLOWUP"]:
                for i, char in enumerate(reply):
                    yield sse_format("kira_message", {"message": char, "complete": False})
                    if i % 10 == 0:
                        await asyncio.sleep(0.01)
            
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
            yield sse_format("status", {"message": "Analyzing intent..."})
            await asyncio.sleep(0.2)
            yield sse_format("status", {"message": "Extracting context..."})
            await asyncio.sleep(0.2)
            yield sse_format("status", {"message": "Identifying domain..."})
            await asyncio.sleep(0.2)
            yield sse_format("status", {"message": "Engineering your prompt..."})

            final_state = await loop.run_in_executor(
                None, _run_swarm, req.message, user.user_id, req.input_modality or "text", req.file_base64, req.file_type
            )

            previous_prompt = ""
            for turn in reversed(history):
                if turn.get("improved_prompt"):
                    previous_prompt = turn["improved_prompt"]
                    break
            if not previous_prompt:
                previous_prompt = req.message

            improved = final_state.get("improved_prompt", "")
            diff = compute_diff(previous_prompt, improved) if improved else []
            
            for i, char in enumerate(reply):
                yield sse_format("kira_message", {"message": char, "complete": False})
                if i % 10 == 0:
                    await asyncio.sleep(0.01)
                    
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

            from database import save_request, update_session_activity, get_conversation_count, get_last_activity
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
            logger.error(f"[api] /chat/stream error: {e}", exc_info=True)
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

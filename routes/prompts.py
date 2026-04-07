# routes/prompts.py
# ─────────────────────────────────────────────
# Prompt Engineering Endpoints
#   POST /refine    → Single-shot, no memory
#   POST /chat      → Conversational with memory
#
# RULES.md: <500 lines, type hints, docstrings, error handling
# ─────────────────────────────────────────────

import logging
import time
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from service import _run_swarm, _run_swarm_with_clarification
from auth import User, get_current_user
from database import (
    save_request, save_agent_logs, save_conversation,
    get_conversation_history, update_session_activity, get_last_activity,
    get_conversation_count, update_user_xp
)
from agents.handlers.unified import kira_unified_handler
from memory import write_to_langmem, update_user_profile, should_trigger_update
from xp_engine import calculate_forge_xp, get_tier_from_xp

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prompts"])


def award_forge_xp(
    user_id: str,
    domain_analysis: dict,
    quality_score: dict,
    user_profile: dict,
    is_clarification_resolved: bool = False,
) -> None:
    """
    Background task: calculate and award XP for prompt engineering.
    Wraps xp_engine.calculate_forge_xp and persists to database.
    """
    try:
        from xp_engine import calculate_forge_xp, get_tier_from_xp
        from database import update_user_xp, save_user_profile

        domain = domain_analysis.get("primary_domain", "general")
        dominant_domains = user_profile.get("dominant_domains", [])
        current_xp = user_profile.get("xp_total", 0)

        xp_result = calculate_forge_xp(
            quality_score=quality_score or {"overall": 3.0},
            domain=domain,
            user_dominant_domains=dominant_domains,
            current_streak=0,  # Streak tracking would need additional state
            is_clarification_resolved=is_clarification_resolved,
        )

        earned = xp_result.get("earned_xp", 0)
        if earned > 0:
            new_tier = get_tier_from_xp(current_xp + earned)
            update_user_xp(user_id, earned, new_tier)
            logger.info(f"[xp] awarded {earned} XP to user {user_id[:8]}... (tier: {new_tier})")

    except Exception as e:
        logger.error(f"[xp] award_forge_xp failed: {e}")


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
        raise HTTPException(status_code=500, detail="Internal server error")


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
            
            # ═══ BACKGROUND TASK: Award XP ═══
            background_tasks.add_task(
                award_forge_xp,
                user_id=user.user_id,
                domain_analysis=final_state.get("domain_analysis", {}),
                quality_score=final_state.get("quality_score", {}),
                user_profile=user_profile,
                is_clarification_resolved=False
            )
            
            interaction_count = get_conversation_count(req.session_id)
            if should_trigger_update(user.user_id, interaction_count):
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
        raise HTTPException(status_code=500, detail="Internal server error")

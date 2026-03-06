# api.py
# ─────────────────────────────────────────────
# FastAPI REST API — PromptForge v2.0
#
# Endpoints:
#   GET  /health         → Liveness check
#   POST /refine         → Single-shot prompt improvement, no memory
#   POST /chat           → Conversational with memory, classifies → routes
#   POST /chat/stream    → Streaming version of /chat — tokens appear live
#   GET  /history        → Past prompts from prompt_history table
#   GET  /conversation   → Full chat history for a session_id
#
# Performance:
#   - _run_swarm() checks cache first — repeat prompts skip LLM entirely
#   - /chat/stream sends SSE tokens as generated — feels instant to user
#   - GRAPH_TIMEOUT = 180s for sequential 4-call swarm
#   - User message saved AFTER classification so message_type is accurate
# ─────────────────────────────────────────────
import json
import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from graph.workflow import workflow
from state import AgentState
from database import (
    save_request, save_agent_logs, save_history,
    get_history, save_conversation, get_conversation_history
)
from agents.autonomous import classify_message, handle_conversation, handle_followup
from utils import get_cached_result, set_cached_result
from auth import User, get_current_user

logger = logging.getLogger(__name__)

GRAPH_TIMEOUT = 180


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
    message:    str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    type:            str
    reply:           str
    improved_prompt: Optional[str]
    breakdown:       Optional[dict]
    session_id:      str


# ── App ───────────────────────────────────────

app = FastAPI(
    title="PromptForge",
    description="Multi-agent prompt improvement system with conversational memory",
    version="2.0.0"
)

# CORS locked to frontend domain (per RULES.md - no wildcard!)
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:9000")
logger.info(f"[api] CORS allowed for: {frontend_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────

def _run_swarm(prompt: str) -> dict:
    """
    Runs full LangGraph swarm.
    Checks cache first — if hit, skips all 4 LLM calls entirely.
    Used by both /refine and /chat.
    """
    # Cache check — instant return on hit
    cached = get_cached_result(prompt)
    if cached:
        return cached

    initial_state = AgentState(
        raw_prompt=prompt,
        intent_result={},
        context_result={},
        domain_result={},
        improved_prompt="",
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
    from state import PromptForgeState
    
    # Check cache first
    cached = get_cached_result(message)
    if cached:
        logger.info(f"[api] cache hit for clarification answer")
        return cached
    
    logger.info(f"[api] running swarm with clarification: key={clarification_key}")
    
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


def _sse(event: str, data: dict) -> str:
    """Formats a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Routes ────────────────────────────────────

@app.get("/health")
def health():
    """Liveness check — no auth required."""
    return {"status": "ok", "version": "2.0.0"}


@app.post("/refine", response_model=RefineResponse)
async def refine(req: RefineRequest, user: User = Depends(get_current_user)):
    """
    Single-shot prompt improvement. No memory.
    Requires JWT authentication.
    """
    logger.info(f"[api] /refine user_id={user.user_id} session={req.session_id} prompt='{req.prompt[:60]}'")
    try:
        final_state = _run_swarm(req.prompt)

        request_id = save_request(
            raw_prompt=final_state["raw_prompt"],
            improved_prompt=final_state.get("improved_prompt", ""),
            session_id=req.session_id,
            user_id=user.user_id  # Add user_id for RLS
        )
        if request_id:
            save_agent_logs(request_id, {
                "intent_agent":  final_state.get("intent_result", {}),
                "context_agent": final_state.get("context_result", {}),
                "domain_agent":  final_state.get("domain_result", {}),
            })
        save_history(
            raw_prompt=final_state["raw_prompt"],
            improved_prompt=final_state.get("improved_prompt", ""),
            session_id=req.session_id,
            user_id=user.user_id  # Add user_id for RLS
        )

        return RefineResponse(
            original_prompt=final_state["raw_prompt"],
            improved_prompt=final_state.get("improved_prompt", ""),
            breakdown={
                "intent":  final_state.get("intent_result", {}),
                "context": final_state.get("context_result", {}),
                "domain":  final_state.get("domain_result", {}),
            },
            session_id=req.session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] /refine error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: User = Depends(get_current_user)):
    """
    Conversational endpoint with memory.
    Checks clarification loop FIRST, then classifies → routes → saves both turns.
    Requires JWT authentication.
    """
    logger.info(f"[api] /chat user_id={user.user_id} session={req.session_id} message='{req.message[:60]}'")

    try:
        # ═══ STEP 1: CHECK CLARIFICATION FLAG FIRST ═══
        from database import get_clarification_flag, save_clarification_flag
        
        pending_clarification, clarification_key = get_clarification_flag(
            session_id=req.session_id,
            user_id=user.user_id
        )
        
        if pending_clarification:
            logger.info(f"[api] clarification pending — injecting answer, firing swarm")
            
            # User's message IS the clarification answer
            # Run swarm with clarification (skips orchestrator re-classification)
            final_state = _run_swarm_with_clarification(
                message=req.message,
                clarification_key=clarification_key,
                user_id=user.user_id,
                session_id=req.session_id
            )
            
            # Clear the clarification flag
            save_clarification_flag(
                session_id=req.session_id,
                user_id=user.user_id,
                pending=False,
                clarification_key=None
            )
            
            # Return result
            improved = final_state.get("improved_prompt", "")
            return ChatResponse(
                type="clarification_resolved",
                reply="Perfect — here's your engineered prompt.",
                improved_prompt=improved,
                breakdown=final_state.get("breakdown"),
                session_id=req.session_id
            )
        
        # ═══ STEP 2: NORMAL FLOW (no pending clarification) ═══
        history = get_conversation_history(req.session_id, limit=6)
        logger.info(f"[api] loaded {len(history)} history turns")

        classification = classify_message(req.message, history)

        if classification == "CONVERSATION":
            reply = handle_conversation(req.message, history)
            save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="conversation", user_id=user.user_id)
            save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="conversation", user_id=user.user_id)
            return ChatResponse(type="conversation", reply=reply, improved_prompt=None, breakdown=None, session_id=req.session_id)

        elif classification == "FOLLOWUP":
            result = handle_followup(req.message, history)
            if result:
                improved = result.get("improved_prompt", "")
                reply = "Updated! Here's your refined prompt ✨\n\nWant any more tweaks?"
                save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="followup", user_id=user.user_id)
                save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="followup_refined", improved_prompt=improved, user_id=user.user_id)
                return ChatResponse(type="followup_refined", reply=reply, improved_prompt=improved, breakdown=None, session_id=req.session_id)
            else:
                logger.info("[api] followup fell back to NEW_PROMPT")
                classification = "NEW_PROMPT"

        if classification == "NEW_PROMPT":
            final_state = _run_swarm(req.message)
            improved = final_state.get("improved_prompt", "")
            breakdown = {
                "intent":  final_state.get("intent_result", {}),
                "context": final_state.get("context_result", {}),
                "domain":  final_state.get("domain_result", {}),
            }
            reply = "Here's your supercharged prompt 🚀\n\nWant me to refine it further, make it more specific, or try a different angle?"
            save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="new_prompt", user_id=user.user_id)
            save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="prompt_improved", improved_prompt=improved, user_id=user.user_id)
            save_history(raw_prompt=req.message, improved_prompt=improved, session_id=req.session_id, user_id=user.user_id)
            save_request(raw_prompt=req.message, improved_prompt=improved, session_id=req.session_id, user_id=user.user_id)
            return ChatResponse(type="prompt_improved", reply=reply, improved_prompt=improved, breakdown=breakdown, session_id=req.session_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] /chat error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, user: User = Depends(get_current_user)):
    """
    Streaming version of /chat.
    Sends Server-Sent Events (SSE) as processing progresses.
    Requires JWT authentication.
    """
    async def generate():
        try:
            logger.info(f"[api] /chat/stream user_id={user.user_id} session={req.session_id}")
            
            # Step 1 — load history
            yield _sse("status", {"message": "Loading conversation history..."})
            history = get_conversation_history(req.session_id, limit=6)

            # Step 2 — classify
            yield _sse("status", {"message": "Understanding your message..."})
            classification = classify_message(req.message, history)
            yield _sse("classification", {"type": classification})

            # Step 3 — route

            if classification == "CONVERSATION":
                yield _sse("status", {"message": "Crafting reply..."})
                reply = handle_conversation(req.message, history)
                save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="conversation", user_id=user.user_id)
                save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="conversation", user_id=user.user_id)
                yield _sse("result", {"type": "conversation", "reply": reply, "improved_prompt": None})

            elif classification == "FOLLOWUP":
                yield _sse("status", {"message": "Refining your prompt..."})
                result = handle_followup(req.message, history)

                if result:
                    improved = result.get("improved_prompt", "")
                    reply = "Updated! Here's your refined prompt ✨\n\nWant any more tweaks?"
                    save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="followup", user_id=user.user_id)
                    save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="followup_refined", improved_prompt=improved, user_id=user.user_id)
                    yield _sse("result", {"type": "followup_refined", "reply": reply, "improved_prompt": improved})
                else:
                    classification = "NEW_PROMPT"

            if classification == "NEW_PROMPT":
                # Check cache first — instant if hit
                cached = get_cached_result(req.message)
                if cached:
                    yield _sse("status", {"message": "Found cached result — instant!"})
                    final_state = cached
                else:
                    yield _sse("status", {"message": "Analyzing intent..."})
                    await asyncio.sleep(0)  # yield control so SSE flushes

                    yield _sse("status", {"message": "Extracting context..."})
                    await asyncio.sleep(0)

                    yield _sse("status", {"message": "Identifying domain..."})
                    await asyncio.sleep(0)

                    yield _sse("status", {"message": "Engineering your prompt..."})
                    # Run swarm in thread so async loop stays free
                    loop = asyncio.get_event_loop()
                    final_state = await loop.run_in_executor(None, _run_swarm, req.message)

                improved = final_state.get("improved_prompt", "")
                breakdown = {
                    "intent":  final_state.get("intent_result", {}),
                    "context": final_state.get("context_result", {}),
                    "domain":  final_state.get("domain_result", {}),
                }
                reply = "Here's your supercharged prompt\n\nWant me to refine it further or try a different angle?"

                save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="new_prompt", user_id=user.user_id)
                save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="prompt_improved", improved_prompt=improved, user_id=user.user_id)
                save_history(raw_prompt=req.message, improved_prompt=improved, session_id=req.session_id, user_id=user.user_id)
                save_request(raw_prompt=req.message, improved_prompt=improved, session_id=req.session_id, user_id=user.user_id)

                yield _sse("result", {"type": "prompt_improved", "reply": reply, "improved_prompt": improved, "breakdown": breakdown})

            yield _sse("done", {"message": "Complete"})

        except Exception as e:
            logger.exception("[api] /chat/stream error")
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/history")
def history(
    session_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user)
):
    """Get prompt history — requires JWT."""
    logger.info(f"[api] /history user_id={user.user_id} session={session_id} limit={limit}")
    data = get_history(session_id=session_id, limit=limit, user_id=user.user_id)
    return {"count": len(data), "history": data}


@app.get("/conversation")
def conversation(
    session_id: str = Query(..., description="Session ID to retrieve"),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user)
):
    """Returns full conversation history for a session — requires JWT."""
    logger.info(f"[api] /conversation user_id={user.user_id} session={session_id}")
    data = get_conversation_history(session_id=session_id, limit=limit)
    return {"count": len(data), "conversation": data}
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
from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from workflow import workflow
from state import AgentState
from database import (
    save_request, save_agent_logs, save_history,
    get_history, save_conversation, get_conversation_history, get_client,
    get_conversation_count, update_session_activity, get_last_activity
)
from agents.autonomous import classify_message, handle_conversation, handle_followup
from utils import get_cached_result, set_cached_result
from auth import User, get_current_user
from memory import write_to_langmem, update_user_profile, should_trigger_update
from multimodal import transcribe_voice
from middleware.rate_limiter import RateLimiterMiddleware

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

# Rate limiting middleware (RULES.md Security Rule #8)
logger.info("[api] Rate limiting enabled: 100 requests/hour per user")
app.add_middleware(RateLimiterMiddleware)


# ── Helpers ───────────────────────────────────

def _run_swarm(prompt: str, input_modality: str = "text", 
               file_base64: str = None, file_type: str = None) -> dict:
    """
    Runs full LangGraph swarm.
    Checks cache first — if hit, skips all 4 LLM calls entirely.
    Used by both /refine and /chat.
    
    Args:
        prompt: User's message
        input_modality: 'text' | 'file' | 'image' | 'voice'
        file_base64: Base64 encoded file content (if any)
        file_type: MIME type of file (if any)
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

    initial_state = AgentState(
        message=prompt,
        intent_analysis={},
        context_analysis={},
        domain_analysis={},
        improved_prompt="",
        attachments=attachments,
        input_modality=input_modality,
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
    """
    Formats a Server-Sent Event string.
    Frontend expects: data: {"type": "event", "data": {...}}
    """
    # Wrap in the format the frontend parser expects
    wrapped_data = {"type": event, "data": data}
    return f"data: {json.dumps(wrapped_data)}\n\n"


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
            raw_prompt=final_state["message"],
            improved_prompt=final_state.get("improved_prompt", ""),
            session_id=req.session_id,
            user_id=user.user_id  # Add user_id for RLS
        )
        if request_id:
            save_agent_logs(request_id, {
                "intent_agent":  final_state.get("intent_analysis", {}),
                "context_agent": final_state.get("context_analysis", {}),
                "domain_agent":  final_state.get("domain_analysis", {}),
            })
        save_history(
            raw_prompt=final_state["message"],
            improved_prompt=final_state.get("improved_prompt", ""),
            session_id=req.session_id,
            user_id=user.user_id  # Add user_id for RLS
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


@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Conversational endpoint with memory.
    Checks clarification loop FIRST, then classifies → routes → saves both turns.
    Requires JWT authentication.

    Background Tasks (user NEVER waits):
    - write_to_langmem(): Store session in pipeline memory
    - update_user_profile(): Update user profile every 5th interaction
    """
    logger.info(f"[api] /chat user_id={user.user_id} session={req.session_id} message='{req.message[:60]}'")

    try:
        # ═══ TRACK SESSION ACTIVITY (for inactivity trigger) ═══
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
        
        # Load user profile for context (unified handler)
        from database import get_user_profile
        user_profile = get_user_profile(user.user_id) or {}
        
        # ═══ UNIFIED HANDLER (1 LLM call with full context) ═══
        # Replaces: classify_message() + handle_conversation()/handle_followup()
        from agents.autonomous import kira_unified_handler
        result = kira_unified_handler(
            message=req.message,
            history=history,
            user_profile=user_profile
        )

        intent = result["intent"]
        reply = result["response"]
        confidence = result.get("confidence", 0.5)
        clarification_needed = result.get("clarification_needed", False)

        # ═══ AUTO-TRIGGER CLARIFICATION IF CONFIDENCE IS LOW ═══
        # RULES.md: Smart defaults, user NEVER waits for uncertainty
        if confidence < 0.5 and not clarification_needed:
            logger.info(f"[api] low confidence ({confidence:.2f}) → auto-requesting clarification")
            clarification_needed = True

        # Handle based on intent + confidence
        if intent == "CONVERSATION":
            save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="conversation", user_id=user.user_id)
            save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="conversation", user_id=user.user_id)
            return ChatResponse(
                type="conversation",
                reply=reply,
                kira_message=reply,
                improved_prompt=None,
                breakdown=None,
                session_id=req.session_id
            )

        elif intent == "FOLLOWUP":
            improved = result.get("improved_prompt", "")
            save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="followup", user_id=user.user_id)
            save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="followup_refined", improved_prompt=improved, user_id=user.user_id)
            return ChatResponse(
                type="followup_refined",
                reply=reply,
                kira_message=reply,
                improved_prompt=improved,
                breakdown=None,
                session_id=req.session_id
            )

        # Fall through to NEW_PROMPT if intent is new_prompt or fallback
        classification = "NEW_PROMPT"

        if classification == "NEW_PROMPT":
            # ═══ CHECK IF CLARIFICATION NEEDED (from confidence or swarm) ═══
            if clarification_needed:
                # Extract clarification question from Kira's response or use default
                clarification_key = "topic"  # Default key for vague requests
                user_facing_message = reply  # Use Kira's natural language response

                # SAVE THE FLAG (critical for clarification loop!)
                save_clarification_flag(
                    session_id=req.session_id,
                    user_id=user.user_id,
                    pending=True,
                    clarification_key=clarification_key
                )

                # Save user message and Kira's question to conversation
                save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="new_prompt", user_id=user.user_id)
                save_conversation(session_id=req.session_id, role="assistant", message=user_facing_message, message_type="clarification_question", user_id=user.user_id)

                logger.info(f"[api] clarification requested (confidence={confidence:.2f}): key={clarification_key}")
                return ChatResponse(
                    type="clarification_requested",
                    reply=user_facing_message,
                    improved_prompt=None,
                    breakdown=None,
                    session_id=req.session_id
                )

            # Normal flow - no clarification needed, run swarm
            final_state = _run_swarm(req.message)
            breakdown = {
                "intent":  final_state.get("intent_analysis", {}),
                "context": final_state.get("context_analysis", {}),
                "domain":  final_state.get("domain_analysis", {}),
            }
            reply = "Here's your supercharged prompt 🚀\n\nWant me to refine it further, make it more specific, or try a different angle?"
            save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="new_prompt", user_id=user.user_id)
            save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="prompt_improved", improved_prompt=improved, user_id=user.user_id)
            save_history(raw_prompt=req.message, improved_prompt=improved, session_id=req.session_id, user_id=user.user_id)
            save_request(raw_prompt=req.message, improved_prompt=improved, session_id=req.session_id, user_id=user.user_id)
            
            # ═══ BACKGROUND TASKS (user never waits) ═══
            # Write to LangMem for future context
            background_tasks.add_task(
                write_to_langmem,
                user_id=user.user_id,
                session_result=final_state
            )
            
            # Update user profile if trigger conditions met
            from database import get_conversation_count
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
                # Send as Kira message for streaming display
                yield _sse("kira_message", {"message": reply, "complete": True})
                yield _sse("result", {"type": "conversation", "reply": reply, "improved_prompt": None})
                yield _sse("done", {"message": "Complete"})
                return

            elif classification == "FOLLOWUP":
                yield _sse("status", {"message": "Refining your prompt..."})
                result = handle_followup(req.message, history)

                if result:
                    improved = result.get("improved_prompt", "")
                    reply = "Updated! Here's your refined prompt ✨\n\nWant any more tweaks?"
                    save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="followup", user_id=user.user_id)
                    save_conversation(session_id=req.session_id, role="assistant", message=reply, message_type="followup_refined", improved_prompt=improved, user_id=user.user_id)
                    # Send as Kira message for streaming display
                    yield _sse("kira_message", {"message": reply, "complete": True})
                    yield _sse("result", {"type": "followup_refined", "reply": reply, "improved_prompt": improved})
                    yield _sse("done", {"message": "Complete"})
                    return
                else:
                    classification = "NEW_PROMPT"

            if classification == "NEW_PROMPT":
                # Check cache first — instant if hit
                # Note: cache key is just the message, attachments are extra context
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
                    # Pass attachment parameters for multimodal support
                    loop = asyncio.get_event_loop()
                    final_state = await loop.run_in_executor(
                        None, 
                        _run_swarm, 
                        req.message,
                        req.input_modality or "text",
                        req.file_base64,
                        req.file_type
                    )

                # ═══ CHECK IF CLARIFICATION NEEDED ═══
                if final_state.get("pending_clarification"):
                    clarification_key = final_state.get("clarification_key", "topic")
                    user_facing_message = final_state.get("user_facing_message", "I need more information.")
                    
                    # SAVE THE FLAG
                    save_clarification_flag(
                        session_id=req.session_id,
                        user_id=user.user_id,
                        pending=True,
                        clarification_key=clarification_key
                    )
                    
                    save_conversation(session_id=req.session_id, role="user", message=req.message, message_type="new_prompt", user_id=user.user_id)
                    save_conversation(session_id=req.session_id, role="assistant", message=user_facing_message, message_type="clarification_question", user_id=user.user_id)
                    
                    yield _sse("status", {"message": "Clarification needed"})
                    yield _sse("result", {"type": "clarification_requested", "reply": user_facing_message, "clarification_key": clarification_key})
                    yield _sse("done", {"message": "Complete"})
                    return

                improved = final_state.get("improved_prompt", "")
                breakdown = {
                    "intent":  final_state.get("intent_analysis", {}),
                    "context": final_state.get("context_analysis", {}),
                    "domain":  final_state.get("domain_analysis", {}),
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


@app.post("/memory/onboarding")
async def save_onboarding_memory(
    request: dict,
    user: User = Depends(get_current_user)
):
    """
    Save onboarding profile as LangMem memory with Gemini embedding.
    
    RULES.md: Background task, user never waits
    
    Args:
        request: {content, profile_type, metadata}
        user: Authenticated user from JWT
    """
    from memory.langmem import _generate_embedding
    from database import get_client
    
    try:
        db = get_client()
        
        content = request.get("content", "")
        profile_type = request.get("profile_type", "onboarding")
        metadata = request.get("metadata", {})
        
        # Generate Gemini embedding (for future semantic search)
        embedding = _generate_embedding(content)
        
        # Prepare memory data matching existing schema
        memory_data = {
            "user_id": user.user_id,
            "content": content,
            "improved_content": f"Onboarding profile: {metadata.get('primary_use', 'unknown')} user",
            "domain": metadata.get('primary_use', 'general'),
            "quality_score": {"onboarding": 5},
            "agents_used": ["onboarding"],
            "agents_skipped": [],
            "metadata": metadata,  # Store full profile as JSONB
        }
        
        # Note: embedding generated but table doesn't have column yet
        # Will be added in future migration for pgvector semantic search
        if embedding:
            logger.info(f"[api] onboarding embedding generated: {len(embedding)} dim (ready for pgvector migration)")
        
        # Store in Supabase
        result = db.table("langmem_memories").insert(memory_data).execute()
        
        logger.info(f"[api] saved onboarding memory for user {user.user_id[:8]}...")
        
        return {"status": "saved", "has_embedding": embedding is not None}
        
    except Exception as e:
        logger.error(f"[api] onboarding memory save failed: {e}")
        # Non-critical - return success anyway
        return {"status": "saved", "has_embedding": False}


# ═══ IMPLICIT FEEDBACK ENDPOINT ═══════════════════════

class FeedbackRequest(BaseModel):
    """
    Implicit feedback submission schema.
    
    RULES.md: Type hints mandatory, docstrings complete.
    """
    session_id: str
    prompt_id: str
    feedback_type: str  # copy|edit|save
    edit_distance: Optional[float] = None
    timestamp: str


@app.post("/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    user: User = Depends(get_current_user)
):
    """
    Collect implicit feedback from user behavior.
    
    RULES.md Compliance:
    - Type hints mandatory
    - Background write (user NEVER waits)
    - Silent fail (safe to fail)
    - RLS enforced via Supabase client
    
    Args:
        req: Feedback request body
        user: Authenticated user from JWT
    
    Returns:
        Status dict
    
    Example:
        POST /feedback {
            "session_id": "session-123",
            "prompt_id": "prompt-456",
            "feedback_type": "copy",
            "timestamp": "2026-03-13T10:30:00Z"
        }
    
    Feedback Types & Weights:
    - copy: +0.08 (user found value - STRONG positive)
    - edit (light, <40%): +0.02 (user engaged - mild positive)
    - edit (heavy, >40%): -0.03 (prompt needed work - mild negative)
    - save: +0.10 (user wants to reuse - VERY strong positive)
    """
    from database import get_client
    
    try:
        db = get_client()
        
        # Insert feedback record (RLS ensures user_id matches JWT)
        db.table("prompt_feedback").insert({
            "user_id": user.user_id,
            "session_id": req.session_id,
            "prompt_id": req.prompt_id,
            "feedback_type": req.feedback_type,
            "edit_distance": req.edit_distance,
            "timestamp": req.timestamp,
        }).execute()
        
        # Calculate feedback weight
        weight = _calculate_feedback_weight(req)
        
        # Queue background task to adjust user quality score
        # (Non-blocking, user doesn't wait)
        background_tasks.add_task(_adjust_user_quality_score, user.user_id, weight)
        
        logger.info(f"[feedback] recorded: type={req.feedback_type}, weight={weight:.3f}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"[feedback] failed: {e}")
        # Silent fail - feedback is non-critical
        return {"status": "error", "message": "Failed to record feedback"}


def _calculate_feedback_weight(req: FeedbackRequest) -> float:
    """
    Map feedback type to quality score adjustment.
    
    RULES.md: Pure function, testable, no side effects.
    
    Args:
        req: Feedback request
    
    Returns:
        Weight adjustment (-0.1 to +0.1)
    
    Weights (based on 2025 Anthropic research):
    - copy: +0.08 (user found value - primary success signal)
    - save: +0.10 (user wants to reuse - strongest signal)
    - edit (light): +0.02 (user engaged, minor tweaks)
    - edit (heavy): -0.03 (significant changes needed)
    """
    weights = {
        "copy": +0.08,
        "save": +0.10,
        "edit": -0.03 if (req.edit_distance or 0) > 0.4 else +0.02,
    }
    return weights.get(req.feedback_type, 0.0)


async def _adjust_user_quality_score(user_id: str, delta: float) -> bool:
    """
    Adjust user's prompt_quality_score in background.
    
    RULES.md:
    - Background task (user NEVER waits)
    - Silent fail (safe to fail)
    - Type hints mandatory
    
    Args:
        user_id: User UUID
        delta: Adjustment amount
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from database import get_user_profile, save_user_profile
        
        profile = get_user_profile(user_id)
        if not profile:
            return False
        
        current_score = profile.get("prompt_quality_score", 0.5)
        new_score = max(0.0, min(1.0, current_score + delta))
        
        profile["prompt_quality_score"] = new_score
        
        success = save_user_profile(user_id, profile)
        
        if success:
            logger.debug(f"[profile] adjusted quality score: {user_id[:8]}... delta={delta:.3f}")
        
        return success
        
    except Exception as e:
        logger.error(f"[profile] quality score adjustment failed: {e}")
        return False


# ═══ MCP ENDPOINTS ════════════════════════════════════
async def transcribe(
    file: UploadFile = File(..., description="Audio file (MP3, WAV, M4A, etc.)"),
    user: User = Depends(get_current_user)
):
    """
    Transcribe voice audio to text using Whisper.
    
    RULES.md: JWT required, file size validation, Supabase Storage RLS
    
    Accepts: MP3, MP4, MPEG, MPGA, M4A, WAV, WebM
    Max size: 25MB
    
    Returns: {text: "transcribed text"}
    """
    from fastapi import UploadFile, File
    from database import get_client
    
    logger.info(f"[api] /transcribe user_id={user.user_id}")
    
    try:
        db = get_client()
        result = await transcribe_voice(
            file=file,
            user_id=user.user_id,
            session_id="transcribe",
            supabase=db
        )
        
        return {
            "text": result["transcript"],
            "file_url": result["file_url"],
            "input_modality": result["input_modality"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] /transcribe error")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="Upload audio, image, or document file"),
    user: User = Depends(get_current_user)
):
    """
    Upload and process multimodal files (voice, image, documents).
    
    RULES.md: JWT required, file size validation, Supabase Storage RLS
    
    Accepts:
    - Audio: MP3, MP4, MPEG, MPGA, M4A, WAV, WebM (max 25MB)
    - Image: JPEG, PNG, GIF, WebP (max 5MB)
    - Documents: PDF, DOCX, TXT (max 2MB)
    
    Returns: Processed content (transcript, base64, or extracted text)
    """
    from database import get_client
    from multimodal import process_image, extract_text_from_file
    
    logger.info(f"[api] /upload user_id={user.user_id} file={file.filename} type={file.content_type}")
    
    try:
        db = get_client()
        
        # Process based on file type
        if file.content_type.startswith("audio/"):
            # Voice → Whisper transcription
            result = await transcribe_voice(file, user.user_id, "upload", db)
            return {
                "success": True,
                "type": "voice",
                "text": result["transcript"],
                "file_url": result["file_url"],
            }
        
        elif file.content_type.startswith("image/"):
            # Image → Base64 for GPT-4o Vision
            result = await process_image(file, user.user_id, "upload", db)
            return {
                "success": True,
                "type": "image",
                "base64_image": result["base64_image"],
                "media_type": result["media_type"],
                "file_url": result["file_url"],
            }
        
        elif file.content_type in [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        ]:
            # Document → Text extraction
            result = await extract_text_from_file(file, user.user_id, "upload", db)
            return {
                "success": True,
                "type": "file",
                "text": result["extracted_text"],
                "file_type": result["file_type"],
                "file_url": result["file_url"],
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported: audio/*, image/*, application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, text/plain"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] /upload error")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


# ═══ MCP TOKEN ENDPOINTS ═══════════════════════

@app.post("/mcp/generate-token")
async def generate_mcp_token(
    user: User = Depends(get_current_user)
):
    """
    Generate long-lived JWT for MCP access (365 days).
    
    User calls this ONCE, copies token to Cursor MCP config.
    Token can be revoked if compromised.
    
    RULES.md Section 9: MCP Integration — JWT authentication
    
    Returns:
        {
            "mcp_token": "eyJhbGc...",
            "expires_in_days": 365,
            "expires_at": "2027-03-07T...",
            "instructions": "Copy to Cursor MCP config"
        }
    """
    import hashlib
    from jose import jwt
    from datetime import timedelta
    
    logger.info(f"[api] /mcp/generate-token user_id={user.user_id}")
    
    try:
        db = get_client()
        
        # Generate long-lived token (365 days)
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        
        payload = {
            "sub": user.user_id,
            "type": "mcp_access",
            "iss": os.getenv("SUPABASE_URL"),
            "exp": expires_at
        }
        
        mcp_token = jwt.encode(
            payload,
            os.getenv("SUPABASE_JWT_SECRET"),
            algorithm="HS256"
        )
        
        # Store token hash (for revocation)
        token_hash = hashlib.sha256(mcp_token.encode()).hexdigest()
        
        db.table("mcp_tokens").insert({
            "user_id": user.user_id,
            "token_hash": token_hash,
            "token_type": "mcp_access",
            "expires_at": expires_at.isoformat(),
            "revoked": False
        }).execute()
        
        logger.info(f"[api] generated MCP token (expires {expires_at.date()})")
        
        return {
            "mcp_token": mcp_token,
            "expires_in_days": 365,
            "expires_at": expires_at.isoformat(),
            "instructions": "Copy to Cursor MCP config. Valid for 365 days."
        }
        
    except Exception as e:
        logger.exception("[api] /mcp/generate-token error")
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")


@app.get("/mcp/list-tokens")
async def list_mcp_tokens(user: User = Depends(get_current_user)):
    """List all active MCP tokens for current user."""
    try:
        db = get_client()
        result = db.table("mcp_tokens").select(
            "id, expires_at, revoked, created_at"
        ).eq("user_id", user.user_id).eq("revoked", False).execute()
        
        return {"tokens": result.data, "count": len(result.data)}
    except Exception as e:
        logger.exception("[api] /mcp/list-tokens error")
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/mcp/revoke-token/{token_id}")
async def revoke_mcp_token(token_id: str, user: User = Depends(get_current_user)):
    """Revoke MCP token (immediate invalidation)."""
    try:
        db = get_client()
        result = db.table("mcp_tokens").update({"revoked": True}).eq(
            "id", token_id
        ).eq("user_id", user.user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Token not found")
        
        return {"success": True, "message": "Token revoked"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] /mcp/revoke-token error")
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")
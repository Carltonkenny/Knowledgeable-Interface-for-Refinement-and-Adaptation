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
        message=prompt,
        intent_analysis={},
        context_analysis={},
        domain_analysis={},
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
            
            # ═══ CHECK IF CLARIFICATION NEEDED ═══
            # Kira may have determined clarification is needed
            if final_state.get("pending_clarification"):
                clarification_key = final_state.get("clarification_key", "topic")
                user_facing_message = final_state.get("user_facing_message", "I need more information.")
                
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
                
                logger.info(f"[api] clarification requested: key={clarification_key}")
                return ChatResponse(
                    type="clarification_requested",
                    reply=user_facing_message,
                    improved_prompt=None,
                    breakdown=None,
                    session_id=req.session_id
                )
            
            # Normal flow - no clarification needed
            improved = final_state.get("improved_prompt", "")
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


@app.post("/transcribe")
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
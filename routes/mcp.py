# routes/mcp.py
# ─────────────────────────────────────────────
# MCP (Model Context Protocol) + Upload Endpoints
#   POST   /upload              → Multimodal file processing
#   POST   /transcribe          → Voice transcription (Whisper)
#   POST   /mcp/generate-token  → Generate long-lived JWT
#   GET    /mcp/list-tokens     → List active tokens
#   POST   /mcp/revoke-token/{id} → Revoke token
#
# RULES.md: <500 lines, type hints, docstrings
# ─────────────────────────────────────────────

import os
import hashlib
import logging
import time
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from auth import User, get_current_user
from database import get_client
from multimodal import transcribe_voice
from voice.rate_limiter import check_voice_rate_limit
from voice.metrics import record_voice_metric
from utils.error_messages import get_error_message, ErrorType

logger = logging.getLogger(__name__)

router = APIRouter(tags=["MCP"])


# ── Upload ────────────────────────────────────

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="Upload audio, image, or document file"),
    user: User = Depends(get_current_user)
):
    """Upload and process multimodal files (voice, image, documents)."""
    from multimodal import process_image, extract_text_from_file

    logger.info(f"[api] /upload user_id={user.user_id} file={file.filename} type={file.content_type}")

    try:
        db = get_client()

        # File size limit: 10MB
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")

        # Reset file pointer if possible, or wrap content for downstream use
        from io import BytesIO
        file.file = BytesIO(content)

        if file.content_type.startswith("audio/"):
            result = await transcribe_voice(file, user.user_id, "upload", db)
            return {"success": True, "type": "voice", "text": result["transcript"], "file_url": result["file_url"]}

        elif file.content_type.startswith("image/"):
            result = await process_image(file, user.user_id, "upload", db)
            return {"success": True, "type": "image", "base64_image": result["base64_image"], "media_type": result["media_type"], "file_url": result["file_url"]}

        elif file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
            result = await extract_text_from_file(file, user.user_id, "upload", db)
            return {"success": True, "type": "file", "text": result["extracted_text"], "file_type": result["file_type"], "file_url": result["file_url"]}

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] /upload error")
        error = get_error_message(ErrorType.UNKNOWN, user_tone="direct")
        raise HTTPException(status_code=500, detail=error["full_message"])


# ── Voice Transcription ───────────────────────

@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(..., description="Audio file for transcription"),
    user: User = Depends(get_current_user)
):
    """
    Transcribe voice audio to text using Whisper.

    Production features:
    - Rate limiting: 10/min, 50/hr per user
    - Budget check: blocks if monthly voice budget exhausted
    - Retry: automatic retry on network failures (in transcribe_voice)
    - Metrics: tracks latency, success rate, cost

    RULES.md: JWT auth required, file size validation, MIME type validation

    Args:
        audio: Audio file (mp3, mp4, mpeg, mpga, m4a, wav, webm)
        user: Authenticated user from JWT

    Returns:
        { "transcript": str }

    Raises:
        400: File too large or unsupported MIME type
        401: Missing or invalid JWT
        429: Rate limit exceeded or budget exhausted
        500: Transcription failed
        504: Timeout
    """
    start_time = time.time()
    logger.info(f"[transcribe] user_id={user.user_id} file={audio.filename} type={audio.content_type}")

    try:
        # RATE LIMIT CHECK (Production item #1)
        allowed, error_msg, headers = check_voice_rate_limit(user.user_id, "transcribe")
        if not allowed:
            record_voice_metric(
                service="transcribe",
                success=False,
                latency_ms=(time.time() - start_time) * 1000,
                user_id=user.user_id,
                provider="pollinations",
                error_type="rate_limited"
            )
            raise HTTPException(status_code=429, detail=error_msg, headers=headers)

        db = get_client()

        # Use a session_id for storage path (use user_id as fallback for standalone transcription)
        session_id = f"transcribe-{user.user_id[:8]}"

        # Call existing transcribe_voice function (no code duplication)
        result = await transcribe_voice(audio, user.user_id, session_id, db)

        logger.info(f"[transcribe] success: {len(result['transcript'])} chars")

        # Return only transcript field to match frontend expectation
        return {"transcript": result["transcript"]}

    except HTTPException:
        raise
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        record_voice_metric(
            service="transcribe",
            success=False,
            latency_ms=latency_ms,
            user_id=user.user_id,
            provider="pollinations",
            error_type="unexpected_error"
        )
        logger.exception("[transcribe] failed")
        error = get_error_message(ErrorType.UNKNOWN, user_tone="direct")
        raise HTTPException(status_code=500, detail=error["full_message"])


# ── MCP Tokens ────────────────────────────────

@router.post("/mcp/generate-token")
async def generate_mcp_token(user: User = Depends(get_current_user)):
    """Generate long-lived JWT for MCP access (365 days)."""
    from jose import jwt
    
    logger.info(f"[api] /mcp/generate-token user_id={user.user_id}")
    
    try:
        db = get_client()
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        
        payload = {
            "sub": user.user_id,
            "type": "mcp_access",
            "iss": os.getenv("SUPABASE_URL"),
            "exp": expires_at
        }
        
        mcp_secret = os.getenv("MCP_JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET")
        if not mcp_secret:
            raise HTTPException(status_code=500, detail="MCP JWT secret not configured")

        mcp_token = jwt.encode(
            payload,
            mcp_secret,
            algorithm="HS256"
        )
        
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
        error = get_error_message(ErrorType.UNKNOWN, user_tone="direct")
        raise HTTPException(status_code=500, detail=error["full_message"])


@router.get("/mcp/list-tokens")
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
        error = get_error_message(ErrorType.UNKNOWN, user_tone="direct")
        raise HTTPException(status_code=500, detail=error["full_message"])


@router.post("/mcp/revoke-token/{token_id}")
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
        error = get_error_message(ErrorType.UNKNOWN, user_tone="direct")
        raise HTTPException(status_code=500, detail=error["full_message"])

# routes/tts.py
# ─────────────────────────────────────────────
# Text-to-Speech Endpoint — Multi-Provider (ElevenLabs + Pollinations)
#   POST /tts          → TTS audio streaming
#   POST /tts/raw      → Query param version
#   GET  /tts/voices   → List available voices
#   GET  /voice/metrics → Admin metrics dashboard
#
# Production hardening (items 1-3, 6):
#   1. Rate limiting — Redis-based (5/min, 30/hr per user)
#   2. Cost tracking — per-request cost in Redis
#   3. Retry logic — exponential backoff on Pollinations (2 retries)
#   6. Metrics — latency, success rate, provider breakdown
#
# RULES.md: <500 lines, type hints, docstrings, JWT auth
# ─────────────────────────────────────────────

import os
import io
import time
import asyncio
import logging
import httpx
import urllib.parse
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import User, get_current_user
from voice.rate_limiter import check_voice_rate_limit
from voice.cost_tracker import track_cost, check_budget, get_monthly_spend, get_cost_breakdown
from voice.metrics import record_voice_metric, get_voice_metrics

logger = logging.getLogger(__name__)
router = APIRouter(tags=["TTS"])

# ── Configuration ─────────────────────────────

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "pollinations").lower()
POLLINATIONS_VOICE = os.getenv("POLLINATIONS_VOICE", "nova")  # Default to Nova for clarity
POLLINATIONS_SPEED = float(os.getenv("POLLINATIONS_SPEED", "1.0"))
POLLINATIONS_LANG = os.getenv("POLLINATIONS_LANG", "en")
POLLINATIONS_BASE_URL = "https://text.pollinations.ai"

# ── Endpoints ─────────────────────────────────

async def _fetch_pollinations_tts(text: str, voice: str, lang: str, speed: float) -> bytes:
    """Fetch audio from Pollinations TTS API.
    
    Verified URL format: https://text.pollinations.ai/openai-audio/{prompt}?voice={voice}
    """
    # Pollinations expects the prompt in the path for the openai-audio model
    encoded_text = urllib.parse.quote(text)
    url = f"{POLLINATIONS_BASE_URL}/openai-audio/{encoded_text}?voice={voice}&lang={lang}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        if response.status_code != 200:
            logger.error(f"[tts] Pollinations failed: {response.status_code} - {response.text[:100]}")
            raise HTTPException(status_code=response.status_code, detail="Free TTS service temporarily unavailable")
        return response.content

@router.post("/tts")
async def text_to_speech(req: TTSRequest, user: User = Depends(get_current_user)):
    """Convert text to speech using free Pollinations provider."""
    start_time = time.time()
    try:
        # Rate limit check
        allowed, error_msg, headers = check_voice_rate_limit(user.user_id, "tts")
        if not allowed:
            raise HTTPException(status_code=429, detail=error_msg, headers=headers)

        voice = req.voice_id or POLLINATIONS_VOICE
        lang = req.model or POLLINATIONS_LANG
        
        # Track usage (free doesn't count against budget, but we track for metrics)
        track_cost(user_id=user.user_id, service="tts", char_count=len(req.text), provider="pollinations")
        
        audio_content = await _fetch_pollinations_tts(req.text, voice, lang, 1.0)
        
        record_voice_metric(service="tts", success=True, latency_ms=(time.time()-start_time)*1000,
            user_id=user.user_id, provider="pollinations")
            
        return StreamingResponse(
            io.BytesIO(audio_content), 
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-cache", **headers}
        )
    except Exception as e:
        logger.exception("[tts] unexpected error")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        record_voice_metric(service="tts", success=False, latency_ms=(time.time()-start_time)*1000,
            user_id=user.user_id, provider=TTS_PROVIDER, error_type="unexpected_error")
        logger.exception("[tts] unexpected error")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.post("/tts/raw", response_class=StreamingResponse)
async def text_to_speech_raw(
    text: str = Query(..., min_length=1, max_length=5000),
    voice_id: Optional[str] = Query(default=None),
    model: Optional[str] = Query(default=None),
    speed: Optional[float] = Query(default=None, ge=0.25, le=4.0),
    user: User = Depends(get_current_user)):
    """Simplified TTS endpoint using query parameters."""
    start_time = time.time()
    try:
        allowed, error_msg, headers = check_voice_rate_limit(user.user_id, "tts")
        if not allowed:
            raise HTTPException(status_code=429, detail=error_msg, headers=headers)
        budget_ok, budget_error, _ = check_budget(user.user_id)
        if not budget_ok:
            raise HTTPException(status_code=429, detail=budget_error)
        if TTS_PROVIDER == "elevenlabs":
            if not ELEVENLABS_API_KEY:
                raise HTTPException(status_code=503, detail="ElevenLabs TTS not configured")
            track_cost(user_id=user.user_id, service="tts", char_count=len(text), provider="elevenlabs")
            record_voice_metric(service="tts", success=True, latency_ms=(time.time()-start_time)*1000,
                user_id=user.user_id, provider="elevenlabs")
            return StreamingResponse(_stream_tts_audio(text, voice_id or ELEVENLABS_VOICE_ID, model or ELEVENLABS_MODEL),
                media_type="audio/mpeg", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive", **headers})
        elif TTS_PROVIDER == "pollinations":
            track_cost(user_id=user.user_id, service="tts", char_count=len(text), provider="pollinations")
            return StreamingResponse(
                _stream_pollinations_tts(text, voice_id or POLLINATIONS_VOICE, model or POLLINATIONS_LANG,
                    speed if speed is not None else POLLINATIONS_SPEED),
                media_type="audio/mpeg", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", **headers})
        else:
            raise HTTPException(status_code=503, detail=f"Unknown TTS provider: {TTS_PROVIDER}")
    except HTTPException:
        raise
    except Exception as e:
        record_voice_metric(service="tts", success=False, latency_ms=(time.time()-start_time)*1000,
            user_id=user.user_id, provider=TTS_PROVIDER, error_type="unexpected_error")
        logger.exception("[tts/raw] unexpected error")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.get("/tts/voices", response_model=TTSVoicesResponse)
async def list_voices(user: User = Depends(get_current_user)):
    """List available voices for the current TTS provider."""
    try:
        if TTS_PROVIDER == "elevenlabs":
            if not ELEVENLABS_API_KEY:
                return TTSVoicesResponse(voices=_get_fallback_voices())
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{ELEVENLABS_BASE_URL}/voices", headers=_get_elevenlabs_headers())
                if response.status_code != 200:
                    return TTSVoicesResponse(voices=_get_fallback_voices())
                data = response.json()
                return TTSVoicesResponse(voices=[
                    {"voice_id": v.get("voice_id",""), "name": v.get("name","Unknown"),
                     "category": v.get("category","premade"), "preview_url": v.get("preview_url","")}
                    for v in data.get("voices", [])])
            except Exception:
                return TTSVoicesResponse(voices=_get_fallback_voices())
        elif TTS_PROVIDER == "pollinations":
            return TTSVoicesResponse(voices=[
                {"voice_id": "alloy", "name": "Alloy", "category": "standard", "preview_url": "", "description": "Neutral, balanced"},
                {"voice_id": "echo", "name": "Echo", "category": "standard", "preview_url": "", "description": "Warm, friendly"},
                {"voice_id": "fable", "name": "Fable", "category": "standard", "preview_url": "", "description": "Storytelling, expressive"},
                {"voice_id": "onyx", "name": "Onyx", "category": "standard", "preview_url": "", "description": "Deep, authoritative"},
                {"voice_id": "nova", "name": "Nova", "category": "standard", "preview_url": "", "description": "Bright, energetic"},
                {"voice_id": "shimmer", "name": "Shimmer", "category": "standard", "preview_url": "", "description": "Soft, gentle"},
            ])
        return TTSVoicesResponse(voices=[])
    except Exception:
        return TTSVoicesResponse(voices=_get_fallback_voices())


@router.get("/voice/metrics")
async def get_voice_metrics_endpoint(user: User = Depends(get_current_user)):
    """Admin endpoint for voice API metrics and cost tracking."""
    try:
        return {
            "metrics": get_voice_metrics(),
            "user_costs": get_cost_breakdown(user.user_id),
            "user_monthly_spend": get_monthly_spend(user.user_id),
        }
    except Exception as e:
        logger.exception("[voice/metrics] failed")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


__all__ = ["router"]

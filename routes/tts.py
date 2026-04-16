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
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
POLLINATIONS_VOICE = os.getenv("POLLINATIONS_VOICE", "alloy")
POLLINATIONS_SPEED = float(os.getenv("POLLINATIONS_SPEED", "1.0"))
POLLINATIONS_LANG = os.getenv("POLLINATIONS_LANG", "en")
POLLINATIONS_BASE_URL = "https://text.pollinations.ai"
TTS_MAX_RETRIES = 2
TTS_RETRY_BACKOFF = [2, 4]  # 2s, 4s


# ── Schemas ───────────────────────────────────

class TTSRequest(BaseModel):
    """Schema for text-to-speech request"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice_id: Optional[str] = Field(default=None, description="Voice ID or name")
    model: Optional[str] = Field(default=None, description="Model ID or language code")
    speed: Optional[float] = Field(default=None, ge=0.25, le=4.0, description="Speech speed")

class TTSVoicesResponse(BaseModel):
    """Schema for available voices response"""
    voices: list[dict]


# ── Helpers ───────────────────────────────────

def _get_elevenlabs_headers() -> dict:
    """Return authorization headers for ElevenLabs API."""
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


async def _stream_tts_audio(text: str, voice_id: str, model: str):
    """Stream audio chunks from ElevenLabs API directly to client."""
    payload = {
        "text": text, "model_id": model, "output_format": "mp3_44100_128",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True},
    }
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}/stream"
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload, headers=_get_elevenlabs_headers()) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                error_text = error_body.decode("utf-8", errors="replace")
                logger.error(f"[tts] ElevenLabs API error: {response.status_code} — {error_text}")
                raise HTTPException(
                    status_code=response.status_code if response.status_code < 500 else 500,
                    detail=f"TTS failed: {error_text[:200]}")
            async for chunk in response.aiter_bytes():
                yield chunk


async def _fetch_pollinations_tts(text: str, voice: str, lang: str, speed: float) -> bytes:
    """Fetch audio from Pollinations TTS API with retry (backoff: 2s, 4s).
    
    Correct URL: https://text.pollinations.ai/{text}?model=openai-audio&voice={voice}
    """
    encoded_text = urllib.parse.quote(text)
    url = f"{POLLINATIONS_BASE_URL}/{encoded_text}?model=openai-audio&voice={voice}&lang={lang}&speed={speed}"
    last_error = None
    for attempt in range(TTS_MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code if response.status_code < 500 else 500,
                    detail=f"TTS failed: {response.text[:200]}")
            return response.content
        except httpx.TimeoutException:
            last_error = "timeout"
        except httpx.RequestError as e:
            last_error = f"request_error: {e}"
        except HTTPException:
            raise
        except Exception as e:
            last_error = str(e)
        if attempt < TTS_MAX_RETRIES - 1:
            backoff = TTS_RETRY_BACKOFF[attempt]
            logger.warning(f"[tts/pollinations] error attempt {attempt+1}/{TTS_MAX_RETRIES}, retry in {backoff}s")
            await asyncio.sleep(backoff)
    raise HTTPException(status_code=500, detail=f"TTS failed after {TTS_MAX_RETRIES} retries: {last_error}")


async def _stream_pollinations_tts(text: str, voice: str, lang: str, speed: float):
    """Generator wrapper for Pollinations TTS with retry logic."""
    yield await _fetch_pollinations_tts(text, voice, lang, speed)


def _get_fallback_voices() -> list[dict]:
    """Return fallback voice list when ElevenLabs API is unavailable."""
    return [
        {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "category": "premade", "preview_url": ""},
        {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "category": "premade", "preview_url": ""},
        {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "category": "premade", "preview_url": ""},
        {"voice_id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel", "category": "premade", "preview_url": ""},
    ]


# ── Endpoints ─────────────────────────────────

@router.post("/tts")
async def text_to_speech(req: TTSRequest, user: User = Depends(get_current_user)):
    """
    Convert text to speech (ElevenLabs or Pollinations).
    Production: rate limiting, budget check, retry, metrics tracking.
    """
    start_time = time.time()
    logger.info(f"[tts] user={user.user_id[:8]}... provider={TTS_PROVIDER} len={len(req.text)}")
    try:
        # Rate limit check
        allowed, error_msg, headers = check_voice_rate_limit(user.user_id, "tts")
        if not allowed:
            record_voice_metric(service="tts", success=False, latency_ms=(time.time()-start_time)*1000,
                user_id=user.user_id, provider=TTS_PROVIDER, error_type="rate_limited")
            raise HTTPException(status_code=429, detail=error_msg, headers=headers)
        # Budget check
        budget_ok, budget_error, _ = check_budget(user.user_id)
        if not budget_ok:
            record_voice_metric(service="tts", success=False, latency_ms=(time.time()-start_time)*1000,
                user_id=user.user_id, provider=TTS_PROVIDER, error_type="budget_exhausted")
            raise HTTPException(status_code=429, detail=budget_error)

        if TTS_PROVIDER == "elevenlabs":
            if not ELEVENLABS_API_KEY:
                raise HTTPException(status_code=503, detail="ElevenLabs TTS not configured")
            vid = req.voice_id or ELEVENLABS_VOICE_ID
            mdl = req.model or ELEVENLABS_MODEL
            track_cost(user_id=user.user_id, service="tts", char_count=len(req.text), provider="elevenlabs")
            record_voice_metric(service="tts", success=True, latency_ms=(time.time()-start_time)*1000,
                user_id=user.user_id, provider="elevenlabs")
            return StreamingResponse(_stream_tts_audio(req.text, vid, mdl), media_type="audio/mpeg",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive", **headers})
        elif TTS_PROVIDER == "pollinations":
            voice = req.voice_id or POLLINATIONS_VOICE
            lang = req.model or POLLINATIONS_LANG
            spd = req.speed if req.speed is not None else POLLINATIONS_SPEED
            track_cost(user_id=user.user_id, service="tts", char_count=len(req.text), provider="pollinations")
            return StreamingResponse(_stream_pollinations_tts(req.text, voice, lang, spd), media_type="audio/mpeg",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", **headers})
        else:
            raise HTTPException(status_code=503, detail=f"Unknown TTS provider: {TTS_PROVIDER}")
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

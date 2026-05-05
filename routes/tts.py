# routes/tts.py
# ─────────────────────────────────────────────
# Text-to-Speech Endpoint — Multi-Provider (ElevenLabs + Pollinations)
#   POST /tts          → TTS audio streaming
#   POST /tts/raw      → Query param version
#   GET  /tts/voices   → List available voices
#   GET  /voice/metrics → Admin metrics dashboard
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
POLLINATIONS_VOICE = os.getenv("POLLINATIONS_VOICE", "nova")
POLLINATIONS_SPEED = float(os.getenv("POLLINATIONS_SPEED", "1.0"))
POLLINATIONS_LANG = os.getenv("POLLINATIONS_LANG", "en")
POLLINATIONS_BASE_URL = "https://text.pollinations.ai"

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")

# ── Schemas ───────────────────────────────────

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: Optional[str] = None
    model: Optional[str] = None
    speed: Optional[float] = Field(default=None, ge=0.25, le=4.0)

class TTSVoice(BaseModel):
    voice_id: str
    name: str
    category: str = "standard"
    preview_url: str = ""
    description: str = ""

class TTSVoicesResponse(BaseModel):
    voices: list[TTSVoice] = []

# ── Helpers ───────────────────────────────────

def _get_elevenlabs_headers() -> dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Accept": "application/json"}

def _get_fallback_voices() -> list[TTSVoice]:
    return [
        TTSVoice(voice_id="nova", name="Nova", category="standard", preview_url="", description="Bright, energetic"),
        TTSVoice(voice_id="alloy", name="Alloy", category="standard", preview_url="", description="Neutral, balanced"),
    ]

async def _fetch_pollinations_tts(text: str, voice: str, lang: str, speed: float) -> bytes:
    """Fetch audio from Pollinations TTS API."""
    encoded_text = urllib.parse.quote(text)
    url = f"{POLLINATIONS_BASE_URL}/openai-audio/{encoded_text}?voice={voice}&lang={lang}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        if response.status_code != 200:
            logger.error(f"[tts] Pollinations failed: {response.status_code} - {response.text[:100]}")
            raise HTTPException(status_code=response.status_code, detail="Free TTS service temporarily unavailable")
        return response.content

async def _stream_pollinations_tts(text: str, voice: str, lang: str, speed: float):
    audio = await _fetch_pollinations_tts(text, voice, lang, speed)
    yield audio

async def _stream_tts_audio(text: str, voice_id: str, model: str):
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=503, detail="ElevenLabs TTS not configured")
    
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}/stream"
    data = {"text": text, "model_id": model}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=data, headers=_get_elevenlabs_headers()) as response:
            if response.status_code != 200:
                error_detail = await response.aread()
                logger.error(f"[tts] ElevenLabs failed: {response.status_code} - {error_detail.decode()}")
                raise HTTPException(status_code=response.status_code, detail="ElevenLabs TTS failed")
            async for chunk in response.aiter_bytes():
                yield chunk

# ── Endpoints ─────────────────────────────────

@router.post("/tts")
async def text_to_speech(req: TTSRequest, user: User = Depends(get_current_user)):
    """Convert text to speech using free Pollinations provider."""
    start_time = time.time()
    try:
        allowed, error_msg, headers = check_voice_rate_limit(user.user_id, "tts")
        if not allowed:
            raise HTTPException(status_code=429, detail=error_msg, headers=headers)

        voice = req.voice_id or POLLINATIONS_VOICE
        lang = req.model or POLLINATIONS_LANG
        
        track_cost(user_id=user.user_id, service="tts", char_count=len(req.text), provider="pollinations")
        audio_content = await _fetch_pollinations_tts(req.text, voice, lang, 1.0)
        
        record_voice_metric(service="tts", success=True, latency_ms=(time.time()-start_time)*1000,
            user_id=user.user_id, provider="pollinations")
            
        return StreamingResponse(
            io.BytesIO(audio_content), 
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-cache", **headers}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[tts] unexpected error")
        record_voice_metric(service="tts", success=False, latency_ms=(time.time()-start_time)*1000,
            user_id=user.user_id, provider="pollinations", error_type="unexpected_error")
        raise HTTPException(status_code=500, detail=str(e))

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

        if TTS_PROVIDER == "elevenlabs":
            if not ELEVENLABS_API_KEY:
                raise HTTPException(status_code=503, detail="ElevenLabs TTS not configured")
            return StreamingResponse(_stream_tts_audio(text, voice_id or ELEVENLABS_VOICE_ID, model or ELEVENLABS_MODEL),
                media_type="audio/mpeg", headers={"Cache-Control": "no-cache", **headers})
        else:
            return StreamingResponse(
                _stream_pollinations_tts(text, voice_id or POLLINATIONS_VOICE, model or POLLINATIONS_LANG,
                    speed if speed is not None else POLLINATIONS_SPEED),
                media_type="audio/mpeg", headers={"Cache-Control": "no-cache", **headers})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[tts/raw] unexpected error")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tts/voices", response_model=TTSVoicesResponse)
async def list_voices(user: User = Depends(get_current_user)):
    """List available voices for the current TTS provider."""
    try:
        if TTS_PROVIDER == "elevenlabs":
            if not ELEVENLABS_API_KEY:
                return TTSVoicesResponse(voices=_get_fallback_voices())
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{ELEVENLABS_BASE_URL}/voices", headers=_get_elevenlabs_headers())
            if response.status_code != 200:
                return TTSVoicesResponse(voices=_get_fallback_voices())
            data = response.json()
            return TTSVoicesResponse(voices=[
                TTSVoice(voice_id=v["voice_id"], name=v["name"], category=v["category"], preview_url=v.get("preview_url",""))
                for v in data.get("voices", [])])
        else:
            return TTSVoicesResponse(voices=[
                TTSVoice(voice_id="alloy", name="Alloy", category="standard", preview_url="", description="Neutral"),
                TTSVoice(voice_id="echo", name="Echo", category="standard", preview_url="", description="Warm"),
                TTSVoice(voice_id="fable", name="Fable", category="standard", preview_url="", description="Expressive"),
                TTSVoice(voice_id="onyx", name="Onyx", category="standard", preview_url="", description="Deep"),
                TTSVoice(voice_id="nova", name="Nova", category="standard", preview_url="", description="Energetic"),
                TTSVoice(voice_id="shimmer", name="Shimmer", category="standard", preview_url="", description="Soft"),
            ])
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

# multimodal/transcribe.py
# ─────────────────────────────────────────────
# Voice Transcription — Whisper via Pollinations
#
# Production hardening (Phase 1 hardening items 1-7):
#   1. Rate limiting — via voice.rate_limiter
#   2. Cost tracking — tracks per-request cost in Redis
#   3. Retry logic — exponential backoff (2s, 4s, 8s) up to 3 retries
#   4. Audio format conversion — converts to MP3 16kHz mono
#   6. Metrics — records latency, success/error rates
#   7. Content moderation — scans transcript for PII/threats
#
# RULES.md Compliance:
# - File size limits enforced BEFORE processing
# - MIME type validation
# - Supabase Storage for persistence
# - Text sanitization
# - <500 lines
#
# Uses: Pollinations Whisper Large V3 ($0.00004/sec)
# ─────────────────────────────────────────────

import os
import time
import asyncio
import logging
import tempfile
from typing import Dict, Optional
from fastapi import UploadFile, HTTPException
from supabase import Client
from multimodal.validators import validate_upload, sanitize_text, MAX_VOICE_SIZE_MB
import requests

from voice.audio_converter import convert_to_mp3, get_audio_info
from voice.cost_tracker import track_cost, check_budget
from voice.moderation import moderate_transcription
from voice.metrics import record_voice_metric

logger = logging.getLogger(__name__)

# ═══ CONFIGURATION ═══════════════════════════

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
POLLINATIONS_WHISPER_URL = "https://api.pollinations.ai/transcribe"
POLLINATIONS_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper")

# Retry configuration (Production item #3)
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [2, 4, 8]  # Exponential backoff


# ═══ TRANSCRIBE VOICE ════════════════════════

async def transcribe_voice(
    file: UploadFile,
    user_id: str,
    session_id: str,
    supabase: Client
) -> Dict[str, str]:
    """
    Transcribe voice audio to text using Pollinations Whisper.

    Production features:
    - Budget check before processing (prevents overages)
    - Audio format conversion (webm/mp4/wav/ogg → MP3 16kHz mono)
    - Retry with exponential backoff on timeout/connection errors
    - Cost tracking per request
    - Content moderation on transcript
    - Metrics recording for observability

    RULES.md: File size validation BEFORE processing, Supabase Storage RLS

    Args:
        file: Uploaded audio file
        user_id: User UUID (for Supabase Storage path)
        session_id: Session UUID (for Supabase Storage path)
        supabase: Supabase client

    Returns:
        Dict with:
        - transcript: Transcribed text
        - file_url: Supabase Storage URL
        - input_modality: "voice"
        - moderation: ModerationResult dict (security metadata)

    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 429 if budget exhausted
        HTTPException: 500/504 if transcription fails after retries
    """
    start_time = time.time()
    moderation_result = None

    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        original_format = (file.content_type or "audio/mp3").split("/")[-1] if file.content_type else "mp3"

        # VALIDATE BEFORE PROCESSING (RULES.md)
        valid, error = validate_upload(
            filename=file.filename or "audio.mp3",
            content_type=file.content_type or "audio/mp3",
            file_size=file_size,
            upload_type="voice"
        )

        if not valid:
            latency_ms = (time.time() - start_time) * 1000
            record_voice_metric(
                service="transcribe",
                success=False,
                latency_ms=latency_ms,
                user_id=user_id,
                error_type="validation_error"
            )
            logger.warning(f"[voice] validation failed: {error}")
            raise HTTPException(status_code=400, detail=error)

        # BUDGET CHECK — block if user exceeded monthly voice budget
        budget_ok, budget_error, monthly_spend = check_budget(user_id)
        if not budget_ok:
            latency_ms = (time.time() - start_time) * 1000
            record_voice_metric(
                service="transcribe",
                success=False,
                latency_ms=latency_ms,
                user_id=user_id,
                error_type="budget_exhausted"
            )
            raise HTTPException(status_code=429, detail=budget_error)

        # AUDIO FORMAT CONVERSION — convert to MP3 16kHz mono for best Whisper accuracy
        audio_data = content
        output_format = original_format
        was_converted = False

        try:
            audio_data, output_format, was_converted = convert_to_mp3(content, original_format)
            if was_converted:
                logger.info(f"[voice] converted {original_format} → MP3 ({len(content)} → {len(audio_data)} bytes)")
        except Exception as e:
            logger.warning(f"[voice] audio conversion failed, using original: {e}")
            # Fallback: use original format anyway

        # Log audio metadata for debugging
        audio_info = get_audio_info(audio_data, output_format)
        logger.info(
            f"[voice] audio info: format={audio_info['format']} "
            f"duration_ms={audio_info.get('duration_ms', 0)} "
            f"converted={was_converted}"
        )

        # TRANSCRIBE WITH RETRY — exponential backoff on timeout/connection errors
        transcript = await _transcribe_with_retry(audio_data, output_format, user_id)

        # Sanitize transcript
        transcript = sanitize_text(transcript.strip())

        if not transcript:
            latency_ms = (time.time() - start_time) * 1000
            record_voice_metric(
                service="transcribe",
                success=False,
                latency_ms=latency_ms,
                user_id=user_id,
                provider="pollinations",
                error_type="empty_transcript"
            )
            logger.error("[voice] empty transcript from Whisper")
            raise HTTPException(status_code=500, detail="Transcription failed")

        # CONTENT MODERATION — scan for PII, threats, hate speech
        moderation_result = moderate_transcription(transcript)

        # COST TRACKING — record cost based on audio duration
        duration_seconds = audio_info.get("duration_ms", 0) / 1000.0
        cost = track_cost(
            user_id=user_id,
            service="transcribe",
            duration_seconds=duration_seconds,
            provider="pollinations"
        )
        logger.debug(f"[voice] cost tracked: ${cost:.6f} (duration={duration_seconds:.1f}s)")

        # Upload to Supabase Storage
        file_path = f"user-files/{user_id}/{session_id}/{file.filename}"
        supabase.storage.from_("user-files").upload(file_path, content)
        file_url = supabase.storage.from_("user-files").get_public_url(file_path)

        # METRICS — record successful request
        latency_ms = (time.time() - start_time) * 1000
        record_voice_metric(
            service="transcribe",
            success=True,
            latency_ms=latency_ms,
            user_id=user_id,
            provider="pollinations"
        )

        logger.info(
            f"[voice] transcribed {file_size} bytes → {len(transcript)} chars "
            f"(latency={latency_ms:.0f}ms, cost=${cost:.6f})"
        )

        result = {
            "transcript": transcript,
            "file_url": file_url,
            "input_modality": "voice",
        }

        # Attach moderation metadata if flags were raised
        if moderation_result and not moderation_result.is_clean:
            result["moderation"] = {
                "flags": moderation_result.flags,
                "severity": moderation_result.severity,
                "pii_detected": moderation_result.pii_detected,
                "pii_types": moderation_result.pii_types,
            }

        return result

    except HTTPException:
        raise
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        record_voice_metric(
            service="transcribe",
            success=False,
            latency_ms=latency_ms,
            user_id=user_id,
            provider="pollinations",
            error_type="unexpected_error"
        )
        logger.error(f"[voice] unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")


async def _transcribe_with_retry(
    audio_data: bytes,
    audio_format: str,
    user_id: str
) -> str:
    """
    Call Pollinations Whisper API with exponential backoff retry.

    WHY: Network failures happen. Retry with backoff (2s, 4s, 8s)
    significantly improves reliability without user-facing errors.
    Only fails to user after ALL retries exhausted.

    Args:
        audio_data: Audio file bytes
        audio_format: Format string (mp3, webm, wav, etc.)
        user_id: User UUID for logging

    Returns:
        Transcribed text from Whisper

    Raises:
        HTTPException: 504 on timeout after all retries
        HTTPException: 500 on API error after all retries
    """
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            # Create temp file for requests library
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{audio_format}"
            ) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Determine MIME type for requests
            mime_map = {
                "mp3": "audio/mpeg",
                "mpga": "audio/mpeg",
                "mpeg": "audio/mpeg",
                "webm": "audio/webm",
                "wav": "audio/wav",
                "ogg": "audio/ogg",
                "mp4": "audio/mp4",
                "m4a": "audio/m4a",
            }
            mime_type = mime_map.get(audio_format.lower(), "audio/mpeg")

            with open(tmp_path, "rb") as audio_file:
                response = requests.post(
                    POLLINATIONS_WHISPER_URL,
                    files={"file": (f"audio.{audio_format}", audio_file, mime_type)},
                    data={"model": POLLINATIONS_WHISPER_MODEL},
                    headers={"Authorization": f"Bearer {POLLINATIONS_API_KEY}"},
                    timeout=60
                )

            # Clean up temp file
            os.unlink(tmp_path)

            # Check response
            response.raise_for_status()
            result = response.json()
            transcript = result.get("text", "").strip()

            if not transcript:
                raise HTTPException(status_code=500, detail="Empty transcript from Whisper")

            return transcript

        except requests.exceptions.Timeout:
            last_error = "timeout"
            if attempt < MAX_RETRIES - 1:
                backoff = RETRY_BACKOFF_SECONDS[attempt]
                logger.warning(
                    f"[voice/transcribe] timeout (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {backoff}s..."
                )
                await asyncio.sleep(backoff)
            else:
                logger.error(
                    f"[voice/transcribe] timeout after {MAX_RETRIES} attempts"
                )

        except requests.exceptions.ConnectionError as e:
            last_error = "connection_error"
            if attempt < MAX_RETRIES - 1:
                backoff = RETRY_BACKOFF_SECONDS[attempt]
                logger.warning(
                    f"[voice/transcribe] connection error (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {backoff}s... error={e}"
                )
                await asyncio.sleep(backoff)
            else:
                logger.error(
                    f"[voice/transcribe] connection error after {MAX_RETRIES} attempts"
                )

        except HTTPException:
            raise  # Re-raise HTTP exceptions immediately
        except Exception as e:
            last_error = f"unexpected: {e}"
            if attempt < MAX_RETRIES - 1:
                backoff = RETRY_BACKOFF_SECONDS[attempt]
                logger.warning(
                    f"[voice/transcribe] error (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {backoff}s... error={e}"
                )
                await asyncio.sleep(backoff)
            else:
                logger.error(
                    f"[voice/transcribe] failed after {MAX_RETRIES} attempts: {e}"
                )
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    # All retries exhausted
    if last_error == "timeout":
        raise HTTPException(status_code=504, detail="Transcription timeout after retries")
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed after {MAX_RETRIES} retries: {last_error}"
        )

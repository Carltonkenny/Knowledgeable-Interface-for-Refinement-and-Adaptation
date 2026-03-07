# multimodal/voice.py
# ─────────────────────────────────────────────
# Voice Transcription — Whisper via Pollinations
#
# RULES.md Compliance:
# - File size validation BEFORE processing
# - MIME type validation
# - Supabase Storage for persistence
# - Text sanitization
#
# Uses: Pollinations Whisper Large V3 (0.00004 pollen/sec)
# ─────────────────────────────────────────────

import os
import logging
import tempfile
from typing import Dict, Optional
from fastapi import UploadFile, HTTPException
from supabase import Client
from multimodal.validators import validate_upload, sanitize_text, MAX_VOICE_SIZE_MB
import requests

logger = logging.getLogger(__name__)

# ═══ CONFIGURATION ═══════════════════════════

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
POLLINATIONS_WHISPER_URL = "https://text.pollinations.ai/transcribe"


# ═══ TRANSCRIBE VOICE ════════════════════════

async def transcribe_voice(
    file: UploadFile,
    user_id: str,
    session_id: str,
    supabase: Client
) -> Dict[str, str]:
    """
    Transcribe voice audio to text using Pollinations Whisper.
    
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
        
    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 500 if transcription fails
        
    Example:
        result = await transcribe_voice(
            file=audio_file,
            user_id="user-uuid",
            session_id="session-uuid",
            supabase=supabase_client
        )
        # result["transcript"] = "write a story about a robot"
    """
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # VALIDATE BEFORE PROCESSING (RULES.md)
    valid, error = validate_upload(
        filename=file.filename or "audio.mp3",
        content_type=file.content_type or "audio/mp3",
        file_size=file_size,
        upload_type="voice"
    )
    
    if not valid:
        logger.warning(f"[voice] validation failed: {error}")
        raise HTTPException(status_code=400, detail=error)
    
    try:
        # Save to temp file for API call
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Call Pollinations Whisper API
        with open(tmp_path, "rb") as audio_file:
            response = requests.post(
                POLLINATIONS_WHISPER_URL,
                files={"file": audio_file},
                data={"model": "whisper"},
                headers={"Authorization": f"Bearer {POLLINATIONS_API_KEY}"},
                timeout=60
            )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Check response
        response.raise_for_status()
        result = response.json()
        
        # Extract and sanitize transcript
        transcript = sanitize_text(result.get("text", "").strip())
        
        if not transcript:
            logger.error("[voice] empty transcript from Whisper")
            raise HTTPException(status_code=500, detail="Transcription failed")
        
        # Upload to Supabase Storage (for history reference)
        file_path = f"user-files/{user_id}/{session_id}/{file.filename}"
        supabase.storage.from_("user-files").upload(file_path, content)
        file_url = supabase.storage.from_("user-files").get_public_url(file_path)
        
        logger.info(f"[voice] transcribed {file_size} bytes → {len(transcript)} chars")
        
        return {
            "transcript": transcript,
            "file_url": file_url,
            "input_modality": "voice",
        }
        
    except requests.exceptions.Timeout:
        logger.error("[voice] Whisper API timeout")
        raise HTTPException(status_code=504, detail="Transcription timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"[voice] Whisper API error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")
    except Exception as e:
        logger.error(f"[voice] unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")

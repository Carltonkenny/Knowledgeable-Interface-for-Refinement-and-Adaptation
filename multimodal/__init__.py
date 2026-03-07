# multimodal/__init__.py
# ─────────────────────────────────────────────
# Multimodal Processing Module — Voice, Image, File
#
# RULES.md Compliance:
# - File size limits enforced BEFORE processing
# - MIME type validation
# - No executables or dangerous file types
# - Supabase Storage RLS (user_id = auth.uid())
# - Text sanitization (remove injection attempts)
#
# Exports:
#   transcribe_voice()     — Whisper → text
#   process_image()        — Image → base64
#   extract_text_from_file() — PDF/DOCX/TXT → text
#   validate_upload()      — Security validation
# ─────────────────────────────────────────────

from multimodal.validators import validate_upload, sanitize_text
from multimodal.transcribe import transcribe_voice
from multimodal.image import process_image
from multimodal.files import extract_text_from_file

__all__ = [
    "validate_upload",
    "sanitize_text",
    "transcribe_voice",
    "process_image",
    "extract_text_from_file",
]

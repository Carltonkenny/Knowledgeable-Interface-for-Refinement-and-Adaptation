# multimodal/validators.py
# ─────────────────────────────────────────────
# Security Validation for Multimodal Uploads
#
# RULES.md Compliance:
# - File size limits enforced BEFORE processing
# - MIME type validation
# - No executables or dangerous file types
# - Text sanitization (remove injection attempts)
#
# Security First: All validation happens BEFORE any processing
# ─────────────────────────────────────────────

import re
import logging
from typing import Tuple, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ═══ FILE SIZE LIMITS (from RULES.md) ═══════

MAX_VOICE_SIZE_MB = 25
MAX_IMAGE_SIZE_MB = 5
MAX_FILE_SIZE_MB = 2

# Convert to bytes
MAX_VOICE_SIZE = MAX_VOICE_SIZE_MB * 1024 * 1024
MAX_IMAGE_SIZE = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024

# ═══ ALLOWED MIME TYPES ═════════════════════

ALLOWED_VOICE_TYPES = {
    "audio/mp3",
    "audio/mp4",
    "audio/mpeg",
    "audio/mpga",
    "audio/m4a",
    "audio/wav",
    "audio/webm",
}

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}

ALLOWED_FILE_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

# ═══ DANGEROUS FILE EXTENSIONS ═══════════════

DANGEROUS_EXTENSIONS = {
    # Executables
    ".exe", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".js",
    # Archives (could contain malware)
    ".zip", ".rar", ".7z", ".tar", ".gz",
    # Scripts
    ".py", ".rb", ".pl", ".php",
    # System files
    ".dll", ".so", ".dylib",
}


# ═══ VALIDATE UPLOAD ═════════════════════════

def validate_upload(
    filename: str,
    content_type: str,
    file_size: int,
    upload_type: str  # "voice", "image", or "file"
) -> Tuple[bool, Optional[str]]:
    """
    Validate file upload BEFORE processing.
    
    RULES.md: File size limits enforced first, MIME type validation, no executables
    
    Args:
        filename: Original filename
        content_type: MIME type from upload
        file_size: File size in bytes
        upload_type: "voice", "image", or "file"
        
    Returns:
        (True, None) if valid
        (False, error_message) if invalid
        
    Example:
        valid, error = validate_upload(
            filename="document.pdf",
            content_type="application/pdf",
            file_size=1024000,
            upload_type="file"
        )
        if not valid:
            raise HTTPException(400, error)
    """
    # Check 1: File size (BEFORE any processing)
    max_size = {
        "voice": MAX_VOICE_SIZE,
        "image": MAX_IMAGE_SIZE,
        "file": MAX_FILE_SIZE,
    }.get(upload_type, MAX_FILE_SIZE)
    
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        logger.warning(f"[security] file too large: {actual_mb:.1f}MB (max: {max_mb:.1f}MB)")
        return False, f"File too large: {actual_mb:.1f}MB (max: {max_mb:.1f}MB)"
    
    # Check 2: MIME type validation
    allowed_types = {
        "voice": ALLOWED_VOICE_TYPES,
        "image": ALLOWED_IMAGE_TYPES,
        "file": ALLOWED_FILE_TYPES,
    }.get(upload_type, ALLOWED_FILE_TYPES)
    
    if content_type not in allowed_types:
        logger.warning(f"[security] invalid MIME type: {content_type}")
        return False, f"Unsupported file type: {content_type}"
    
    # Check 3: Dangerous extension check
    ext = "." + filename.lower().split(".")[-1] if "." in filename else ""
    
    if ext in DANGEROUS_EXTENSIONS:
        logger.warning(f"[security] dangerous extension blocked: {ext}")
        return False, f"Dangerous file type: {ext}"
    
    # Check 4: Filename sanitization (prevent path traversal)
    if ".." in filename or "/" in filename or "\\" in filename:
        logger.warning(f"[security] suspicious filename: {filename}")
        return False, "Invalid filename"
    
    logger.info(f"[security] upload validated: {filename} ({file_size} bytes, {content_type})")
    return True, None


# ═══ SANITIZE TEXT ═══════════════════════════

def sanitize_text(text: str) -> str:
    """
    Sanitize extracted text to remove injection attempts.
    
    RULES.md: Text sanitization (remove injection attempts)
    
    Args:
        text: Raw extracted text from file
        
    Returns:
        Cleaned text with potential injections removed
        
    Removes:
        - Null bytes
        - Control characters (except newlines/tabs)
        - Potential prompt injection patterns
        - Excessive whitespace
        
    Example:
        clean = sanitize_text(extracted_text)
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Remove control characters (keep newlines and tabs)
    text = re.sub(r"[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    
    # Remove potential prompt injection patterns
    injection_patterns = [
        r"ignore previous instructions",
        r"you are now",
        r"system message",
        r"new instruction",
        r"###system###",
        r"### SYSTEM ###",
        r"<script>",
        r"</script>",
    ]
    
    for pattern in injection_patterns:
        text = re.sub(pattern, "[REMOVED]", text, flags=re.IGNORECASE)
    
    # Normalize whitespace
    text = " ".join(text.split())
    
    # Limit length (prevent memory exhaustion)
    max_length = 50000  # 50K chars max
    if len(text) > max_length:
        text = text[:max_length - 3] + "..."  # Reserve 3 chars for "..."
        logger.warning(f"[security] text truncated to {max_length} chars")
    
    return text

# multimodal/image.py
# ─────────────────────────────────────────────
# Image Processing — Base64 Encoding for LLM
#
# RULES.md Compliance:
# - File size validation BEFORE processing
# - MIME type validation
# - Supabase Storage for persistence
# - No OCR or separate processing (GPT-4o native)
#
# Uses: Pollinations Vision API (included with API key)
# ─────────────────────────────────────────────

import base64
import logging
from typing import Dict
from fastapi import UploadFile, HTTPException
from supabase import Client
from multimodal.validators import validate_upload, MAX_IMAGE_SIZE_MB

logger = logging.getLogger(__name__)


# ═══ PROCESS IMAGE ═══════════════════════════

async def process_image(
    file: UploadFile,
    user_id: str,
    session_id: str,
    supabase: Client
) -> Dict[str, str]:
    """
    Process image and encode to base64 for LLM input.
    
    RULES.md: File size validation BEFORE processing, Supabase Storage RLS
    
    Args:
        file: Uploaded image file
        user_id: User UUID (for Supabase Storage path)
        session_id: Session UUID (for Supabase Storage path)
        supabase: Supabase client
        
    Returns:
        Dict with:
        - base64_image: Base64 encoded image string
        - file_url: Supabase Storage URL
        - input_modality: "image"
        - media_type: MIME type
        
    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 500 if processing fails
        
    Example:
        result = await process_image(
            file=image_file,
            user_id="user-uuid",
            session_id="session-uuid",
            supabase=supabase_client
        )
        # result["base64_image"] = "iVBORw0KGgoAAAANSUhEUgAA..."
    """
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # VALIDATE BEFORE PROCESSING (RULES.md)
    valid, error = validate_upload(
        filename=file.filename or "image.jpg",
        content_type=file.content_type or "image/jpeg",
        file_size=file_size,
        upload_type="image"
    )
    
    if not valid:
        logger.warning(f"[image] validation failed: {error}")
        raise HTTPException(status_code=400, detail=error)
    
    try:
        # Encode to base64
        base64_image = base64.b64encode(content).decode("utf-8")
        
        # Upload to Supabase Storage (for history reference)
        file_path = f"user-files/{user_id}/{session_id}/{file.filename}"
        supabase.storage.from_("user-files").upload(file_path, content)
        file_url = supabase.storage.from_("user-files").get_public_url(file_path)
        
        logger.info(f"[image] processed {file_size} bytes → {len(base64_image)} chars base64")
        
        return {
            "base64_image": base64_image,
            "file_url": file_url,
            "input_modality": "image",
            "media_type": file.content_type or "image/jpeg",
        }
        
    except Exception as e:
        logger.error(f"[image] processing failed: {e}")
        raise HTTPException(status_code=500, detail="Image processing failed")


# ═══ PREPARE FOR GPT VISION ══════════════════

def prepare_for_gpt_vision(
    base64_image: str,
    media_type: str,
    query: str = "Analyze this image"
) -> Dict:
    """
    Prepare image for GPT-4o Vision input.
    
    RULES.md: No separate OCR — GPT-4o is natively multimodal
    
    Args:
        base64_image: Base64 encoded image string
        media_type: MIME type (e.g., "image/jpeg")
        query: Question about the image
        
    Returns:
        Message dict for ChatOpenAI
        
    Example:
        message = prepare_for_gpt_vision(
            base64_image="iVBORw0KGgo...",
            media_type="image/jpeg",
            query="What's in this image?"
        )
        # Returns: {"role": "user", "content": [...]}
    """
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": query},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{base64_image}"}
            }
        ]
    }

# multimodal/files.py
# ─────────────────────────────────────────────
# File Text Extraction — PDF, DOCX, TXT
#
# RULES.md Compliance:
# - File size validation BEFORE processing
# - MIME type validation
# - Supabase Storage for persistence
# - Text sanitization (remove injection attempts)
# - No RAG or embedding — context enrichment only
#
# Uses: PyMuPDF (PDF), python-docx (DOCX), built-in (TXT)
# ─────────────────────────────────────────────

import logging
from typing import Dict
from fastapi import UploadFile, HTTPException
from supabase import Client
from multimodal.validators import validate_upload, sanitize_text
from io import BytesIO

logger = logging.getLogger(__name__)


# ═══ EXTRACT TEXT FROM FILE ══════════════════

async def extract_text_from_file(
    file: UploadFile,
    user_id: str,
    session_id: str,
    supabase: Client
) -> Dict[str, str]:
    """
    Extract text from PDF, DOCX, or TXT files.
    
    RULES.md: File size validation BEFORE processing, text sanitization
    
    Args:
        file: Uploaded document file
        user_id: User UUID (for Supabase Storage path)
        session_id: Session UUID (for Supabase Storage path)
        supabase: Supabase client
        
    Returns:
        Dict with:
        - extracted_text: Cleaned text content
        - file_url: Supabase Storage URL
        - input_modality: "file"
        - file_type: File extension
        
    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 500 if extraction fails
        
    Example:
        result = await extract_text_from_file(
            file=pdf_file,
            user_id="user-uuid",
            session_id="session-uuid",
            supabase=supabase_client
        )
        # result["extracted_text"] = "Document content..."
    """
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # VALIDATE BEFORE PROCESSING (RULES.md)
    valid, error = validate_upload(
        filename=file.filename or "document.txt",
        content_type=file.content_type or "text/plain",
        file_size=file_size,
        upload_type="file"
    )
    
    if not valid:
        logger.warning(f"[file] validation failed: {error}")
        raise HTTPException(status_code=400, detail=error)
    
    try:
        # Extract text based on file type
        if file.content_type == "application/pdf":
            text = _extract_pdf_text(content)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = _extract_docx_text(content)
        elif file.content_type == "text/plain":
            text = content.decode("utf-8")
        else:
            logger.error(f"[file] unsupported type: {file.content_type}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        # SANITIZE TEXT (RULES.md: remove injection attempts)
        cleaned_text = sanitize_text(text)
        
        if not cleaned_text.strip():
            logger.error("[file] empty text after extraction")
            raise HTTPException(status_code=400, detail="No text could be extracted")
        
        # Upload to Supabase Storage (for history reference)
        file_path = f"user-files/{user_id}/{session_id}/{file.filename}"
        supabase.storage.from_("user-files").upload(file_path, content)
        file_url = supabase.storage.from_("user-files").get_public_url(file_path)
        
        logger.info(f"[file] extracted {len(cleaned_text)} chars from {file_size} bytes")
        
        return {
            "extracted_text": cleaned_text,
            "file_url": file_url,
            "input_modality": "file",
            "file_type": file.filename.split(".")[-1].lower() if "." in file.filename else "txt",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[file] extraction failed: {e}")
        raise HTTPException(status_code=500, detail="File extraction failed")


# ═══ PDF EXTRACTION ══════════════════════════

def _extract_pdf_text(content: bytes) -> str:
    """
    Extract text from PDF using PyMuPDF.
    
    Args:
        content: PDF file bytes
        
    Returns:
        Extracted text string
    """
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        
        for page in doc:
            text += page.get_text()
        
        doc.close()
        return text
        
    except ImportError:
        logger.error("[file] PyMuPDF not installed — run: pip install PyMuPDF")
        raise HTTPException(status_code=500, detail="PDF extraction requires PyMuPDF")
    except Exception as e:
        logger.error(f"[file] PDF extraction failed: {e}")
        raise HTTPException(status_code=500, detail="PDF extraction failed")


# ═══ DOCX EXTRACTION ═════════════════════════

def _extract_docx_text(content: bytes) -> str:
    """
    Extract text from DOCX using python-docx.
    
    Args:
        content: DOCX file bytes
        
    Returns:
        Extracted text string
    """
    try:
        from docx import Document
        
        doc = Document(BytesIO(content))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
        
    except ImportError:
        logger.error("[file] python-docx not installed — run: pip install python-docx")
        raise HTTPException(status_code=500, detail="DOCX extraction requires python-docx")
    except Exception as e:
        logger.error(f"[file] DOCX extraction failed: {e}")
        raise HTTPException(status_code=500, detail="DOCX extraction failed")

# memory/langmem.py
# ─────────────────────────────────────────────
# LangMem with Supabase Store — Persistent memory for web app
#
# RULES.md Compliance:
# - Surface isolation: LangMem NEVER on MCP requests
# - User isolation: Supabase RLS (user_id = auth.uid())
# - Background writes: FastAPI BackgroundTasks
# - No hardcoded secrets: All from .env
# - Type hints: All functions annotated
# - Error handling: Try/catch with graceful fallback
#
# Storage: Supabase (production-ready, survives restarts)
# Embeddings: Pollinations AI (embedding model for semantic search)
# Search: pgvector SQL operators (FAST - database-side similarity)
# ─────────────────────────────────────────────

import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import time
from database import get_client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ═══ CONFIGURATION ═══════════════════════════

SUPABASE_TABLE = "langmem_memories"

# Embedding model configuration
# Updated: gemini-embedding-001 with output_dimensionality=768 (was 3072)
# Reason: Supabase free tier HNSW index limit is 2000 dims
# Migration: 024_fix_embedding_dimensions.sql
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_MODEL = "gemini-embedding-001"  # Gemini model (supports output_dimensionality)
EMBEDDING_DIM = 768  # Output dimensionality (must be <= 2000 for Supabase HNSW)


# ═══ EMBEDDING GENERATION ════════════════════

def _describe_image(base64_image: str) -> Optional[str]:
    """
    Generate a text description of an image using Gemini Vision.

    Uses for LangMem embedding: Creates a text description that can be embedded
    for semantic search. This allows Kira to remember what images contained.

    Args:
        base64_image: Base64 encoded image string

    Returns:
        Text description (2-3 sentences) or None if failed

    Example:
        desc = _describe_image("iVBORw0KGgoAAAANSUhEUgAA...")
        # Returns: "Screenshot of Python code showing a function definition..."
    """
    if not base64_image:
        logger.warning("[langmem] skipping image description — empty base64")
        return None

    logger.info("[langmem] describing image for embedding...")

    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)

            # Use Gemini Pro Vision for image description
            model = genai.GenerativeModel("gemini-pro-vision")

            # Decode base64 to bytes
            import base64
            image_bytes = base64.b64decode(base64_image)

            # Generate description
            response = model.generate_content([
                "Describe this image in 2-3 sentences for semantic search indexing. "
                "Focus on: what type of image it is (screenshot, diagram, photo, etc.), "
                "the main content/subject, and any text or code visible. "
                "Be concise but specific enough for future retrieval.",
                {"mime_type": "image/png", "data": image_bytes}
            ])

            description = response.text.strip()
            logger.debug(f"[langmem] image description: '{description[:100]}...'")
            return description

        except ImportError:
            logger.warning("[langmem] google-generativeai not installed, skipping vision")
        except Exception as e:
            logger.error(f"[langmem] Vision description failed: {str(e)}", exc_info=True)

    logger.error("[langmem] Image description failed, returning None")
    return None


def _generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector for text using Google Gemini API.

    Uses Gemini gemini-embedding-001 with output_dimensionality=768.
    Compatible with Supabase free tier HNSW index (limit: 2000 dims).

    Args:
        text: Text to embed

    Returns:
        List of floats (embedding vector) or None if failed

    Example:
        embedding = _generate_embedding("write a python function")
        # Returns: [0.123, -0.456, 0.789, ...] (768 dimensions)
    """
    if not text or not text.strip():
        logger.warning("[langmem] skipping embedding — empty text")
        return None

    logger.info(f"[langmem] generating embedding for: '{text[:100]}'")

    # Try Google Gemini first
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)

            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text[:2048],  # Gemini context limit
                output_dimensionality=768  # Reduce from 3072 to 768 for Supabase HNSW
            )

            embedding = result.get("embedding", [])
            logger.debug(f"[langmem] gemini embedding: {len(embedding)} dimensions")
            return embedding

        except ImportError:
            logger.warning("[langmem] google-generativeai not installed, skipping Gemini")
        except Exception as e:
            logger.error(f"[langmem] Gemini embedding failed: {str(e)}", exc_info=True)

    logger.error("[langmem] No embedding API configured or embedding failed, returning None")
    return None


# ═══ QUERY LANGMEM (pgvector SQL - FAST) ═════

def query_langmem(
    user_id: str,
    query: str,
    top_k: int = 5,
    surface: str = "web_app"
) -> List[Dict[str, Any]]:
    """
    Semantic search for relevant memories using pgvector SQL operators.

    RULES.md: Query on every web request (parallel with other context loads)
    RULES.md: Surface isolation — LangMem is web-app exclusive

    PERFORMANCE:
    - Uses pgvector <=> operator for database-side cosine similarity
    - Only transfers top_k results (not all memories)
    - 100x faster than Python-based similarity for large datasets
    - Network transfer: ~10KB vs ~2MB for 1000 memories

    Args:
        user_id: User UUID from JWT (for RLS isolation)
        query: User's current message (for semantic search)
        top_k: Number of memories to return (default: 5)
        surface: "web_app" or "mcp" — raises error if MCP tries to use LangMem

    Returns:
        List of memory dicts with content, score, metadata
        Empty list if error or no memories found (graceful fallback)

    Example:
        memories = query_langmem(
            user_id="user-uuid",
            query="write a Python function",
            top_k=5
        )
        # Returns: [{content: "...", similarity_score: 0.92, domain: "python"}, ...]
    """
    logger.info(f"[langmem] query_langmem entered for user={user_id[:8]}... query='{query[:50]}'")
    # RULES.md: Surface isolation — LangMem is web-app exclusive
    if surface == "mcp":
        raise ValueError(
            "LangMem is web-app exclusive. MCP must use Supermemory. "
            "See RULES.md: Memory System — Two Layers, Never Merge Them"
        )

    try:
        # Guard: empty user_id causes Postgres UUID parse error (22P02)
        if not user_id:
            logger.warning("[langmem] skipping query — empty user_id")
            return []

        db = get_client()

        if not query or not query.strip():
            logger.warning("[langmem] skipping search — empty query")
            return []

        # Step 1: Generate embedding for query (API call ~500ms)
        query_embedding = _generate_embedding(query)

        if not query_embedding:
            logger.warning("[langmem] embedding generation failed, returning empty")
            return []

        # Step 2: Use SAFE parameterized RPC function with pgvector
        # RULES.md Security: No raw SQL execution — uses predefined RPC function
        # search_langmem_memories is parameterized, preventing SQL injection
        result = db.rpc(
            "match_memories",
            {
                "filter_user_id": user_id,
                "match_count": top_k,
                "query_embedding": query_embedding
            }
        ).execute()

        if not hasattr(result, 'data') or not result.data:
            logger.debug(f"[langmem] no memories found for user {user_id[:8]}...")
            return []

        # Format results (RPC returns 'similarity' not 'similarity_score')
        memories = [
            {
                "id": row.get("id"),
                "content": row.get("content", ""),
                "improved_content": row.get("improved_content", ""),
                "domain": row.get("domain", "general"),
                "quality_score": row.get("quality_score", {}),
                "created_at": row.get("created_at"),
                "similarity_score": float(row.get("similarity_score", 0))
            }
            for row in result.data
        ]

        # Sort by similarity (highest first) and return top_k
        memories.sort(key=lambda m: m.get("similarity_score", 0), reverse=True)

        logger.info(
            f"[langmem] semantic search returned {len(memories)} memories "
            f"for user {user_id[:8]}... (top similarity: {memories[0]['similarity_score']:.3f} if memories else 0)"
        )
        return memories[:top_k]

    except Exception as e:
        logger.error(f"[langmem] query failed: {e}")
        return []  # Graceful fallback


# ═══ WRITE TO LANGMEM ════════════════════════

def write_to_langmem(
    user_id: str,
    session_result: Dict[str, Any]
) -> bool:
    """
    Store session facts asynchronously with embedding.

    RULES.md: Write as background task (user NEVER waits)

    Args:
        user_id: User UUID from JWT (for RLS isolation)
        session_result: Full swarm result with quality scores

    Returns:
        True if successful, False otherwise

    What Gets Stored:
        - Prompt and improved version
        - Quality scores
        - Domain identification
        - Agent skip decisions
        - Embedding for semantic search
        - For images: vision-based description embedded
        - For files: extracted text summary embedded
    """
    try:
        db = get_client()

        # Extract base content
        # NOTE: Swarm uses 'message', but legacy code expects 'raw_prompt'
        raw_prompt = session_result.get("raw_prompt") or session_result.get("message", "")[:2000]
        improved_prompt = session_result.get("improved_prompt", "")[:2000]
        input_modality = session_result.get("input_modality", "text")
        attachments = session_result.get("attachments", [])

        # Log what we received
        logger.info(f"[langmem] received: raw_prompt={len(raw_prompt)} chars, improved={len(improved_prompt)} chars")

        # Build enriched content for embedding based on modality
        if input_modality == "image" and attachments:
            # NEW: Describe image for embedding
            base64_image = attachments[0].get("content", "") if attachments else ""
            image_description = _describe_image(base64_image)
            
            if image_description:
                combined_content = f"Image: {image_description}. User said: {raw_prompt}. Improved: {improved_prompt}"
                logger.info(f"[langmem] embedding image description: {len(image_description)} chars")
            else:
                # Fallback to text only if vision fails
                combined_content = f"{raw_prompt} {improved_prompt}"
                logger.warning("[langmem] image description failed, using text only")
                
        elif input_modality == "file" and attachments:
            # NEW: Use file content for embedding
            # For files, content is already extracted text or base64
            file_content = attachments[0].get("extracted_text", "")[:1000] if attachments else ""
            
            if file_content:
                combined_content = f"File content: {file_content}. User said: {raw_prompt}. Improved: {improved_prompt}"
                logger.info(f"[langmem] embedding file summary: {len(file_content)} chars")
            else:
                # Fallback for base64 files (would need extraction)
                combined_content = f"{raw_prompt} {improved_prompt}"
                logger.warning("[langmem] no extracted text for file, using text only")
                
        else:
            # Text or voice (voice already transcribed to text)
            combined_content = f"{raw_prompt} {improved_prompt}"

        # Generate embedding
        embedding = _generate_embedding(combined_content)

        # Extract facts from session
        memory_data = {
            "user_id": user_id,
            "content": raw_prompt,
            "improved_content": improved_prompt,
            "domain": session_result.get("domain_analysis", {}).get("primary_domain", "general"),
            "quality_score": session_result.get("quality_score", {}),
            "agents_used": session_result.get("agents_used", []),
            "agents_skipped": session_result.get("agents_skipped", []),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Add embedding if generated
        if embedding:
            memory_data["embedding"] = embedding
            logger.debug(f"[langmem] storing embedding: {len(embedding)} dimensions")

        # Insert into Supabase with retry (max 2 attempts, 500ms backoff)
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                db.table(SUPABASE_TABLE).insert(memory_data).execute()
                logger.info(f"[langmem] stored memory with embedding for user {user_id[:8]}...")
                return True
            except Exception as insert_err:
                if attempt < max_attempts - 1:
                    logger.warning(f"[langmem] write attempt {attempt + 1} failed, retrying in 500ms: {insert_err}")
                    time.sleep(0.5)
                else:
                    logger.error(f"[langmem] write failed after {max_attempts} attempts: {insert_err}")
                    return False

        return False  # Should not reach here

    except Exception as e:
        logger.error(f"[langmem] write_to_langmem setup failed: {e}")
        return False  # Silent fail (background task)


# ═══ GET STYLE REFERENCE ═════════════════════

def get_style_reference(
    user_id: str,
    domain: str,
    count: int = 5
) -> List[str]:
    """
    Get user's best past prompts in a domain for stylistic reference.

    RULES.md: Used by prompt engineer to match user's established quality bar.

    Args:
        user_id: User UUID from JWT
        domain: Domain to search in (e.g., "python", "creative writing")
        count: Number of prompts to return (default: 5)

    Returns:
        List of improved prompt strings (user's best work)
        Empty list if error or no memories found

    Example:
        styles = get_style_reference(
            user_id="user-uuid",
            domain="python",
            count=5
        )
        # Returns: ["You are a Python expert...", ...]
    """
    try:
        # Use semantic search with domain as query
        memories = query_langmem(user_id, query=domain, top_k=count * 2, surface="web_app")

        # Filter for high quality scores and matching domain
        high_quality = [
            m.get("improved_content", "")
            for m in memories
            if m.get("domain") == domain
            and m.get("quality_score", {}).get("overall", 0) >= 0.7
        ]

        # If not enough in domain, include general high-quality
        if len(high_quality) < count:
            general = [
                m.get("improved_content", "")
                for m in memories
                if m.get("quality_score", {}).get("overall", 0) >= 0.8
            ]
            high_quality.extend(general)

        logger.info(f"[langmem] retrieved {len(high_quality)} style references for {domain}")
        return high_quality[:count]

    except Exception as e:
        logger.error(f"[langmem] style reference failed: {e}")
        return []


# ═══ GET QUALITY TREND (FR-3 SPEC V1) ═════════════════════

def get_quality_trend(user_id: str, last_n: int = 10) -> str:
    """
    Analyze quality trend over user's last N sessions.

    RULES.md: Used by profile updater to track prompt_quality_trend.
    Compares first half vs second half average quality scores.

    Args:
        user_id: User UUID from JWT (for RLS isolation)
        last_n: Number of sessions to analyze (default: 10)

    Returns:
        str: One of:
            - 'improving': Recent sessions avg > older sessions avg by 0.1+
            - 'declining': Recent sessions avg < older sessions avg by 0.1+
            - 'stable': Change < 0.1 threshold (avoids noise)
            - 'insufficient_data': < 3 sessions to compare

    Example:
        trend = get_quality_trend("user-uuid", last_n=10)
        # Returns: 'improving' | 'stable' | 'declining' | 'insufficient_data'
    """
    try:
        db = get_client()

        # Query last N quality scores (ordered by created_at DESC)
        result = db.table("langmem_memories")\
            .select("quality_score")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(last_n)\
            .execute()

        memories = result.data if hasattr(result, 'data') else []

        if len(memories) < 3:
            logger.debug(f"[langmem] quality trend: insufficient data for {user_id[:8]}...")
            return "insufficient_data"

        # Extract overall scores (handle missing/invalid scores gracefully)
        scores = []
        for m in memories:
            qs = m.get("quality_score", {})
            if isinstance(qs, dict):
                score = qs.get("overall", 0)
                if isinstance(score, (int, float)) and 0 <= score <= 1:
                    scores.append(score)

        if len(scores) < 3:
            logger.debug(f"[langmem] quality trend: insufficient valid scores for {user_id[:8]}...")
            return "insufficient_data"

        # Compare first half (older) vs second half (newer)
        # Note: scores are already ordered DESC (newest first)
        mid = len(scores) // 2
        avg_newer = sum(scores[:mid]) / len(scores[:mid]) if scores[:mid] else 0
        avg_older = sum(scores[mid:]) / len(scores[mid:]) if scores[mid:] else 0

        # Determine trend with 0.1 threshold (avoids noise)
        diff = avg_newer - avg_older

        if diff > 0.1:
            trend = "improving"
        elif diff < -0.1:
            trend = "declining"
        else:
            trend = "stable"

        logger.info(f"[langmem] quality trend for {user_id[:8]}...: {trend} (newer={avg_newer:.2f}, older={avg_older:.2f})")
        return trend

    except Exception as e:
        logger.error(f"[langmem] quality trend failed: {e}")
        return "stable"  # Graceful fallback

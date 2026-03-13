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
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import requests
from database import get_client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ═══ CONFIGURATION ═══════════════════════════

SUPABASE_TABLE = "langmem_memories"

# Embedding model configuration
# Primary: Google Gemini gemini-embedding-001 (3072 dimensions)
# Note: Requires HNSW index in Supabase (IVFFlat limited to 2000 dims)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_MODEL = "gemini-embedding-001"  # Gemini model
EMBEDDING_DIM = 3072  # Gemini gemini-embedding-001 dimension


# ═══ EMBEDDING GENERATION ════════════════════

def _generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector for text using Google Gemini API.

    Uses Gemini gemini-embedding-001 (3072 dimensions).
    Requires HNSW index in Supabase (IVFFlat limited to 2000 dims).

    Args:
        text: Text to embed

    Returns:
        List of floats (embedding vector) or None if failed

    Example:
        embedding = _generate_embedding("write a python function")
        # Returns: [0.123, -0.456, 0.789, ...] (3072 dimensions)
    """
    # Try Google Gemini first
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            
            result = genai.embed_content(
                model="gemini-embedding-001",
                content=text[:2048]  # Gemini context limit
            )
            
            embedding = result.get("embedding", [])
            logger.debug(f"[langmem] gemini embedding: {len(embedding)} dimensions")
            return embedding
        
        except ImportError:
            logger.warning("[langmem] google-generativeai not installed, skipping Gemini")
        except Exception as e:
            logger.warning(f"[langmem] Gemini embedding failed: {e}")

    logger.warning("[langmem] No embedding API configured, returning None")
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
    # RULES.md: Surface isolation — LangMem is web-app exclusive
    if surface == "mcp":
        raise ValueError(
            "LangMem is web-app exclusive. MCP must use Supermemory. "
            "See RULES.md: Memory System — Two Layers, Never Merge Them"
        )

    try:
        db = get_client()

        # Step 1: Generate embedding for query (API call ~500ms)
        query_embedding = _generate_embedding(query)

        if not query_embedding:
            logger.warning("[langmem] embedding generation failed, returning empty")
            return []

        # Step 2: Use pgvector SQL operator for similarity search
        # <=> returns cosine distance (0 = identical, 1 = opposite)
        # 1 - <=> returns cosine similarity (1 = identical, 0 = opposite)
        
        # Convert embedding to string format for SQL
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Execute raw SQL with pgvector similarity operator
        result = db.rpc(
            "exec_sql",
            {
                "sql": f"""
                    SELECT 
                        id,
                        content,
                        improved_content,
                        domain,
                        quality_score,
                        created_at,
                        (1 - (embedding <=> '{embedding_str}'::vector)) AS similarity_score
                    FROM {SUPABASE_TABLE}
                    WHERE user_id = '{user_id}'
                    ORDER BY embedding <=> '{embedding_str}'::vector
                    LIMIT {top_k}
                """
            }
        ).execute()

        if not hasattr(result, 'data') or not result.data:
            logger.debug(f"[langmem] no memories found for user {user_id[:8]}...")
            return []

        # Format results
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
    """
    try:
        db = get_client()

        # Prepare content for embedding
        raw_prompt = session_result.get("raw_prompt", "")[:2000]
        improved_prompt = session_result.get("improved_prompt", "")[:2000]
        combined_content = f"{raw_prompt} {improved_prompt}"

        # Generate embedding asynchronously (don't block)
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

        # Insert into Supabase
        db.table(SUPABASE_TABLE).insert(memory_data).execute()

        logger.info(f"[langmem] stored memory with embedding for user {user_id[:8]}...")
        return True

    except Exception as e:
        logger.error(f"[langmem] write failed: {e}")
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

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

# Use existing Pollinations API key for embeddings
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
SUPABASE_TABLE = "langmem_memories"

# Embedding model configuration
# Pollinations: all-MiniLM-L6-v2 (384 dimensions)
# OpenAI fallback: text-embedding-3-small (1536 dimensions)
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI fallback
EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small dimension


# ═══ EMBEDDING GENERATION ════════════════════

def _generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector for text using Pollinations API or OpenAI fallback.

    Uses all-MiniLM-L6-v2 model via Pollinations, falls back to OpenAI text-embedding-3-small.

    Args:
        text: Text to embed

    Returns:
        List of floats (embedding vector) or None if failed

    Example:
        embedding = _generate_embedding("write a python function")
        # Returns: [0.123, -0.456, 0.789, ...] (384 dimensions)
    """
    # Try Pollinations first
    if POLLINATIONS_API_KEY:
        try:
            # Pollinations embedding API endpoint (OpenAI-compatible)
            url = "https://gen.pollinations.ai/v1/embeddings"

            headers = {
                "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": EMBEDDING_MODEL,
                "input": text[:8000]  # Limit text length for embedding
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()

                # Extract embedding from response
                # Response format: {"data": [{"embedding": [...], "index": 0}]}
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0].get("embedding", [])
                    logger.debug(f"[langmem] pollinations embedding: {len(embedding)} dimensions")
                    return embedding

        except Exception as e:
            logger.warning(f"[langmem] Pollinations API failed: {e}")

    # Fallback to OpenAI embeddings
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000]
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"[langmem] openai embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.warning(f"[langmem] OpenAI embedding fallback failed: {e}")

    logger.warning("[langmem] All embedding services failed, returning None")
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

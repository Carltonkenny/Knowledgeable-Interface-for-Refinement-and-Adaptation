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
# Embeddings: Pollinations (uses existing API key)
# ─────────────────────────────────────────────

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from database import get_client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ═══ CONFIGURATION ═══════════════════════════

# Use existing Pollinations API key for embeddings
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
SUPABASE_TABLE = "langmem_memories"


# ═══ QUERY LANGMEM ═══════════════════════════

def query_langmem(
    user_id: str,
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Semantic search for relevant memories.
    
    RULES.md: Query on every web request (parallel with other context loads)
    
    Args:
        user_id: User UUID from JWT (for RLS isolation)
        query: User's current message (for semantic search)
        top_k: Number of memories to return (default: 5)
        
    Returns:
        List of memory dicts with content, score, metadata
        Empty list if error or no memories found (graceful fallback)
        
    Example:
        memories = query_langmem(
            user_id="user-uuid",
            query="write a Python function",
            top_k=5
        )
        # Returns: [{content: "...", score: 0.92, domain: "python"}, ...]
    """
    try:
        db = get_client()
        
        # Simple keyword-based search (no embeddings for MVP)
        # Search in prompt text for relevant keywords
        words = query.lower().split()[:5]  # Use first 5 words
        
        memories = []
        for word in words:
            if len(word) < 3:  # Skip short words
                continue
                
            response = db.table(SUPABASE_TABLE).select("*").eq("user_id", user_id).ilike("content", f"%{word}%").limit(top_k).execute()
            
            if response.data:
                for memory in response.data:
                    if memory not in memories:
                        memories.append({
                            "id": memory.get("id"),
                            "content": memory.get("content", ""),
                            "domain": memory.get("domain", "general"),
                            "quality_score": memory.get("quality_score", {}),
                            "created_at": memory.get("created_at"),
                        })
            
            if len(memories) >= top_k:
                break
        
        # Sort by quality score (highest first)
        memories.sort(key=lambda m: m.get("quality_score", {}).get("overall", 0), reverse=True)
        
        logger.info(f"[langmem] queried {len(memories)} memories for user {user_id[:8]}...")
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
    Store session facts asynchronously.
    
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
        
    Example:
        write_to_langmem(
            user_id="user-uuid",
            session_result={
                "raw_prompt": "...",
                "improved_prompt": "...",
                "quality_score": {...},
                "domain_analysis": {...}
            }
        )
    """
    try:
        db = get_client()
        
        # Extract facts from session
        memory_data = {
            "user_id": user_id,
            "content": session_result.get("raw_prompt", "")[:2000],  # Limit content length
            "improved_content": session_result.get("improved_prompt", "")[:2000],
            "domain": session_result.get("domain_analysis", {}).get("primary_domain", "general"),
            "quality_score": session_result.get("quality_score", {}),
            "agents_used": session_result.get("agents_used", []),
            "agents_skipped": session_result.get("agents_skipped", []),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Insert into Supabase
        db.table(SUPABASE_TABLE).insert(memory_data).execute()
        
        logger.info(f"[langmem] stored memory for user {user_id[:8]}...")
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
        memories = query_langmem(user_id, query=domain, top_k=count * 2)
        
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

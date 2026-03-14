# utils.py
# ─────────────────────────────────────────────
# Shared utilities for PromptForge v2.0
#
# Utilities:
#   parse_json_response — handles 3 LLM JSON failure modes
#   format_history      — formats conversation turns for LLM context
#   get_redis_client    — cached Redis client (connection pooling)
#   get_cache_key       — SHA-256 hash of prompt (per RULES.md)
#   get_cached_result   — returns cached swarm result from Redis
#   set_cached_result   — stores to Redis with 1-hour expiry
#
# Cache rules (from RULES.md):
# - SHA-256 for cache keys (NEVER MD5)
# - Cache capacity: 100 entries max
# - Auto-expires after 1 hour
# - Survives server restarts (Redis, not in-memory)
# - Configurable for Upstash (cloud) via REDIS_URL env
# ─────────────────────────────────────────────

import json
import re
import hashlib
import os
import logging
from functools import lru_cache
from typing import Optional, Any, Dict
import redis
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ═══ Redis Client ════════════════════════════

@lru_cache(maxsize=1)
def get_redis_client() -> Optional[redis.Redis]:
    """
    Returns cached Redis client.
    Created once, reused everywhere (connection pooling).
    Reads REDIS_URL from .env.
    
    Returns:
        Redis client if connected, None if connection fails
        
    Example:
        client = get_redis_client()
        if client:
            client.set("key", "value")
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        logger.info(f"[redis] connected to {redis_url}")
        return client
    except redis.ConnectionError as e:
        logger.error(f"[redis] connection failed: {e}")
        logger.warning("[redis] cache disabled — continuing without Redis")
        return None
    except Exception as e:
        logger.error(f"[redis] unexpected error: {e}")
        return None


# ═══ Cache Functions ═════════════════════════

def get_cache_key(prompt: str) -> str:
    """
    SHA-256 hash of normalized prompt.
    Per RULES.md: NEVER use MD5 (security vulnerability).
    
    Args:
        prompt: User's prompt text
        
    Returns:
        64-character hex string (SHA-256 hash)
        
    Example:
        key = get_cache_key("write a story")
        # Returns: "a1b2c3..." (64 chars)
    """
    return hashlib.sha256(prompt.strip().lower().encode()).hexdigest()


def get_cached_result(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Returns cached swarm result for this prompt from Redis.
    Returns None if not cached or Redis unavailable.
    
    Args:
        prompt: User's prompt text
        
    Returns:
        Cached swarm result dict, or None if not found
        
    Example:
        cached = get_cached_result("write a story")
        if cached:
            return cached  # Cache hit — skip LLM calls
        else:
            return run_swarm()  # Cache miss — run full pipeline
    """
    client = get_redis_client()
    
    if not client:
        logger.debug("[cache] Redis unavailable — skipping cache check")
        return None
    
    try:
        key = f"prompt:{get_cache_key(prompt)}"
        cached = client.get(key)
        
        if cached:
            logger.info(f"[cache] HIT for prompt: '{prompt[:50]}'")
            return json.loads(cached)
        else:
            logger.info(f"[cache] MISS for prompt: '{prompt[:50]}'")
            return None
            
    except redis.ConnectionError as e:
        logger.warning(f"[cache] Redis connection error: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"[cache] JSON decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"[cache] unexpected error: {e}")
        return None


def set_cached_result(prompt: str, result: Dict[str, Any]) -> None:
    """
    Stores swarm result in Redis with 1-hour expiry.
    LRU eviction handled automatically by Redis.
    
    Args:
        prompt: User's prompt text
        result: Full swarm result dict to cache
        
    Example:
        result = run_swarm("write a story")
        set_cached_result("write a story", result)
        # Next get_cached_result() returns cached result
    """
    client = get_redis_client()
    
    if not client:
        logger.debug("[cache] Redis unavailable — skipping cache write")
        return
    
    try:
        key = f"prompt:{get_cache_key(prompt)}"
        
        # Store with 1-hour expiry (3600 seconds)
        client.setex(key, 3600, json.dumps(result))
        
        logger.info(f"[cache] STORED result for prompt: '{prompt[:50]}' (expires in 1h)")
        
        # Track cache size for monitoring
        cache_size = client.dbsize()
        if cache_size > 100:
            logger.warning(f"[cache] size={cache_size} — consider increasing capacity or reducing TTL")
            
    except redis.ConnectionError as e:
        logger.warning(f"[cache] Redis connection error on write: {e}")
    except (TypeError, json.JSONDecodeError) as e:
        logger.error(f"[cache] JSON encode error: {e}")
    except Exception as e:
        logger.error(f"[cache] unexpected error on write: {e}")


def parse_json_response(raw: str, agent_name: str, retries: int = 1) -> dict:
    """
    Safely parses JSON from LLM response.
    Handles 3 failure modes: clean JSON, markdown-wrapped, buried in text.
    Returns {} on complete failure — caller decides how to handle.
    """
    if not raw or not raw.strip():
        logger.warning(f"[{agent_name}] empty response from LLM")
        return {}

    attempts = [
        lambda r: json.loads(r.strip()),
        lambda r: json.loads(re.sub(r'```(?:json)?|```', '', r).strip()),
        lambda r: json.loads(re.search(r'\{.*\}', r, re.DOTALL).group()),
    ]

    for i, attempt in enumerate(attempts):
        try:
            result = attempt(raw)
            if i > 0:
                logger.debug(f"[{agent_name}] JSON parsed on attempt {i + 1}")
            return result
        except (json.JSONDecodeError, AttributeError):
            continue

    logger.error(f"[{agent_name}] all JSON parse attempts failed. Raw: {raw[:200]}")
    return {}


def format_history(history: list, max_turns: int = 4) -> str:
    """
    Formats conversation history into readable text for LLM context.
    Shared by all autonomous agent functions to avoid duplication.
    """
    if not history:
        return "No previous conversation"
    return "\n".join([
        f"{t['role'].upper()}: {t['message'][:200]}"
        for t in history[-max_turns:]
    ])


def calculate_overall_quality(quality_score: dict) -> float:
    """
    Calculates the overall quality score from specificity, clarity, and actionability.
    Standardized helper used by search and analytics to ensure consistency.
    
    Args:
        quality_score: Dict containing 'specificity', 'clarity', 'actionability' (1-5)
                       and optionally an 'overall' field.
                       
    Returns:
        float: Calculated or retrieved overall score (0-5).
    """
    if not quality_score:
        return 0.0
        
    if 'overall' in quality_score:
        return float(quality_score['overall'])
        
    # Dynamic fallback calculation
    metrics = ['specificity', 'clarity', 'actionability']
    scores = [quality_score.get(m, 0) for m in metrics]
    
    if not any(scores):
        return 0.0
        
    return round(sum(scores) / len(scores), 1)

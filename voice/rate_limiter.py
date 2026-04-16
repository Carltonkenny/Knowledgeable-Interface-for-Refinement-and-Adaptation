# voice/rate_limiter.py
# ─────────────────────────────────────────────
# Redis-based Rate Limiting for Voice Endpoints
#
# WHY: Voice APIs have higher cost per request than text. Separate
# rate limits prevent budget overruns while allowing normal text usage.
#
# Implements sliding window algorithm using Redis sorted sets.
# Decorator pattern for easy application to any endpoint.
#
# Limits (configurable via .env):
#   /transcribe: 10/min, 50/hr per user
#   /tts:        5/min, 30/hr per user
#
# Returns 429 with Retry-After header when exceeded.
# ─────────────────────────────────────────────

import os
import time
import logging
import functools
from typing import Optional, Tuple, Callable, Any
from fastapi import HTTPException, Request

from utils import get_redis_client

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────

VOICE_RATE_LIMIT_ENABLED = os.getenv("VOICE_RATE_LIMIT_ENABLED", "true").lower() == "true"

# Transcription limits
TRANSCRIBE_PER_MINUTE = int(os.getenv("VOICE_TRANSCRIBE_PER_MINUTE", "10"))
TRANSCRIBE_PER_HOUR = int(os.getenv("VOICE_TRANSCRIBE_PER_HOUR", "50"))

# TTS limits
TTS_PER_MINUTE = int(os.getenv("VOICE_TTS_PER_MINUTE", "5"))
TTS_PER_HOUR = int(os.getenv("VOICE_TTS_PER_HOUR", "30"))

# Redis key prefixes
_TRANSCRIBE_MIN_KEY = "voice:rate:transcribe:min"
_TRANSCRIBE_HOUR_KEY = "voice:rate:transcribe:hour"
_TTS_MIN_KEY = "voice:rate:tts:min"
_TTS_HOUR_KEY = "voice:rate:tts:hour"


def _get_window_key(base_key: str, window_seconds: int) -> str:
    """
    Generate time-bucketed Redis key for sliding window.

    Args:
        base_key: Base Redis key prefix
        window_seconds: Window size in seconds

    Returns:
        Time-bucketed key like "voice:rate:tts:min:1712345600"
    """
    window = int(time.time()) // window_seconds
    return f"{base_key}:{window}"


def _check_and_increment(
    redis_key: str,
    limit: int,
    window_seconds: int,
    user_id: str
) -> Tuple[bool, int, int]:
    """
    Check rate limit and increment counter using Redis atomic operations.

    Uses INCR with EXPIRE for automatic window cleanup.

    Args:
        redis_key: Redis key (will be appended with user_id)
        limit: Maximum requests allowed in window
        window_seconds: Window duration in seconds
        user_id: User identifier

    Returns:
        Tuple of (is_allowed, current_count, remaining)
    """
    client = get_redis_client()

    if not client:
        # Redis unavailable — allow request (fail open for availability)
        logger.warning("[voice/rate_limiter] Redis unavailable — allowing request")
        return True, 0, limit

    key = f"{redis_key}:{user_id}"

    try:
        # Atomic increment with TTL
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        results = pipe.execute()

        current_count = results[0] if results else 0
        remaining = max(0, limit - current_count)
        is_allowed = current_count <= limit

        if not is_allowed:
            logger.warning(
                f"[voice/rate_limiter] limit exceeded: user={user_id[:8]}... "
                f"key={redis_key} count={current_count}/{limit}"
            )

        return is_allowed, current_count, remaining

    except Exception as e:
        logger.error(f"[voice/rate_limiter] Redis error: {e}")
        # Fail open — allow request on Redis error
        return True, 0, limit


def check_voice_rate_limit(
    user_id: str,
    endpoint: str = "transcribe"
) -> Tuple[bool, str, dict]:
    """
    Check voice rate limits for a user on a specific endpoint.

    WHY: Called before processing to enforce per-endpoint rate limits.
    Separate limits for transcription vs TTS because cost profiles differ.

    Args:
        user_id: User UUID from JWT
        endpoint: "transcribe" or "tts"

    Returns:
        Tuple of (is_allowed, error_message, rate_limit_headers)

    Example:
        allowed, error, headers = check_voice_rate_limit(user_id, "transcribe")
        if not allowed:
            raise HTTPException(429, error)
    """
    if not VOICE_RATE_LIMIT_ENABLED:
        return True, "", {}

    now = time.time()
    headers = {}

    if endpoint == "transcribe":
        # Check per-minute limit
        min_key = _get_window_key(_TRANSCRIBE_MIN_KEY, 60)
        allowed_min, count_min, remaining_min = _check_and_increment(
            min_key, TRANSCRIBE_PER_MINUTE, 60, user_id
        )

        if not allowed_min:
            retry_after = 60 - (int(now) % 60)
            headers["Retry-After"] = str(retry_after)
            headers["X-RateLimit-Limit"] = str(TRANSCRIBE_PER_MINUTE)
            headers["X-RateLimit-Remaining"] = "0"
            headers["X-RateLimit-Reset"] = str(int(now) + retry_after)
            return False, f"Transcription rate limit exceeded ({TRANSCRIBE_PER_MINUTE}/min). Retry in {retry_after}s.", headers

        # Check per-hour limit
        hour_key = _get_window_key(_TRANSCRIBE_HOUR_KEY, 3600)
        allowed_hr, count_hr, remaining_hr = _check_and_increment(
            hour_key, TRANSCRIBE_PER_HOUR, 3600, user_id
        )

        if not allowed_hr:
            retry_after = 3600 - (int(now) % 3600)
            headers["Retry-After"] = str(retry_after)
            headers["X-RateLimit-Limit"] = str(TRANSCRIBE_PER_HOUR)
            headers["X-RateLimit-Remaining"] = "0"
            headers["X-RateLimit-Reset"] = str(int(now) + retry_after)
            return False, f"Transcription hourly limit exceeded ({TRANSCRIBE_PER_HOUR}/hr). Retry in {retry_after}s.", headers

        # Add remaining headers for successful requests
        headers["X-RateLimit-Limit-Minute"] = str(TRANSCRIBE_PER_MINUTE)
        headers["X-RateLimit-Remaining-Minute"] = str(remaining_min)
        headers["X-RateLimit-Limit-Hour"] = str(TRANSCRIBE_PER_HOUR)
        headers["X-RateLimit-Remaining-Hour"] = str(remaining_hr)

    elif endpoint == "tts":
        # Check per-minute limit
        min_key = _get_window_key(_TTS_MIN_KEY, 60)
        allowed_min, count_min, remaining_min = _check_and_increment(
            min_key, TTS_PER_MINUTE, 60, user_id
        )

        if not allowed_min:
            retry_after = 60 - (int(now) % 60)
            headers["Retry-After"] = str(retry_after)
            headers["X-RateLimit-Limit"] = str(TTS_PER_MINUTE)
            headers["X-RateLimit-Remaining"] = "0"
            headers["X-RateLimit-Reset"] = str(int(now) + retry_after)
            return False, f"TTS rate limit exceeded ({TTS_PER_MINUTE}/min). Retry in {retry_after}s.", headers

        # Check per-hour limit
        hour_key = _get_window_key(_TTS_HOUR_KEY, 3600)
        allowed_hr, count_hr, remaining_hr = _check_and_increment(
            hour_key, TTS_PER_HOUR, 3600, user_id
        )

        if not allowed_hr:
            retry_after = 3600 - (int(now) % 3600)
            headers["Retry-After"] = str(retry_after)
            headers["X-RateLimit-Limit"] = str(TTS_PER_HOUR)
            headers["X-RateLimit-Remaining"] = "0"
            headers["X-RateLimit-Reset"] = str(int(now) + retry_after)
            return False, f"TTS hourly limit exceeded ({TTS_PER_HOUR}/hr). Retry in {retry_after}s.", headers

        headers["X-RateLimit-Limit-Minute"] = str(TTS_PER_MINUTE)
        headers["X-RateLimit-Remaining-Minute"] = str(remaining_min)
        headers["X-RateLimit-Limit-Hour"] = str(TTS_PER_HOUR)
        headers["X-RateLimit-Remaining-Hour"] = str(remaining_hr)

    return True, "", headers


def rate_limit(endpoint: str = "transcribe"):
    """
    Decorator for applying voice rate limits to FastAPI endpoints.

    WHY: Decorator pattern keeps endpoint code clean and reusable.
    Can be applied to any voice-related endpoint.

    Args:
        endpoint: "transcribe" or "tts" — determines which limits apply

    Example:
        @router.post("/transcribe")
        @rate_limit("transcribe")
        async def transcribe(audio: UploadFile, user: User = Depends(get_current_user)):
            ...

        @router.post("/tts")
        @rate_limit("tts")
        async def text_to_speech(req: TTSRequest, user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract user from kwargs (FastAPI dependency injection)
            user = kwargs.get("user")
            if user and hasattr(user, "user_id"):
                user_id = user.user_id
            else:
                # If no user found, let the request through
                logger.warning("[voice/rate_limiter] Could not extract user_id — allowing request")
                return await func(*args, **kwargs)

            # Check rate limit
            allowed, error_msg, headers = check_voice_rate_limit(user_id, endpoint)

            if not allowed:
                retry_after = int(headers.get("Retry-After", 60))
                raise HTTPException(
                    status_code=429,
                    detail=error_msg,
                    headers=headers
                )

            # Call the actual endpoint
            response = await func(*args, **kwargs)

            # Add rate limit headers to response if it's a Response object
            if hasattr(response, "headers"):
                for key, value in headers.items():
                    response.headers[key] = value

            return response

        return wrapper
    return decorator

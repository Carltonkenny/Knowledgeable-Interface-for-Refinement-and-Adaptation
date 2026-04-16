# voice/cost_tracker.py
# ─────────────────────────────────────────────
# Cost Tracking and Budget Enforcement for Voice APIs
#
# WHY: Voice APIs (Whisper, ElevenLabs) are significantly more expensive
# than text LLM calls. Without cost tracking, users can accidentally
# run up large bills. Budget caps prevent surprise charges.
#
# Pricing model:
#   Transcription (Whisper): $0.00004/sec of audio
#   TTS (Pollinations):     FREE
#   TTS (ElevenLabs):       ~$0.0003/character (varies by plan)
#
# Budget enforcement:
#   Monthly cap: $10 default (configurable)
#   80% warning: Logged when approaching cap
#   100% block: Return 429 when budget exhausted
#
# Tracking key: voice:costs:{user_id}:{year-month}
# ─────────────────────────────────────────────

import os
import time
import logging
from typing import Optional, Tuple
from datetime import datetime, timezone

from utils import get_redis_client

logger = logging.getLogger(__name__)

# ── Pricing Configuration ─────────────────────

# Pollinations Whisper pricing: $0.00004 per second of audio
TRANSCRIBE_COST_PER_SECOND = float(os.getenv("VOICE_TRANSCRIBE_COST_PER_SEC", "0.00004"))

# Pollinations TTS is FREE
TTS_POLLINATIONS_COST_PER_CHAR = 0.0

# ElevenLabs pricing: ~$0.0003 per character (varies by plan)
TTS_ELEVENLABS_COST_PER_CHAR = float(os.getenv("VOICE_TTS_ELEVENLABS_COST_PER_CHAR", "0.0003"))

# Budget configuration
MONTHLY_BUDGET_USD = float(os.getenv("VOICE_MONTHLY_BUDGET_USD", "10.0"))
BUDGET_WARNING_THRESHOLD = 0.8  # 80% → log warning
BUDGET_BLOCK_THRESHOLD = 1.0    # 100% → block requests


def _get_cost_key(user_id: str) -> str:
    """
    Generate Redis key for monthly cost tracking.

    Format: voice:costs:{user_id}:{year-month}
    Example: voice:costs:abc123:2026-04

    Args:
        user_id: User UUID

    Returns:
        Redis key string
    """
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m")
    return f"voice:costs:{user_id}:{month_str}"


def _get_total_spend_key() -> str:
    """
    Generate Redis key for total monthly spend across all users.

    Format: voice:costs:total:{year-month}
    """
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m")
    return f"voice:costs:total:{month_str}"


def track_cost(
    user_id: str,
    service: str,
    duration_seconds: float = 0.0,
    char_count: int = 0,
    provider: str = "pollinations"
) -> float:
    """
    Track the cost of a voice API call and update Redis counters.

    WHY: Called after each successful voice request to accumulate costs.
    Separates per-user and total tracking for billing and monitoring.

    Args:
        user_id: User UUID
        service: "transcribe" or "tts"
        duration_seconds: Audio duration in seconds (for transcription)
        char_count: Character count (for TTS)
        provider: "pollinations" or "elevenlabs"

    Returns:
        Cost in USD for this request

    Example:
        cost = track_cost(user_id, "transcribe", duration_seconds=15.5)
        # cost = 15.5 * 0.00004 = $0.00062
    """
    # Calculate cost based on service and provider
    if service == "transcribe":
        cost = duration_seconds * TRANSCRIBE_COST_PER_SECOND
    elif service == "tts":
        if provider == "elevenlabs":
            cost = char_count * TTS_ELEVENLABS_COST_PER_CHAR
        else:
            # Pollinations is free
            cost = char_count * TTS_POLLINATIONS_COST_PER_CHAR
    else:
        logger.warning(f"[voice/cost_tracker] Unknown service: {service}")
        return 0.0

    if cost <= 0:
        return 0.0

    # Update Redis counters
    client = get_redis_client()
    if not client:
        logger.warning("[voice/cost_tracker] Redis unavailable — cost not tracked")
        return cost

    user_key = _get_cost_key(user_id)
    total_key = _get_total_spend_key()

    try:
        pipe = client.pipeline()
        pipe.hincrbyfloat(user_key, "total_spent", cost)
        pipe.hincrby(user_key, "request_count", 1)
        # Track total spend across all users
        pipe.hincrbyfloat(total_key, "total_spent", cost)
        pipe.hincrby(total_key, "request_count", 1)
        # Set 90-day expiry on keys (auto-cleanup)
        for key in [user_key, total_key]:
            pipe.expire(key, 90 * 24 * 3600)
        pipe.execute()

        logger.debug(
            f"[voice/cost_tracker] tracked ${cost:.6f} for user={user_id[:8]}... "
            f"service={service} provider={provider}"
        )

    except Exception as e:
        logger.error(f"[voice/cost_tracker] Redis error: {e}")

    return cost


def check_budget(user_id: str) -> Tuple[bool, str, float]:
    """
    Check if user has remaining voice budget for this month.

    WHY: Called BEFORE processing to prevent budget overruns.
    Returns clear messaging when budget is exhausted.

    Args:
        user_id: User UUID

    Returns:
        Tuple of (is_allowed, error_message, current_monthly_spend)

    Example:
        allowed, error, spend = check_budget(user_id)
        if not allowed:
            raise HTTPException(429, error)
    """
    monthly_spend = get_monthly_spend(user_id)
    budget_ratio = monthly_spend / MONTHLY_BUDGET_USD if MONTHLY_BUDGET_USD > 0 else 0

    # Log warning at 80% threshold
    if budget_ratio >= BUDGET_WARNING_THRESHOLD and budget_ratio < BUDGET_BLOCK_THRESHOLD:
        remaining = MONTHLY_BUDGET_USD - monthly_spend
        logger.warning(
            f"[voice/cost_tracker] budget warning: user={user_id[:8]}... "
            f"spent=${monthly_spend:.2f}/${MONTHLY_BUDGET_USD:.2f} "
            f"({budget_ratio*100:.0f}%) — ${remaining:.2f} remaining"
        )

    # Block at 100%
    if budget_ratio >= BUDGET_BLOCK_THRESHOLD:
        error_msg = (
            f"Voice budget exhausted. You've used ${monthly_spend:.2f} of your "
            f"${MONTHLY_BUDGET_USD:.2f} monthly budget. Voice features are paused "
            f"until next billing cycle."
        )
        logger.warning(
            f"[voice/cost_tracker] budget exhausted: user={user_id[:8]}... "
            f"spent=${monthly_spend:.2f}"
        )
        return False, error_msg, monthly_spend

    return True, "", monthly_spend


def get_monthly_spend(user_id: str) -> float:
    """
    Get user's total voice spend for the current month.

    Args:
        user_id: User UUID

    Returns:
        Monthly spend in USD (0.0 if Redis unavailable or no data)

    Example:
        spend = get_monthly_spend("user-uuid")
        # spend = 3.45
    """
    client = get_redis_client()
    if not client:
        return 0.0

    user_key = _get_cost_key(user_id)

    try:
        total_spent = client.hget(user_key, "total_spent")
        return float(total_spent) if total_spent else 0.0
    except Exception as e:
        logger.error(f"[voice/cost_tracker] Redis error: {e}")
        return 0.0


def get_total_monthly_spend() -> float:
    """
    Get total voice spend across ALL users for the current month.

    Returns:
        Total monthly spend in USD

    Example:
        total = get_total_monthly_spend()
        # total = 45.67
    """
    client = get_redis_client()
    if not client:
        return 0.0

    total_key = _get_total_spend_key()

    try:
        total_spent = client.hget(total_key, "total_spent")
        return float(total_spent) if total_spent else 0.0
    except Exception as e:
        logger.error(f"[voice/cost_tracker] Redis error: {e}")
        return 0.0


def get_cost_breakdown(user_id: str) -> dict:
    """
    Get detailed cost breakdown for user's current month.

    Args:
        user_id: User UUID

    Returns:
        Dict with total_spent, request_count, budget_remaining, budget_pct_used
    """
    client = get_redis_client()
    if not client:
        return {"total_spent": 0.0, "request_count": 0, "budget_remaining": MONTHLY_BUDGET_USD, "budget_pct_used": 0.0}

    user_key = _get_cost_key(user_id)

    try:
        data = client.hgetall(user_key)
        total_spent = float(data.get("total_spent", 0.0))
        request_count = int(data.get("request_count", 0))
        budget_remaining = max(0.0, MONTHLY_BUDGET_USD - total_spent)
        budget_pct_used = (total_spent / MONTHLY_BUDGET_USD * 100) if MONTHLY_BUDGET_USD > 0 else 0.0

        return {
            "total_spent": round(total_spent, 4),
            "request_count": request_count,
            "budget_remaining": round(budget_remaining, 4),
            "budget_pct_used": round(budget_pct_used, 1),
            "monthly_budget": MONTHLY_BUDGET_USD,
        }
    except Exception as e:
        logger.error(f"[voice/cost_tracker] Redis error: {e}")
        return {"total_spent": 0.0, "request_count": 0, "budget_remaining": MONTHLY_BUDGET_USD, "budget_pct_used": 0.0}

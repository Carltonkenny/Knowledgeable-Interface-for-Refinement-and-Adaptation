# voice/metrics.py
# ─────────────────────────────────────────────
# Voice Observability Metrics Collection
#
# WHY: Production systems need real-time visibility into voice API
# health, performance, and cost. Metrics enable dashboards, alerts,
# and capacity planning.
#
# Tracks:
#   - Total requests, success rate, error rate
#   - Latency (average, p95, p99)
#   - Cost per user, total monthly spend
#   - Provider breakdown (Pollinations vs ElevenLabs)
#
# Storage: Redis hashes for real-time dashboard access.
# Also emits structured JSON logs for external monitoring (Sentry).
# ─────────────────────────────────────────────

import os
import time
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime, timezone

from utils import get_redis_client

logger = logging.getLogger(__name__)

# Redis key prefixes
_METRICS_PREFIX = "voice:metrics"
_LATENCY_KEY = f"{_METRICS_PREFIX}:latency"
_REQUESTS_KEY = f"{_METRICS_PREFIX}:requests"
_ERRORS_KEY = f"{_METRICS_PREFIX}:errors"
_PROVIDER_KEY = f"{_METRICS_PREFIX}:provider"


def _get_daily_key(metric: str) -> str:
    """
    Generate date-bucketed Redis key for daily metrics.

    Args:
        metric: Metric name (latency, requests, errors, provider)

    Returns:
        Key like "voice:metrics:requests:2026-04-09"
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{_METRICS_PREFIX}:{metric}:{today}"


def record_voice_metric(
    service: str,
    success: bool,
    latency_ms: float,
    user_id: Optional[str] = None,
    provider: str = "pollinations",
    error_type: Optional[str] = None
) -> None:
    """
    Record a voice API request metric to Redis.

    WHY: Called after EVERY voice request (success or failure) to maintain
    accurate real-time metrics. Single call captures all needed data.

    Args:
        service: "transcribe" or "tts"
        success: Whether the request succeeded
        latency_ms: Request duration in milliseconds
        user_id: Optional user UUID for per-user tracking
        provider: "pollinations" or "elevenlabs"
        error_type: Error category if failed (e.g., "timeout", "api_error")

    Example:
        record_voice_metric(
            service="transcribe",
            success=True,
            latency_ms=2340.5,
            user_id="abc123",
            provider="pollinations"
        )
    """
    client = get_redis_client()
    if not client:
        return  # Metrics are non-critical — fail silently

    try:
        pipe = client.pipeline()

        # ── Request count ──
        req_key = _get_daily_key("requests")
        pipe.hincrby(req_key, f"{service}:total", 1)
        pipe.hincrby(req_key, f"{service}:success" if success else f"{service}:error", 1)

        # ── Latency tracking (store individual values for percentile calc) ──
        lat_key = _get_daily_key("latency")
        pipe.lpush(f"{lat_key}:{service}", str(latency_ms))
        # Keep only last 1000 latency samples per service per day
        pipe.ltrim(f"{lat_key}:{service}", 0, 999)

        # ── Error tracking ──
        err_key = None
        if not success and error_type:
            err_key = _get_daily_key("errors")
            pipe.hincrby(err_key, f"{service}:{error_type}", 1)

        # ── Provider breakdown ──
        prov_key = _get_daily_key("provider")
        pipe.hincrby(prov_key, f"{provider}:{service}:total", 1)
        if success:
            pipe.hincrby(prov_key, f"{provider}:{service}:success", 1)

        # ── Per-user tracking (optional) ──
        if user_id:
            user_key = f"{_METRICS_PREFIX}:user:{user_id}"
            pipe.hincrby(user_key, f"{service}:total", 1)
            pipe.hincrby(user_key, f"{service}:success" if success else f"{service}:error", 1)
            pipe.expire(user_key, 30 * 24 * 3600)  # 30-day expiry

        # ── Set expiry on daily keys ──
        expiry_keys = [req_key, lat_key, prov_key]
        if err_key:
            expiry_keys.append(err_key)
        for key in expiry_keys:
            pipe.expire(key, 24 * 3600)  # 24-hour expiry

        pipe.execute()

        # ── Structured JSON log for external monitoring ──
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": service,
            "success": success,
            "latency_ms": round(latency_ms, 1),
            "provider": provider,
            "user_id": user_id[:8] + "..." if user_id else None,
        }
        if error_type:
            log_entry["error_type"] = error_type

        if success:
            logger.info(f"[voice/metrics] {json.dumps(log_entry)}")
        else:
            logger.warning(f"[voice/metrics] {json.dumps(log_entry)}")

    except Exception as e:
        logger.error(f"[voice/metrics] Redis error: {e}")


def _calculate_percentile(values: List[float], percentile: float) -> float:
    """
    Calculate percentile from a list of values.

    Args:
        values: List of numeric values
        percentile: Percentile to calculate (e.g., 95 for p95)

    Returns:
        Percentile value
    """
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    index = min(index, len(sorted_values) - 1)
    return sorted_values[index]


def get_voice_metrics(service: Optional[str] = None) -> dict:
    """
    Retrieve aggregated voice metrics from Redis.

    WHY: Called by admin dashboard and GET /voice/metrics endpoint
    to display real-time health of voice APIs.

    Args:
        service: Optional filter ("transcribe" or "tts")

    Returns:
        Dict with aggregated metrics including success rate, latency percentiles

    Example:
        metrics = get_voice_metrics("transcribe")
        # {
        #   "total_requests": 150,
        #   "success_rate": 98.7,
        #   "avg_latency_ms": 2100.0,
        #   "p95_latency_ms": 4500.0,
        #   "p99_latency_ms": 8200.0,
        #   "error_count": 2,
        #   "provider_breakdown": {...}
        # }
    """
    client = get_redis_client()
    if not client:
        return {"error": "Redis unavailable", "metrics": {}}

    services = [service] if service else ["transcribe", "tts"]
    result = {}

    try:
        for svc in services:
            req_key = _get_daily_key("requests")
            lat_key = _get_daily_key("latency")

            # Request counts
            req_data = client.hgetall(req_key)
            total = int(req_data.get(f"{svc}:total", 0))
            success = int(req_data.get(f"{svc}:success", 0))
            errors = int(req_data.get(f"{svc}:error", 0))
            success_rate = (success / total * 100) if total > 0 else 0.0

            # Latency percentiles
            latency_samples = client.lrange(f"{lat_key}:{svc}", 0, -1)
            latency_values = [float(v) for v in latency_samples if v]

            avg_latency = sum(latency_values) / len(latency_values) if latency_values else 0.0
            p95_latency = _calculate_percentile(latency_values, 95)
            p99_latency = _calculate_percentile(latency_values, 99)

            # Error breakdown
            err_key = _get_daily_key("errors")
            error_data = client.hgetall(err_key)
            error_breakdown = {
                k.replace(f"{svc}:", ""): int(v)
                for k, v in error_data.items()
                if k.startswith(f"{svc}:")
            }

            # Provider breakdown
            prov_key = _get_daily_key("provider")
            prov_data = client.hgetall(prov_key)
            provider_breakdown = {
                k.replace(f"{svc}:", ""): int(v)
                for k, v in prov_data.items()
                if k.endswith(f":{svc}:total") or k.endswith(f":{svc}:success")
            }

            result[svc] = {
                "total_requests": total,
                "success_count": success,
                "error_count": errors,
                "success_rate": round(success_rate, 1),
                "avg_latency_ms": round(avg_latency, 1),
                "p95_latency_ms": round(p95_latency, 1),
                "p99_latency_ms": round(p99_latency, 1),
                "error_breakdown": error_breakdown,
                "provider_breakdown": provider_breakdown,
            }

        # Add total spend
        from voice.cost_tracker import get_total_monthly_spend
        result["total_monthly_spend"] = round(get_total_monthly_spend(), 4)
        result["collected_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        logger.error(f"[voice/metrics] Failed to retrieve metrics: {e}")
        result["error"] = str(e)

    return result

# middleware/rate_limiter.py
# ─────────────────────────────────────────────
# Rate Limiting Middleware — RULES.md Security Rule #8
#
# Redis-backed sliding window rate limiter.
# Works across multiple Docker instances — all share the same Redis state.
#
# Configuration (via .env):
# - RATE_LIMIT_ENABLED: Master toggle (true/false)
# - RATE_LIMIT_HOURLY: Max requests per hour (default: 100)
# - RATE_LIMIT_DAILY: Max requests per day (default: 1000)
# - RATE_LIMIT_MONTHLY: Max requests per month (default: 15000)
# - RATE_LIMIT_UNLIMITED_USERS: Comma-separated VIP user IDs
# - REDIS_URL: Redis connection string (default: redis://redis:6379)
#
# RULES.md Compliance:
# - Rate limiting per user_id
# - Returns 429 when limit exceeded
# - Works with JWT authentication
# - Master toggle for dev/demo flexibility
# - VIP bypass for admin/friends/paid users
# ─────────────────────────────────────────────

import os
import time
import logging
import redis
from datetime import datetime, timezone
from typing import Tuple, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── VIP bypass list ──
RATE_LIMIT_UNLIMITED_USERS = [
    uid.strip() for uid in os.getenv("RATE_LIMIT_UNLIMITED_USERS", "").split(",") if uid.strip()
]


class RedisRateLimiter:
    """
    Redis-backed sliding window rate limiter.

    Uses Redis INCR + EXPIRE for atomic counting.
    Works across multiple instances — all share the same Redis state.

    Limits (generous defaults, configurable via .env):
    - Hourly: 100 requests per user
    - Daily: 1000 requests per user
    - Monthly: 15000 requests per user

    VIP users (configured via RATE_LIMIT_UNLIMITED_USERS) bypass all limits.
    """

    def __init__(
        self,
        redis_url: str = "redis://redis:6379",
        hourly_limit: int = 100,
        daily_limit: int = 1000,
        monthly_limit: int = 15000,
    ):
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self._redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._connect()

    def _connect(self):
        """Establish connection to Redis with retry-safe settings."""
        try:
            self._redis = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            self._redis.ping()
            logger.info("[rate_limiter] connected to Redis successfully")
        except Exception as e:
            logger.error(f"[rate_limiter] failed to connect to Redis: {e}")
            self._redis = None

    def _get_redis(self) -> Optional[redis.Redis]:
        """Lazy reconnect if connection dropped."""
        if self._redis is None:
            self._connect()
        return self._redis

    def is_allowed(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user is within rate limits.

        Args:
            user_id: User identifier

        Returns:
            (allowed: bool, reason: str)
        """
        r = self._get_redis()
        if r is None:
            # Redis unavailable — fail open (allow request)
            logger.warning("[rate_limiter] Redis unavailable, allowing request")
            return True, "OK (Redis unavailable)"

        now = int(time.time())
        now_utc = datetime.now(timezone.utc)
        hour_key = f"rate:{user_id}:h:{now // 3600}"
        day_key = f"rate:{user_id}:d:{now_utc.date().isoformat()}"
        month_key = f"rate:{user_id}:m:{now_utc.year}-{now_utc.month:02d}"

        try:
            # Atomic increment + set expiry
            hourly_count = r.incr(hour_key)
            if hourly_count == 1:
                r.expire(hour_key, 3600)

            daily_count = r.incr(day_key)
            if daily_count == 1:
                r.expire(day_key, 86400)

            monthly_count = r.incr(month_key)
            if monthly_count == 1:
                r.expire(month_key, 86400 * 31)

            # Check limits
            if hourly_count > self.hourly_limit:
                return False, f"Hourly limit exceeded ({hourly_count}/{self.hourly_limit})"
            if daily_count > self.daily_limit:
                return False, f"Daily limit exceeded ({daily_count}/{self.daily_limit})"
            if monthly_count > self.monthly_limit:
                return False, f"Monthly limit exceeded ({monthly_count}/{self.monthly_limit})"

            return True, "OK"
        except Exception as e:
            logger.error(f"[rate_limiter] Redis error: {e}")
            return True, "OK (Redis error, fail open)"

    def get_remaining(self, user_id: str) -> Tuple[int, int, int]:
        """
        Get remaining requests in current windows.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (hourly_remaining, daily_remaining, monthly_remaining)
        """
        r = self._get_redis()
        if r is None:
            return self.hourly_limit, self.daily_limit, self.monthly_limit

        now = int(time.time())
        now_utc = datetime.now(timezone.utc)
        hour_key = f"rate:{user_id}:h:{now // 3600}"
        day_key = f"rate:{user_id}:d:{now_utc.date().isoformat()}"
        month_key = f"rate:{user_id}:m:{now_utc.year}-{now_utc.month:02d}"

        try:
            hourly = int(r.get(hour_key) or 0)
            daily = int(r.get(day_key) or 0)
            monthly = int(r.get(month_key) or 0)

            return (
                max(0, self.hourly_limit - hourly),
                max(0, self.daily_limit - daily),
                max(0, self.monthly_limit - monthly),
            )
        except Exception:
            return self.hourly_limit, self.daily_limit, self.monthly_limit


# ── Lazy-init singleton ──
_rate_limiter_instance: Optional[RedisRateLimiter] = None


def get_rate_limiter() -> Optional[RedisRateLimiter]:
    """Get (or create) the global RedisRateLimiter instance."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RedisRateLimiter(
            redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
            hourly_limit=int(os.getenv("RATE_LIMIT_HOURLY", "100")),
            daily_limit=int(os.getenv("RATE_LIMIT_DAILY", "1000")),
            monthly_limit=int(os.getenv("RATE_LIMIT_MONTHLY", "15000")),
        )
    return _rate_limiter_instance


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware — checks Redis rate limits per user.

    Extracts user_id from request.state (set by auth middleware).
    Falls back to IP-based identifier for anonymous requests.
    Returns 429 Too Many Requests when limit exceeded.

    Features:
    - Master toggle (RATE_LIMIT_ENABLED)
    - VIP user bypass (RATE_LIMIT_UNLIMITED_USERS)
    - Hourly, daily, and monthly limits
    - Dev mode auto-disable (ENVIRONMENT=development)
    - Fail-open when Redis is unavailable
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Checks (in order):
        1. Master toggle (RATE_LIMIT_ENABLED)
        2. Dev mode (ENVIRONMENT=development)
        3. Health check skip (/health)
        4. CORS preflight skip (OPTIONS)
        5. VIP user bypass (RATE_LIMIT_UNLIMITED_USERS)
        6. Hourly, daily, monthly limits

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response or 429 error
        """
        # ═══ MASTER TOGGLE CHECK ═══
        if os.getenv("RATE_LIMIT_ENABLED", "true").lower() != "true":
            logger.debug("[rate_limiter] DISABLED via master toggle")
            return await call_next(request)

        # ═══ DEV MODE AUTO-DISABLE ═══
        if os.getenv("ENVIRONMENT", "development") == "development":
            logger.debug("[rate_limiter] DEV MODE - skipping rate limiting")
            return await call_next(request)

        # ═══ SKIP HEALTH CHECK ═══
        if request.url.path == "/health":
            return await call_next(request)

        # ═══ SKIP CORS PREFLIGHT ═══
        if request.method == "OPTIONS":
            return await call_next(request)

        # ═══ EXTRACT USER_ID ═══
        user_id = None

        # Try to get user_id from request.state (set by auth middleware)
        if hasattr(request, 'state') and hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
            if user_id:
                logger.debug(f"[rate_limiter] Using user_id from request.state: {user_id[:8]}...")

        # Fallback: If no user_id from state, use client IP
        if not user_id:
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                client_ip = forwarded_for.split(',')[0].strip()
            else:
                client_ip = request.client.host if request.client else 'unknown'
            user_id = f"anon:{client_ip}"
            logger.debug(f"[rate_limiter] Using IP-based identifier: {user_id}")

        # ═══ VIP USER BYPASS CHECK ═══
        if user_id in RATE_LIMIT_UNLIMITED_USERS:
            logger.debug(f"[rate_limiter] VIP user bypass: {user_id[:8]}...")
            return await call_next(request)

        # ═══ CHECK RATE LIMITS ═══
        limiter = get_rate_limiter()
        if limiter is None:
            return await call_next(request)

        allowed, reason = limiter.is_allowed(user_id)

        if not allowed:
            hourly_rem, daily_rem, monthly_rem = limiter.get_remaining(user_id)
            logger.warning(
                f"[rate_limiter] blocked request for user {user_id[:8]}... "
                f"reason={reason}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": reason,
                    "limits": {
                        "hourly": limiter.hourly_limit,
                        "daily": limiter.daily_limit,
                        "monthly": limiter.monthly_limit,
                    },
                    "remaining": {
                        "hourly": hourly_rem,
                        "daily": daily_rem,
                        "monthly": monthly_rem,
                    },
                },
                headers={
                    'Retry-After': '3600',
                    'X-RateLimit-Limit-Hourly': str(limiter.hourly_limit),
                    'X-RateLimit-Limit-Daily': str(limiter.daily_limit),
                    'X-RateLimit-Limit-Monthly': str(limiter.monthly_limit),
                },
            )

        # ═══ ADD RATE LIMIT HEADERS TO RESPONSE ═══
        response = await call_next(request)
        hourly_rem, daily_rem, monthly_rem = limiter.get_remaining(user_id)
        response.headers['X-RateLimit-Remaining-Hourly'] = str(hourly_rem)
        response.headers['X-RateLimit-Remaining-Daily'] = str(daily_rem)
        response.headers['X-RateLimit-Remaining-Monthly'] = str(monthly_rem)

        return response

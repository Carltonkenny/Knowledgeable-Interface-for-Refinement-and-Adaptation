# middleware/rate_limiter.py
# ─────────────────────────────────────────────
# Rate Limiting Middleware — RULES.md Security Rule #8
#
# Implements per-user rate limiting to prevent API abuse.
# Uses sliding window algorithm with in-memory storage.
#
# Configuration (via .env):
# - RATE_LIMIT_ENABLED: Master toggle (true/false)
# - RATE_LIMIT_HOURLY: Max requests per hour (default: 10)
# - RATE_LIMIT_DAILY: Max requests per day (default: 50)
# - RATE_LIMIT_MONTHLY: Max requests per month (default: 1500)
# - RATE_LIMIT_EXEMPT_USERS: Comma-separated VIP user IDs
#
# RULES.md Compliance:
# - Rate limiting per user_id
# - Returns 429 when limit exceeded
# - Works with JWT authentication
# - Master toggle for dev/demo flexibility
# ─────────────────────────────────────────────

import time
import logging
import os
import json
from collections import defaultdict
from typing import Dict, List, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, JWTError

logger = logging.getLogger(__name__)


# ═══ MASTER TOGGLE — Single boolean to enable/disable ALL rate limiting ═══
# Set via environment variable for easy deployment control
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

# Per-user override (comma-separated user IDs)
RATE_LIMIT_EXEMPT_USERS = [
    uid.strip() for uid in os.getenv("RATE_LIMIT_EXEMPT_USERS", "").split(",") if uid.strip()
]

# Rate limit configuration from environment
RATE_LIMIT_HOURLY = int(os.getenv("RATE_LIMIT_HOURLY", "10"))
RATE_LIMIT_DAILY = int(os.getenv("RATE_LIMIT_DAILY", "50"))
RATE_LIMIT_MONTHLY = int(os.getenv("RATE_LIMIT_MONTHLY", "1500"))

logger.info(
    f"[rate_limiter] config: enabled={RATE_LIMIT_ENABLED}, "
    f"hourly={RATE_LIMIT_HOURLY}, daily={RATE_LIMIT_DAILY}, monthly={RATE_LIMIT_MONTHLY}"
)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.

    Thread-safe for single-instance deployments.
    For multi-instance, use Redis-based rate limiting.

    Tracks:
    - Hourly requests (sliding window)
    - Daily requests (calendar day, UTC)
    - Monthly requests (calendar month, UTC)
    """

    def __init__(
        self,
        hourly_limit: int = 10,
        daily_limit: int = 50,
        monthly_limit: int = 1500,
        window_seconds: int = 3600
    ):
        """
        Initialize rate limiter.

        Args:
            hourly_limit: Max requests per hour (default: 10)
            daily_limit: Max requests per day (default: 50)
            monthly_limit: Max requests per month (default: 1500)
            window_seconds: Sliding window size in seconds (default: 3600 = 1 hour)
        """
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.window_seconds = window_seconds
        
        # Hourly tracking (sliding window)
        self._hourly_requests: Dict[str, List[float]] = defaultdict(list)
        
        # Daily tracking (calendar day, UTC)
        self._daily_requests: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Monthly tracking (calendar month, UTC)
        self._monthly_requests: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        logger.info(
            f"[rate_limiter] initialized: hourly={hourly_limit}, "
            f"daily={daily_limit}, monthly={monthly_limit}"
        )

    def is_allowed(self, user_id: str) -> bool:
        """
        Check if request is allowed for this user.
        Checks hourly, daily, and monthly limits.

        Args:
            user_id: User identifier from JWT

        Returns:
            True if request allowed, False if any limit exceeded
        """
        now = time.time()
        now_utc = datetime.now(timezone.utc)
        today_key = now_utc.date().isoformat()
        month_key = f"{now_utc.year}-{now_utc.month:02d}"
        
        # Clean old hourly requests outside current window
        window_start = now - self.window_seconds
        self._hourly_requests[user_id] = [
            timestamp
            for timestamp in self._hourly_requests[user_id]
            if timestamp > window_start
        ]
        
        # Check hourly limit
        if len(self._hourly_requests[user_id]) >= self.hourly_limit:
            logger.warning(
                f"[rate_limiter] hourly limit exceeded for user {user_id[:8]}... "
                f"({len(self._hourly_requests[user_id])}/{self.hourly_limit})"
            )
            return False
        
        # Check daily limit
        daily_count = self._daily_requests[user_id].get(today_key, 0)
        if daily_count >= self.daily_limit:
            logger.warning(
                f"[rate_limiter] daily limit exceeded for user {user_id[:8]}... "
                f"({daily_count}/{self.daily_limit})"
            )
            return False
        
        # Check monthly limit
        monthly_count = self._monthly_requests[user_id].get(month_key, 0)
        if monthly_count >= self.monthly_limit:
            logger.warning(
                f"[rate_limiter] monthly limit exceeded for user {user_id[:8]}... "
                f"({monthly_count}/{self.monthly_limit})"
            )
            return False
        
        # All limits passed — record this request
        self._hourly_requests[user_id].append(now)
        self._daily_requests[user_id][today_key] += 1
        self._monthly_requests[user_id][month_key] += 1
        
        return True

    def get_remaining(self, user_id: str) -> Tuple[int, int, int]:
        """
        Get remaining requests for user in current windows.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (hourly_remaining, daily_remaining, monthly_remaining)
        """
        now = time.time()
        now_utc = datetime.now(timezone.utc)
        today_key = now_utc.date().isoformat()
        month_key = f"{now_utc.year}-{now_utc.month:02d}"
        
        # Clean old hourly requests
        window_start = now - self.window_seconds
        self._hourly_requests[user_id] = [
            timestamp
            for timestamp in self._hourly_requests[user_id]
            if timestamp > window_start
        ]
        
        hourly_remaining = max(0, self.hourly_limit - len(self._hourly_requests[user_id]))
        daily_remaining = max(0, self.daily_limit - self._daily_requests[user_id].get(today_key, 0))
        monthly_remaining = max(0, self.monthly_limit - self._monthly_requests[user_id].get(month_key, 0))
        
        return hourly_remaining, daily_remaining, monthly_remaining

    def check_limits(self, user_id: str) -> Tuple[bool, str]:
        """
        Check which limit (if any) is exceeded.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (is_allowed, reason)
        """
        now = time.time()
        now_utc = datetime.now(timezone.utc)
        today_key = now_utc.date().isoformat()
        month_key = f"{now_utc.year}-{now_utc.month:02d}"
        window_start = now - self.window_seconds
        
        # Clean and check hourly
        self._hourly_requests[user_id] = [
            timestamp
            for timestamp in self._hourly_requests[user_id]
            if timestamp > window_start
        ]
        hourly_count = len(self._hourly_requests[user_id])
        
        if hourly_count >= self.hourly_limit:
            return False, f"Hourly limit exceeded ({hourly_count}/{self.hourly_limit})"
        
        # Check daily
        daily_count = self._daily_requests[user_id].get(today_key, 0)
        if daily_count >= self.daily_limit:
            return False, f"Daily limit exceeded ({daily_count}/{self.daily_limit})"
        
        # Check monthly
        monthly_count = self._monthly_requests[user_id].get(month_key, 0)
        if monthly_count >= self.monthly_limit:
            return False, f"Monthly limit exceeded ({monthly_count}/{self.monthly_limit})"
        
        return True, "OK"


# Global rate limiter instance
# RULES.md: Configurable limits via environment variables
rate_limiter = RateLimiter(
    hourly_limit=RATE_LIMIT_HOURLY,
    daily_limit=RATE_LIMIT_DAILY,
    monthly_limit=RATE_LIMIT_MONTHLY,
    window_seconds=3600
)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Extracts user_id from JWT token in Authorization header.
    Returns 429 Too Many Requests when limit exceeded.

    Features:
    - Master toggle (RATE_LIMIT_ENABLED)
    - VIP user bypass (RATE_LIMIT_EXEMPT_USERS)
    - Hourly, daily, and monthly limits
    - Dev mode auto-disable (ENVIRONMENT=development)
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Checks (in order):
        1. Master toggle (RATE_LIMIT_ENABLED)
        2. Dev mode (ENVIRONMENT=development)
        3. VIP user bypass (RATE_LIMIT_EXEMPT_USERS)
        4. Health check skip (/health)
        5. CORS preflight skip (OPTIONS)
        6. Hourly, daily, monthly limits

        RULES.md:
        - Skip rate limiting for health checks
        - Skip rate limiting for CORS preflight (OPTIONS)
        - Rate limit per user_id or per-IP for anonymous (configurable)

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response or 429 error
        """
        # ═══ MASTER TOGGLE CHECK ═══
        if not RATE_LIMIT_ENABLED:
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
            logger.debug(f"[rate_limiter] Using user_id from request.state: {user_id[:8]}...")

        # ═══ VIP USER BYPASS CHECK ═══
        if user_id and user_id in RATE_LIMIT_EXEMPT_USERS:
            logger.debug(f"[rate_limiter] VIP user bypass: {user_id[:8]}...")
            return await call_next(request)

        # Fallback: If no user_id from state, use client IP
        if not user_id:
            # Get client IP (handle X-Forwarded-For for proxied requests)
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                # Take the first IP in the chain (client IP)
                client_ip = forwarded_for.split(',')[0].strip()
            else:
                client_ip = request.client.host if request.client else 'unknown'

            user_id = f"anon:{client_ip}"
            logger.debug(f"[rate_limiter] Using IP-based identifier: {user_id[:8]}...")

        # ═══ CHECK RATE LIMITS ═══
        is_allowed, reason = rate_limiter.check_limits(user_id)
        
        if not is_allowed:
            hourly_rem, daily_rem, monthly_rem = rate_limiter.get_remaining(user_id)
            logger.warning(
                f"[rate_limiter] blocked request for user {user_id[:8]}... "
                f"reason={reason}"
            )
            # Return JSONResponse directly (avoids 500 error from HTTPException)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": reason,
                    "limits": {
                        "hourly": RATE_LIMIT_HOURLY,
                        "daily": RATE_LIMIT_DAILY,
                        "monthly": RATE_LIMIT_MONTHLY
                    },
                    "remaining": {
                        "hourly": hourly_rem,
                        "daily": daily_rem,
                        "monthly": monthly_rem
                    }
                },
                headers={
                    'X-RateLimit-Limit-Hourly': str(RATE_LIMIT_HOURLY),
                    'X-RateLimit-Limit-Daily': str(RATE_LIMIT_DAILY),
                    'X-RateLimit-Limit-Monthly': str(RATE_LIMIT_MONTHLY),
                    'Retry-After': '3600'
                }
            )

        # ═══ ADD RATE LIMIT HEADERS TO RESPONSE ═══
        response = await call_next(request)
        hourly_rem, daily_rem, monthly_rem = rate_limiter.get_remaining(user_id)
        response.headers['X-RateLimit-Limit-Hourly'] = str(RATE_LIMIT_HOURLY)
        response.headers['X-RateLimit-Remaining-Hourly'] = str(hourly_rem)
        response.headers['X-RateLimit-Limit-Daily'] = str(RATE_LIMIT_DAILY)
        response.headers['X-RateLimit-Remaining-Daily'] = str(daily_rem)
        response.headers['X-RateLimit-Limit-Monthly'] = str(RATE_LIMIT_MONTHLY)
        response.headers['X-RateLimit-Remaining-Monthly'] = str(monthly_rem)

        return response

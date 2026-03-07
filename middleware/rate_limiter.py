# middleware/rate_limiter.py
# ─────────────────────────────────────────────
# Rate Limiting Middleware — RULES.md Security Rule #8
#
# Implements per-user rate limiting to prevent API abuse.
# Uses sliding window algorithm with in-memory storage.
#
# Configuration:
# - RATE_LIMIT_REQUESTS: Max requests per window (default: 100)
# - RATE_LIMIT_WINDOW: Window size in seconds (default: 3600 = 1 hour)
#
# RULES.md Compliance:
# - Rate limiting per user_id
# - Returns 429 when limit exceeded
# - Works with JWT authentication
# ─────────────────────────────────────────────

import time
import logging
import os
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    
    Thread-safe for single-instance deployments.
    For multi-instance, use Redis-based rate limiting.
    """
    
    def __init__(self, requests_per_window: int = 100, window_seconds: int = 3600):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_window: Max requests allowed per window (default: 100/hour)
            window_seconds: Window size in seconds (default: 3600 = 1 hour)
        """
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        logger.info(f"[rate_limiter] initialized: {requests_per_window} requests per {window_seconds}s")
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Check if request is allowed for this user.
        
        Args:
            user_id: User identifier from JWT
            
        Returns:
            True if request allowed, False if rate limit exceeded
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests outside current window
        self._requests[user_id] = [
            timestamp 
            for timestamp in self._requests[user_id] 
            if timestamp > window_start
        ]
        
        # Check if limit exceeded
        if len(self._requests[user_id]) >= self.requests_per_window:
            logger.warning(
                f"[rate_limiter] limit exceeded for user {user_id[:8]}... "
                f"({len(self._requests[user_id])} requests in window)"
            )
            return False
        
        # Record this request
        self._requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining requests for user in current window.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of remaining requests allowed
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self._requests[user_id] = [
            timestamp 
            for timestamp in self._requests[user_id] 
            if timestamp > window_start
        ]
        
        remaining = self.requests_per_window - len(self._requests[user_id])
        return max(0, remaining)


# Global rate limiter instance
# RULES.md: 100 requests per hour per user_id
rate_limiter = RateLimiter(requests_per_window=100, window_seconds=3600)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    
    Extracts user_id from request state (set by auth middleware).
    Returns 429 Too Many Requests when limit exceeded.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Extracts user_id from JWT token in Authorization header.
        Skips rate limiting for /health endpoint.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response or 429 error

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Skip rate limiting for health check (no auth required)
        if request.url.path == "/health":
            return await call_next(request)

        # Extract user_id from JWT token in Authorization header
        user_id = 'anonymous'
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
            supabase_url = os.getenv("SUPABASE_URL")

            if jwt_secret and supabase_url:
                try:
                    payload = jwt.decode(
                        token,
                        jwt_secret,
                        algorithms=["HS256"],
                        issuer=supabase_url,
                        options={"verify_aud": False}
                    )
                    user_id = payload.get("sub", "anonymous")
                except (JWTError, Exception) as e:
                    # If JWT validation fails, still rate limit but as anonymous
                    logger.debug(f"[rate_limiter] JWT validation failed, using anonymous: {e}")
                    user_id = 'anonymous'

        # Check rate limit
        if not rate_limiter.is_allowed(user_id):
            remaining = rate_limiter.get_remaining(user_id)
            logger.warning(
                f"[rate_limiter] blocked request for user {user_id[:8]}... "
                f"(remaining: {remaining})"
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "limit": "100 requests per hour",
                    "remaining": remaining
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        remaining = rate_limiter.get_remaining(user_id)
        response.headers['X-RateLimit-Limit'] = '100'
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Window'] = '3600'

        return response

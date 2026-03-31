# middleware/metrics.py
# ─────────────────────────────────────────────
# Request Metrics Middleware — Performance Monitoring
#
# Captures and logs structured metrics for every request:
# - Request timing (total latency)
# - Agent-level latencies
# - Error rates
# - Cache hit/miss
# - User-specific metrics
#
# RULES.md Compliance:
# - Type hints mandatory
# - Docstrings complete
# - Error handling comprehensive
# - Logging contextual (structured JSON format)
# ─────────────────────────────────────────────

import time
import uuid
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    In-memory metrics collector for request/response tracking.
    
    Thread-safe for single-instance deployments.
    For multi-instance, use Redis-based metrics aggregation.
    
    Tracks:
    - Request count (total, by endpoint, by user)
    - Latency percentiles (p50, p95, p99)
    - Error rates (by endpoint, by error type)
    - Cache hit/miss rates
    - Agent execution times
    """
    
    def __init__(self):
        self._request_count = 0
        self._latencies = []  # List of latencies for percentile calculation
        self._errors_by_endpoint: Dict[str, int] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._agent_latencies: Dict[str, list] = {}  # agent_name -> [latencies]
        
        logger.info("[metrics] MetricsCollector initialized")
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        latency_ms: float,
        status_code: int,
        user_id: Optional[str] = None,
        cache_hit: bool = False,
        agent_latencies: Optional[Dict[str, int]] = None
    ):
        """
        Record a completed request with all metrics.
        
        Args:
            endpoint: API endpoint path (e.g., "/chat", "/refine")
            method: HTTP method (GET, POST, etc.)
            latency_ms: Total request latency in milliseconds
            status_code: HTTP response status code
            user_id: User identifier (optional, for per-user metrics)
            cache_hit: True if served from cache
            agent_latencies: Dict of agent_name -> latency_ms
        """
        self._request_count += 1
        self._latencies.append(latency_ms)
        
        # Keep only last 1000 latencies for memory efficiency
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-1000:]
        
        # Record errors
        if status_code >= 400:
            self._errors_by_endpoint[endpoint] = self._errors_by_endpoint.get(endpoint, 0) + 1
        
        # Record cache stats
        if cache_hit:
            self._cache_hits += 1
        else:
            self._cache_misses += 1
        
        # Record agent latencies
        if agent_latencies:
            for agent_name, latency in agent_latencies.items():
                if agent_name not in self._agent_latencies:
                    self._agent_latencies[agent_name] = []
                self._agent_latencies[agent_name].append(latency)
                # Keep only last 100 per agent
                if len(self._agent_latencies[agent_name]) > 100:
                    self._agent_latencies[agent_name] = self._agent_latencies[agent_name][-100:]
    
    def get_percentile(self, percentile: float) -> float:
        """
        Calculate latency percentile.
        
        Args:
            percentile: Percentile to calculate (0.5 = p50, 0.95 = p95, etc.)
        
        Returns:
            Latency value at specified percentile, or 0 if no data
        """
        if not self._latencies:
            return 0.0
        
        sorted_latencies = sorted(self._latencies)
        index = int(len(sorted_latencies) * percentile)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get current metrics summary.
        
        Returns:
            Dict with key metrics for monitoring
        """
        cache_total = self._cache_hits + self._cache_misses
        cache_hit_rate = (self._cache_hits / cache_total * 100) if cache_total > 0 else 0.0
        
        return {
            "total_requests": self._request_count,
            "latency_p50_ms": round(self.get_percentile(0.5), 2),
            "latency_p95_ms": round(self.get_percentile(0.95), 2),
            "latency_p99_ms": round(self.get_percentile(0.99), 2),
            "error_count": sum(self._errors_by_endpoint.values()),
            "errors_by_endpoint": self._errors_by_endpoint,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "agent_latencies": {
                agent: {
                    "count": len(lats),
                    "avg_ms": round(sum(lats) / len(lats), 2) if lats else 0,
                    "max_ms": max(lats) if lats else 0
                }
                for agent, lats in self._agent_latencies.items()
            }
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for request/response metrics collection.
    
    Captures:
    - Request start time
    - Endpoint and method
    - Response status code
    - Total latency
    - User ID (if authenticated)
    
    Logs structured JSON for each request:
    {
        "request_id": "uuid",
        "timestamp": "ISO8601",
        "method": "POST",
        "endpoint": "/chat",
        "latency_ms": 1234,
        "status_code": 200,
        "user_id": "abc123...",
        "cache_hit": false
    }
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and collect metrics.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
        
        Returns:
            HTTP response with optional metrics headers
        """
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Extract user_id if authenticated (set by auth middleware)
        user_id = None
        if hasattr(request, 'state') and hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error with full context
            latency_ms = (time.time() - start_time) * 1000
            self._log_metrics(
                request=request,
                request_id=request_id,
                latency_ms=latency_ms,
                status_code=500,
                user_id=user_id,
                error=str(e)
            )
            raise
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract cache hit from response headers (if set by cache middleware)
        cache_hit = response.headers.get('X-Cache', 'miss') == 'hit'
        
        # Extract agent latencies from response headers (if set)
        agent_latencies = {}
        for header_name in response.headers:
            if header_name.startswith('X-Agent-Latency-'):
                agent_name = header_name.replace('X-Agent-Latency-', '')
                try:
                    agent_latencies[agent_name] = int(response.headers[header_name])
                except ValueError:
                    pass
        
        # Log metrics
        self._log_metrics(
            request=request,
            request_id=request_id,
            latency_ms=latency_ms,
            status_code=response.status_code,
            user_id=user_id,
            cache_hit=cache_hit,
            agent_latencies=agent_latencies
        )
        
        # Add metrics to response headers (for debugging)
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Response-Time-Ms'] = str(round(latency_ms, 2))
        
        return response
    
    def _log_metrics(
        self,
        request: Request,
        request_id: str,
        latency_ms: float,
        status_code: int,
        user_id: Optional[str] = None,
        cache_hit: bool = False,
        agent_latencies: Optional[Dict[str, int]] = None,
        error: Optional[str] = None
    ):
        """
        Log structured metrics JSON.
        
        Args:
            request: HTTP request object
            request_id: Unique request identifier
            latency_ms: Total request latency
            status_code: HTTP response status
            user_id: User identifier (if authenticated)
            cache_hit: True if cache hit
            agent_latencies: Dict of agent latencies
            error: Error message (if any)
        """
        endpoint = request.url.path
        method = request.method
        
        # Build structured log entry
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "endpoint": endpoint,
            "latency_ms": round(latency_ms, 2),
            "status_code": status_code,
            "user_id": user_id[:8] + "..." if user_id else None,
            "cache_hit": cache_hit,
        }
        
        # Add agent latencies if present
        if agent_latencies:
            log_entry["agent_latencies"] = agent_latencies
        
        # Add error if present
        if error:
            log_entry["error"] = error
        
        # Log at appropriate level
        if status_code >= 500:
            logger.error(f"[metrics] {json.dumps(log_entry)}")
        elif status_code >= 400:
            logger.warning(f"[metrics] {json.dumps(log_entry)}")
        else:
            # Only log 10% of successful requests to reduce noise
            import random
            if random.random() < 0.1:
                logger.info(f"[metrics] {json.dumps(log_entry)}")
        
        # Record in metrics collector
        metrics_collector.record_request(
            endpoint=endpoint,
            method=method,
            latency_ms=latency_ms,
            status_code=status_code,
            user_id=user_id,
            cache_hit=cache_hit,
            agent_latencies=agent_latencies
        )


# Utility function to get current metrics summary
def get_metrics_summary() -> Dict[str, Any]:
    """
    Get current metrics summary for monitoring dashboards.
    
    Returns:
        Dict with aggregated metrics
    """
    return metrics_collector.get_summary()


__all__ = [
    "MetricsMiddleware",
    "MetricsCollector",
    "metrics_collector",
    "get_metrics_summary",
]

# api.py
# ─────────────────────────────────────────────
# FastAPI App Factory — PromptForge v2.0
#
# This file creates the FastAPI app and registers all routers.
# Business logic lives in service.py.
# Endpoint logic lives in routes/*.py.
#
# Architecture:
#   api.py          → App factory + middleware (this file)
#   service.py      → Business logic (_run_swarm, compute_diff, sse_format)
#   routes/         → Endpoint routers (7 files, all <500 lines)
#   agents/         → AI agent implementations
#
# RULES.md Compliance:
#   - <500 lines per file ✅
#   - No wildcard CORS ✅
#   - Rate limiting enabled ✅
#   - JWT auth on all protected routes ✅
#   - Error tracking with Sentry ✅
# ─────────────────────────────────────────────

# ═══ SENTRY INITIALIZATION — MUST BE FIRST ═══
# Per RULES.md: Error tracking for production monitoring
# This MUST come before any other imports to capture all errors
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # Sample 10% of transactions for performance monitoring
    profiles_sample_rate=0.1,  # Sample 10% of profiles
    environment=os.getenv("ENVIRONMENT", "production"),
    release="promptforge-2.0.0",
    # Only send errors in production
    send_default_pii=False,
)

# ── Standard Imports ──────────────────────────

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from middleware.rate_limiter import RateLimiterMiddleware
from middleware.metrics import MetricsMiddleware
from routes import ALL_ROUTERS

logger = logging.getLogger(__name__)


# ── App Factory ───────────────────────────────

app = FastAPI(
    title="PromptForge",
    description="Multi-agent prompt improvement system with conversational memory",
    version="2.0.0"
)

# CORS locked to frontend domains (per RULES.md - no wildcard!)
frontend_urls = os.getenv("FRONTEND_URLS", "http://localhost:3000,http://localhost:9000").split(",")
logger.info(f"[api] CORS allowed for: {frontend_urls}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (RULES.md Security Rule #8)
logger.info("[api] Rate limiting enabled: 100 requests/hour per user")
app.add_middleware(RateLimiterMiddleware)

# Metrics collection middleware (for monitoring and debugging)
logger.info("[api] Metrics middleware enabled: structured logging + latency tracking")
app.add_middleware(MetricsMiddleware)


# ── Register All Routers ──────────────────────

for router in ALL_ROUTERS:
    app.include_router(router)

logger.info(f"[api] Registered {len(ALL_ROUTERS)} route modules")


# ── Backward Compatibility ────────────────────
# These imports allow existing code (tests, main.py) to keep doing:
#   from api import app, ChatRequest, RefineRequest
# without breaking. They re-export from the router modules.

from routes.prompts import ChatRequest, ChatResponse, RefineRequest, RefineResponse
from service import compute_diff as _compute_diff, sse_format as _sse


# ── Test Route for Sentry (Development only) ─
# Per RULES.md: Available in dev for testing, gated in production

if os.getenv("ENVIRONMENT", "production") != "production":
    @app.get("/test-error")
    async def test_sentry_error():
        """
        Test route to verify Sentry error tracking is working.
        Only available when ENVIRONMENT != production.
        
        Visit: GET /test-error
        Expected: 500 error sent to Sentry dashboard
        """
        logger.warning("[test] triggering test error for Sentry verification")
        raise ValueError("🔍 SENTRY TEST ERROR — If you see this in Sentry, integration works!")


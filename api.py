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
# ─────────────────────────────────────────────

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from middleware.rate_limiter import RateLimiterMiddleware
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

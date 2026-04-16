# routes/__init__.py
# ─────────────────────────────────────────────
# FastAPI Router Registry
# Import all routers here for clean api.py factory.
# ─────────────────────────────────────────────

from routes.health import router as health_router
from routes.prompts import router as prompts_router
from routes.prompts_stream import router as prompts_stream_router
from routes.sessions import router as sessions_router
from routes.history import router as history_router
from routes.user import router as user_router
from routes.mcp import router as mcp_router
from routes.feedback import router as feedback_router
from routes.usage import router as usage_router
from routes.analytics import router as analytics_router
from routes.newsletter import router as newsletter_router
from routes.tts import router as tts_router

ALL_ROUTERS = [
    health_router,
    prompts_router,
    prompts_stream_router,
    sessions_router,
    history_router,
    user_router,
    mcp_router,
    feedback_router,
    usage_router,
    analytics_router,
    newsletter_router,
    tts_router,
]

__all__ = ["ALL_ROUTERS"]

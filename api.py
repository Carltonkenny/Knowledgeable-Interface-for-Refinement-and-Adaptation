from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import ALL_ROUTERS
import os
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PromptForge API",
    description="Multi-agent prompt engineering API with memory and multimodal capabilities",
    version="2.0.0"
)

# ═══ CORS — reads from FRONTEND_URLS env var ═══
# Railway: set FRONTEND_URLS=https://your-app.vercel.app,http://localhost:3000
_raw_origins = os.getenv("FRONTEND_URLS", "http://localhost:3000")
ALLOWED_ORIGINS = [url.strip() for url in _raw_origins.split(",") if url.strip()]

# In development (no FRONTEND_URLS set), allow all origins
if not os.getenv("FRONTEND_URLS"):
    logger.warning("[api] FRONTEND_URLS not set! Defaulting to allow all origins ('*'). If this is production, please set FRONTEND_URLS.")
    ALLOWED_ORIGINS = ["*"]

logger.info(f"[api] CORS allowed origins configured: {ALLOWED_ORIGINS}")

# Validate critical auth variables on startup (Fail Fast)
if not os.getenv("SUPABASE_URL") or not (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")):
    logger.critical("[api] CRITICAL: SUPABASE_URL or SUPABASE_ANON_KEY is missing. Authentication will fail.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══ Register all routers from routes/__init__.py ═══
for router in ALL_ROUTERS:
    app.include_router(router)

logger.info(f"[api] {len(ALL_ROUTERS)} routers registered")


@app.get("/")
async def root():
    return {"message": "PromptForge API v2.0", "status": "running"}

@app.get("/health")
async def health_check():
    """Detailed health check for automated CI/CD and deployment ping."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "cors_origins": ALLOWED_ORIGINS,
    }
# routes/health.py
# ─────────────────────────────────────────────
# Health check endpoint — no auth required.
# RULES.md: <500 lines per file
# ─────────────────────────────────────────────

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    """Liveness check — no auth required."""
    return {"status": "ok", "version": "2.0.0"}

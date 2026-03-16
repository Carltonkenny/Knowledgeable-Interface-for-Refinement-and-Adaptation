# routes/feedback.py
# ─────────────────────────────────────────────
# Implicit Feedback Endpoint
#   POST /feedback → Collect usage signals (copy, edit, save)
#
# RULES.md: <500 lines, type hints, docstrings
# ─────────────────────────────────────────────

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from auth import User, get_current_user
from database import get_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Feedback"])


# ── Schemas ───────────────────────────────────

class FeedbackRequest(BaseModel):
    """Implicit feedback submission schema."""
    session_id: str
    prompt_id: str
    feedback_type: str  # copy|edit|save
    edit_distance: Optional[float] = None
    timestamp: str


# ── Helpers ───────────────────────────────────

def _calculate_feedback_weight(req: FeedbackRequest) -> float:
    """
    Map feedback type to quality score adjustment.
    
    Args:
        req: Feedback request
    Returns:
        Weight adjustment (-0.1 to +0.1)
    """
    weights = {
        "copy": +0.08,
        "save": +0.10,
        "edit": -0.03 if (req.edit_distance or 0) > 0.4 else +0.02,
    }
    return weights.get(req.feedback_type, 0.0)


async def _adjust_user_quality_score(user_id: str, delta: float) -> bool:
    """Adjust user's prompt_quality_score in background."""
    try:
        from database import get_user_profile, save_user_profile
        
        profile = get_user_profile(user_id)
        if not profile:
            return False
        
        current_score = profile.get("prompt_quality_score", 0.5)
        new_score = max(0.0, min(1.0, current_score + delta))
        
        profile["prompt_quality_score"] = new_score
        success = save_user_profile(user_id, profile)
        
        if success:
            logger.debug(f"[profile] adjusted quality score: {user_id[:8]}... delta={delta:.3f}")
        
        return success
        
    except Exception as e:
        logger.error(f"[profile] quality score adjustment failed: {e}")
        return False


# ── Endpoint ──────────────────────────────────

@router.post("/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    user: User = Depends(get_current_user)
):
    """Collect implicit feedback from user behavior."""
    try:
        db = get_client()
        
        db.table("prompt_feedback").insert({
            "user_id": user.user_id,
            "session_id": req.session_id,
            "prompt_id": req.prompt_id,
            "feedback_type": req.feedback_type,
            "edit_distance": req.edit_distance,
            "timestamp": req.timestamp,
        }).execute()
        
        weight = _calculate_feedback_weight(req)
        
        # Background quality adjustment
        await _adjust_user_quality_score(user.user_id, weight)
        
        logger.info(f"[feedback] recorded: type={req.feedback_type}, weight={weight:.3f}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"[feedback] failed: {e}")
        return {"status": "error", "message": "Failed to record feedback"}

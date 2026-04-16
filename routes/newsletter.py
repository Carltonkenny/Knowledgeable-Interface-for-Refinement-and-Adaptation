# routes/newsletter.py
# ─────────────────────────────────────────────
# Newsletter Subscription Route
# ─────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel, EmailStr
import logging
from database import get_client

router = APIRouter(prefix="/newsletter", tags=["newsletter"])
logger = logging.getLogger(__name__)

class SubscribeRequest(BaseModel):
    email: EmailStr
    source: str = "footer"

@router.post("/subscribe")
async def subscribe_newsletter(req: SubscribeRequest):
    """
    Subscribes a user to the PromptForge newsletter.
    Stores email in Supabase 'newsletter_subscribers' table.
    """
    try:
        db = get_client()

        # Insert email into the database
        result = db.table("newsletter_subscribers").upsert(
            {
                "email": req.email,
                "source": req.source,
                "is_active": True
            },
            on_conflict="email"
        ).execute()

        logger.info(f"[newsletter] new subscription: {req.email} (source={req.source})")
        
        return {"status": "success", "message": "Successfully subscribed to the newsletter!"}

    except Exception as e:
        # Check if it's a unique constraint violation or something similar
        if "duplicate key value" in str(e).lower() or "unique constraint" in str(e).lower():
            # Already subscribed, treat as success implicitly to prevent email enumeration
            logger.info(f"[newsletter] duplicate subscription attempt: {req.email}")
            return {"status": "success", "message": "Successfully subscribed to the newsletter!"}

        logger.error(f"[newsletter] Failed to subscribe {req.email}: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe. Please try again later.")

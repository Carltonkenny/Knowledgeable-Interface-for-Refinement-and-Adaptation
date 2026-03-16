# routes/user.py
# ─────────────────────────────────────────────
# User Profile & Digital Twin Endpoints
#   POST   /user/profile        → Update profile
#   GET    /user/domains        → Domain niches
#   GET    /user/memories       → LangMem memory previews
#   GET    /user/quality-trend  → Quality sparkline
#   GET    /user/stats          → Usage statistics
#   DELETE /user/account        → GDPR account deletion
#   GET    /user/export-data    → GDPR data export
#
# RULES.md: <500 lines, type hints, docstrings
# ─────────────────────────────────────────────

import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from auth import User, get_current_user
from database import get_client
from utils import calculate_overall_quality

logger = logging.getLogger(__name__)

router = APIRouter(tags=["User"])


# ── Schemas ───────────────────────────────────

class UsernameUpdateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""
    primary_use: Optional[str] = None
    audience: Optional[str] = None
    ai_frustration: Optional[str] = None
    frustration_detail: Optional[str] = None
    preferred_tone: Optional[str] = None
    clarification_rate: Optional[float] = None
    prompt_quality_score: Optional[float] = None


# ── Endpoints ─────────────────────────────────

@router.post("/user/profile")
async def update_user_profile_endpoint(
    req: UserProfileUpdateRequest,
    user: User = Depends(get_current_user)
):
    """Update the user's profile settings."""
    logger.info(f"[api] /user/profile update requested by user={user.user_id}")
    try:
        db = get_client()
        
        update_data = {}
        if req.primary_use is not None:
            update_data["primary_use"] = req.primary_use
        if req.audience is not None:
            update_data["audience"] = req.audience
        if req.ai_frustration is not None:
            update_data["ai_frustration"] = req.ai_frustration
        if req.frustration_detail is not None:
            update_data["frustration_detail"] = req.frustration_detail
        if req.preferred_tone is not None:
            update_data["preferred_tone"] = req.preferred_tone
        if req.clarification_rate is not None:
            update_data["clarification_rate"] = req.clarification_rate
        if req.prompt_quality_score is not None:
            update_data["prompt_quality_score"] = req.prompt_quality_score
        
        result = db.table("user_profiles").update(update_data).eq("user_id", user.user_id).execute()
        
        if not result.data:
            insert_data = {"user_id": user.user_id, **update_data}
            result = db.table("user_profiles").insert(insert_data).execute()
        
        logger.info(f"[api] profile updated for user={user.user_id}")
        return {"status": "success", "profile": result.data[0] if result.data else update_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[api] Profile update failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/domains")
async def get_user_domains(user: User = Depends(get_current_user)):
    """Fetch the user's domain niches from LangMem."""
    logger.info(f"[api] /user/domains requested by user={user.user_id}")
    try:
        db = get_client()
        result = db.table("requests").select("domain_analysis").eq("user_id", user.user_id).not_.is_("domain_analysis", "null").execute()
        
        domain_counts = {}
        confidence_sums = {}
        
        for req in result.data:
            domain_info = req.get("domain_analysis", {})
            if isinstance(domain_info, dict):
                domain_name = domain_info.get("primary_domain")
                confidence = domain_info.get("confidence_score", 0.0)
                
                if domain_name and domain_name != "unknown":
                    domain_counts[domain_name] = domain_counts.get(domain_name, 0) + 1
                    confidence_sums[domain_name] = confidence_sums.get(domain_name, 0.0) + confidence
                    
        domains = []
        for name, count in domain_counts.items():
            domains.append({
                "domain": name.title(),
                "confidence": round(confidence_sums[name] / count, 2),
                "interaction_count": count,
                "last_active": datetime.now(timezone.utc).isoformat()
            })
            
        domains.sort(key=lambda x: x["confidence"], reverse=True)
        return {"domains": domains[:10]}
        
    except Exception as e:
        logger.exception(f"[api] Get domains failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/memories")
async def get_user_memories(user: User = Depends(get_current_user)):
    """Fetch LangMem memory previews associated with the user profile."""
    logger.info(f"[api] /user/memories requested by user={user.user_id}")
    try:
        db = get_client()
        result = db.table("langmem_memories").select("id, content, domain, created_at").eq("user_id", user.user_id).order("created_at", desc=True).limit(15).execute()
        
        memories = []
        for row in result.data:
            memories.append({
                "id": str(row.get("id")),
                "content": row.get("content", ""),
                "category": row.get("domain", "General").title(),
                "created_at": row.get("created_at")
            })
            
        return {"memories": memories}
        
    except Exception as e:
        logger.exception(f"[api] Get memories failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/quality-trend")
async def get_user_quality_trend(user: User = Depends(get_current_user)):
    """Generate the quality trend sparkline data for the user profile."""
    logger.info(f"[api] /user/quality-trend requested by user={user.user_id}")
    try:
        db = get_client()
        result = db.table("requests").select("created_at, quality_score, agents_used").eq("user_id", user.user_id).order("created_at", desc=False).limit(30).execute()
        
        trend_data = []
        for i, row in enumerate(result.data):
            score = row.get("quality_score") or {}
            overall = calculate_overall_quality(score)
            trend_data.append({"index": i, "score": overall, "date": row.get("created_at")})
            
        return {"trend": trend_data}
        
    except Exception as e:
        logger.exception(f"[api] Get quality trend failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/stats")
async def get_user_stats(user: User = Depends(get_current_user)):
    """Calculate usage statistics for the user profile."""
    logger.info(f"[api] /user/stats requested by user={user.user_id}")
    try:
        db = get_client()
        
        req_result = db.table("requests").select("id", count="exact").eq("user_id", user.user_id).execute()
        total_prompts = req_result.count if hasattr(req_result, 'count') else len(req_result.data)
        
        sess_result = db.table("chat_sessions").select("id", count="exact").eq("user_id", user.user_id).execute()
        total_sessions = sess_result.count if hasattr(sess_result, 'count') else len(sess_result.data)
        
        quality_res = db.table("requests").select("quality_score").eq("user_id", user.user_id).limit(100).execute()
        scores = []
        for row in quality_res.data:
            sc = row.get("quality_score") or {}
            scores.append(calculate_overall_quality(sc))
            
        avg_quality = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "total_prompts_engineered": total_prompts,
            "active_chat_sessions": total_sessions,
            "average_quality_score": round(avg_quality, 1),
            "member_since": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.exception(f"[api] Get user stats failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/account")
async def delete_user_account(user: User = Depends(get_current_user)):
    """Delete the user's account and all associated data (GDPR)."""
    logger.info(f"[api] GDPR ACCOUNT DELETION requested by user={user.user_id}")
    try:
        db = get_client()
        
        db.table("requests").delete().eq("user_id", user.user_id).execute()
        db.table("chat_sessions").delete().eq("user_id", user.user_id).execute()
        db.table("conversations").delete().eq("user_id", user.user_id).execute()
        db.table("user_profiles").delete().eq("user_id", user.user_id).execute()
        db.table("langmem_memories").delete().eq("user_id", user.user_id).execute()
        
        return {"status": "deleted", "message": "Account data scheduled for permanent deletion."}
        
    except Exception as e:
        logger.exception(f"[api] Account deletion failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/export-data")
async def export_user_data(user: User = Depends(get_current_user)):
    """Export all user data to comply with GDPR data portability requirements."""
    logger.info(f"[api] GDPR DATA EXPORT requested by user={user.user_id}")
    try:
        db = get_client()
        
        profile = db.table("user_profiles").select("*").eq("user_id", user.user_id).execute()
        requests = db.table("requests").select("*").eq("user_id", user.user_id).execute()
        sessions = db.table("chat_sessions").select("*").eq("user_id", user.user_id).execute()
        conversations = db.table("conversations").select("*").eq("user_id", user.user_id).execute()
        
        return {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "user_id": user.user_id,
            "profile": profile.data[0] if profile.data else {},
            "requests": requests.data,
            "sessions": sessions.data,
            "conversations": conversations.data
        }
        
    except Exception as e:
        logger.exception(f"[api] Data export failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail=str(e))

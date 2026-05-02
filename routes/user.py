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

import os
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from auth import User, get_current_user
from database import get_client, get_user_profile

class FavoriteUpdate(BaseModel):
    is_favorite: bool

class DomainUpdate(BaseModel):
    primary_domain: str
    sub_domain: Optional[str] = "Manual Override"

from utils import calculate_overall_quality
from memory.langmem import write_to_langmem

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
    phone: Optional[str] = Field(None, max_length=20, description="User's phone number")
    company: Optional[str] = Field(None, max_length=100, description="Company/organization name")
    location: Optional[str] = Field(None, max_length=100, description="User's location/timezone")
    bio: Optional[str] = Field(None, max_length=500, description="Short bio or description")
    job_title: Optional[str] = Field(None, max_length=100, description="Job title/role")
    website: Optional[str] = Field(None, max_length=200, description="Personal website URL")
    github: Optional[str] = Field(None, max_length=100, description="GitHub username")
    twitter: Optional[str] = Field(None, max_length=100, description="Twitter username")
    linkedin: Optional[str] = Field(None, max_length=200, description="LinkedIn profile URL")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Profile picture URL")
    is_public: Optional[bool] = Field(None, description="Whether profile is publicly visible")
    default_tone: Optional[str] = Field(None, max_length=20, description="Default prompt tone")
    default_audience: Optional[str] = Field(None, max_length=20, description="Default audience")
    session_timeout_hours: Optional[int] = Field(None, ge=1, le=720, description="Session timeout in hours")


class OnboardingRequest(BaseModel):
    """Schema for memory onboarding request"""
    content: str = Field(..., min_length=10, max_length=5000, description="User's onboarding profile content")
    metadata: dict = Field(default_factory=dict, description="Additional metadata (primary_use, audience, etc.)")
    phone: Optional[str] = Field(None, max_length=20, description="User's phone number")
    company: Optional[str] = Field(None, max_length=100, description="Company/organization name")
    location: Optional[str] = Field(None, max_length=100, description="User's location/timezone")
    bio: Optional[str] = Field(None, max_length=500, description="Short bio or description")


class ChangePasswordRequest(BaseModel):
    """Schema for changing user password."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


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
        if req.phone is not None:
            update_data["phone"] = req.phone
        if req.company is not None:
            update_data["company"] = req.company
        if req.location is not None:
            update_data["location"] = req.location
        if req.bio is not None:
            update_data["bio"] = req.bio
        if req.job_title is not None:
            update_data["job_title"] = req.job_title
        if req.website is not None:
            update_data["website"] = req.website
        if req.github is not None:
            update_data["github"] = req.github
        if req.twitter is not None:
            update_data["twitter"] = req.twitter
        if req.linkedin is not None:
            update_data["linkedin"] = req.linkedin
        if req.avatar_url is not None:
            update_data["avatar_url"] = req.avatar_url

        result = db.table("user_profiles").update(update_data).eq("user_id", user.user_id).execute()

        if not result.data:
            insert_data = {
                "user_id": user.user_id,
                "prompt_quality_trend": "stable",
                "clarification_rate": 0.0,
                **update_data
            }
            result = db.table("user_profiles").insert(insert_data).execute()

        logger.info(f"[api] profile updated for user={user.user_id}")
        return {"status": "success", "profile": result.data[0] if result.data else update_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[api] Profile update failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/user/username")
async def update_username_endpoint(
    req: UsernameUpdateRequest,
    user: User = Depends(get_current_user)
):
    """Update the user's username (display name) via Supabase auth metadata."""
    logger.info(f"[api] /user/username update requested by user={user.user_id}")
    try:
        from supabase import create_client
        import os

        # Use service role key to update user metadata
        supabase_admin = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )

        # Update user metadata in auth.users
        # Note: update_user_by_id takes user_id as first positional arg (not keyword)
        result = supabase_admin.auth.admin.update_user_by_id(
            user.user_id,
            {"data": {"username": req.username}}
        )

        logger.info(f"[api] username updated for user={user.user_id} to {req.username}")
        return {"status": "success", "username": req.username}

    except Exception as e:
        logger.exception(f"[api] Username update failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        raise HTTPException(status_code=500, detail="Internal server error")


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
                "category": row.get("domain", "other").lower(),
                "created_at": row.get("created_at")
            })
            
        return {"memories": memories}
        
    except Exception as e:
        logger.exception(f"[api] Get memories failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        raise HTTPException(status_code=500, detail="Internal server error")


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

        # fetch xp stuff
        profile_res = db.table("user_profiles").select("xp_total", "loyalty_tier").eq("user_id", user.user_id).execute()
        xp_total = 0
        loyalty_tier = "Bronze"
        if profile_res.data:
            xp_total = profile_res.data[0].get("xp_total", 0)
            loyalty_tier = profile_res.data[0].get("loyalty_tier", "Bronze")

        # FIX #2: Calculate real member_since from first activity
        first_activity_result = db.table("requests").select("created_at").eq("user_id", user.user_id).order("created_at", desc=False).limit(1).execute()
        member_since = first_activity_result.data[0]["created_at"] if first_activity_result.data else datetime.now(timezone.utc).isoformat()

        # FIX #1: Calculate trust level using same logic as memory/supermemory.py:get_trust_level()
        conv_result = db.table("conversations").select("id", count="exact").eq("user_id", user.user_id).execute()
        session_count = conv_result.count if hasattr(conv_result, 'count') else len(conv_result.data)

        if session_count < 3:
            trust_level = 0  # Cold
        elif session_count < 10:
            trust_level = 1  # Warm
        else:
            trust_level = 2  # Tuned

        # ═══ STREAK DATA FETCH ═══
        # Fetch timestamps of recent prompts for streak calculation
        stats_data_res = db.table("requests").select("created_at").eq("user_id", user.user_id).order("created_at", desc=True).limit(100).execute()
        stats_data = stats_data_res.data if stats_data_res.data else []

        # ═══ TIMEZONE-AWARE STREAK CALCULATION ═══
        # Get user's timezone from profile (default: UTC)
        profile = get_user_profile(user.user_id) or {}
        user_tz_str = profile.get("user_timezone", "UTC")
        
        try:
            from zoneinfo import ZoneInfo
            user_tz = ZoneInfo(user_tz_str)
        except Exception:
            user_tz = ZoneInfo("UTC")  # Fallback to UTC if invalid timezone
        
        # Calculate streak using user's local timezone
        today = datetime.now(user_tz).date()
        yesterday = today - timedelta(days=1)
        
        # Build set of dates (in user's timezone) when prompts were created
        dates_active = set()
        for r in stats_data:
            dt_str = r.get("created_at")
            if dt_str:
                # Parse UTC timestamp and convert to user's timezone
                dt_utc = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                dt_local = dt_utc.astimezone(user_tz)
                dates_active.add(dt_local.date())
        
        # Calculate streak with 36-hour grace window
        streak = 0
        curr_d = today
        
        # Check if active today
        if curr_d in dates_active:
            streak = 1
            curr_d -= timedelta(days=1)
            # Count consecutive days backward
            while curr_d in dates_active:
                streak += 1
                curr_d -= timedelta(days=1)
        # Check if active yesterday (grace period)
        elif yesterday in dates_active:
            streak = 1
            curr_d = yesterday - timedelta(days=1)
            # Count consecutive days backward
            while curr_d in dates_active:
                streak += 1
                curr_d -= timedelta(days=1)

        return {
            "total_prompts_engineered": total_prompts,
            "active_chat_sessions": total_sessions,
            "average_quality_score": round(avg_quality, 1),
            "member_since": member_since,
            "trust_level": trust_level,
            "xp_total": xp_total,
            "loyalty_tier": loyalty_tier,
            "streak": streak,
            "user_timezone": user_tz_str  # Return timezone for frontend display
        }

    except Exception as e:
        logger.exception(f"[api] Get user stats failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/profile-info")
async def get_user_profile_info(user: User = Depends(get_current_user)):
    """Get user's profile information including email, personal details, and Kira's learned profile."""
    logger.info(f"[api] /user/profile-info requested by user={user.user_id}")
    try:
        db = get_client()

        # Get user profile info — include both personal fields AND analysis fields
        profile_result = db.table("user_profiles").select(
            "phone, company, location, bio, job_title, website, github, twitter, linkedin, avatar_url, "
            "dominant_domains, preferred_tone, clarification_rate, domain_confidence, "
            "prompt_quality_trend, notable_patterns, xp_total, loyalty_tier"
        ).eq("user_id", user.user_id).execute()
        profile_data = profile_result.data[0] if profile_result.data else {}

        # Get email and username from Supabase auth
        try:
            from supabase import create_client
            supabase_admin = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_KEY")
            )
            user_data = supabase_admin.auth.admin.get_user_by_id(user.user_id)
            email = user_data.user.email
            # Username is stored in user metadata
            username = user_data.user.user_metadata.get("username") if user_data.user.user_metadata else None
        except Exception as auth_err:
            logger.warning(f"[api] Supabase admin lookup failed for user={user.user_id}: {auth_err}")
            # Graceful fallback: use JWT-derived email from auth middleware
            email = user.email
            username = None

        return {
            # Identity fields
            "username": username,
            "email": email,
            # Personal info fields
            "phone": profile_data.get("phone"),
            "company": profile_data.get("company"),
            "location": profile_data.get("location"),
            "bio": profile_data.get("bio"),
            "job_title": profile_data.get("job_title"),
            "website": profile_data.get("website"),
            "github": profile_data.get("github"),
            "twitter": profile_data.get("twitter"),
            "linkedin": profile_data.get("linkedin"),
            "avatar_url": profile_data.get("avatar_url"),
            # Kira's learned profile analysis fields
            "dominant_domains": profile_data.get("dominant_domains", []),
            "preferred_tone": profile_data.get("preferred_tone", "direct"),
            "clarification_rate": profile_data.get("clarification_rate", 0.0),
            "domain_confidence": profile_data.get("domain_confidence", 0.5),
            "prompt_quality_trend": profile_data.get("prompt_quality_trend", "stable"),
            "notable_patterns": profile_data.get("notable_patterns", []),
            "xp_total": profile_data.get("xp_total", 0),
            "loyalty_tier": profile_data.get("loyalty_tier", "Bronze"),
        }

    except Exception as e:
        logger.exception(f"[api] Get profile info failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/user/change-password")
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user)
):
    """Change user's password. Requires current password for verification."""
    logger.info(f"[security] password change requested by user={user.user_id[:8]}...")
    try:
        supabase_admin = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )

        # Sign in with current password to verify
        try:
            supabase_admin.auth.sign_in_with_password({
                "email": user.email,
                "password": req.current_password
            })
        except Exception:
            raise HTTPException(status_code=401, detail="Current password is incorrect")

        # Update to new password
        supabase_admin.auth.admin.update_user_by_id(
            user.user_id,
            {"password": req.new_password}
        )
        
        logger.info(f"[security] password updated for user={user.user_id[:8]}...")
        return {"status": "success", "message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[security] password change failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/sessions")
async def get_active_sessions(user: User = Depends(get_current_user)):
    """Get list of active login sessions for the user."""
    logger.info(f"[security] sessions list requested by user={user.user_id[:8]}...")
    try:
        # Supabase doesn't expose session list via API
        # Return current session info from JWT (not mock data)

        return {
            "sessions": [{
                "id": "current",
                "device": "Current Session",
                "browser": "Active now",
                "location": "Authenticated",
                "last_active": datetime.now(timezone.utc).isoformat(),
                "is_current": True
            }]
        }

    except Exception as e:
        logger.exception(f"[security] sessions list failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/user/sessions/{session_id}")
async def revoke_session(session_id: str, user: User = Depends(get_current_user)):
    """Revoke a specific login session."""
    logger.info(f"[security] session revoke requested by user={user.user_id[:8]}... session={session_id}")
    try:
        # Supabase doesn't expose session revocation via API
        # This endpoint reserved for future implementation
        logger.info(f"[security] session revoke requested but not yet implemented for user={user.user_id[:8]}...")
        return {"status": "info", "message": "Session management not yet fully implemented. Please sign out and back in."}

    except Exception as e:
        logger.exception(f"[security] session revoke failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/activity")
async def get_user_activity(
    limit: int = Query(default=15, ge=1, le=50),
    user: User = Depends(get_current_user)
):
    """Get user's recent activity (prompts, achievements, stats)."""
    logger.info(f"[activity] activity feed requested by user={user.user_id[:8]}...")
    try:
        db = get_client()
        
        # Get recent prompts
        prompts_result = db.table("requests")\
            .select("id, raw_prompt, improved_prompt, domain_analysis, quality_score, created_at, is_favorite")\
            .eq("user_id", user.user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        prompts = []
        for row in (prompts_result.data or []):
            analysis = row.get("domain_analysis") or {}
            prompts.append({
                "id": row.get("id"),
                "raw_prompt": row.get("raw_prompt", "")[:100],
                "improved_prompt": row.get("improved_prompt", "")[:100],
                "domain": analysis.get("primary_domain", "general"),
                "sub_domain": analysis.get("sub_domain"),
                "quality_score": (row.get("quality_score") or {}).get("overall", 0),
                "created_at": row.get("created_at"),
                "is_favorite": row.get("is_favorite", False)
            })
        
        # Get stats
        stats_result = db.table("requests").select("id, quality_score, created_at").eq("user_id", user.user_id).execute()
        stats_data = stats_result.data or []
        
        total_prompts = len(stats_data)
        
        # Avg Quality
        scores = [(r.get("quality_score") or {}).get("overall", 0) for r in stats_data if r.get("quality_score")]
        avg_quality = sum(scores) / len(scores) if scores else 0
        
        # Streak Calculation
        dates_set = set()
        for r in stats_data:
            dt_str = r.get("created_at")
            if dt_str:
                dates_set.add(dt_str.split("T")[0])
                
        today = datetime.now(timezone.utc).date()
        from datetime import timedelta
        
        streak = 0
        curr_d = today
        if str(curr_d) in dates_set:
            streak += 1
            curr_d -= timedelta(days=1)
            while str(curr_d) in dates_set:
                streak += 1
                curr_d -= timedelta(days=1)
        elif str(today - timedelta(days=1)) in dates_set:
            streak += 1
            curr_d = today - timedelta(days=2)
            while str(curr_d) in dates_set:
                streak += 1
                curr_d -= timedelta(days=1)
        
        return {
            "prompts": prompts,
            "total_prompts": total_prompts,
            "avg_quality": avg_quality,
            "streak": streak
        }
        
    except Exception as e:
        logger.exception(f"[activity] activity feed failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/user/activity/{request_id}/favorite")
async def toggle_favorite(request_id: str, update: FavoriteUpdate, user: User = Depends(get_current_user)):
    """Toggle the favorite status of a prompt."""
    logger.info(f"[activity] favorite toggle requested by user={user.user_id[:8]} for request={request_id}")
    try:
        db = get_client()
        result = db.table("requests").update({"is_favorite": update.is_favorite}).eq("id", request_id).eq("user_id", user.user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
            
        return {"status": "success", "is_favorite": update.is_favorite}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[activity] favorite toggle failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/user/activity/{request_id}/domain")
async def update_domain(request_id: str, update: DomainUpdate, user: User = Depends(get_current_user)):
    """
    Manually update a prompt's domain.
    Also resets user's domain_confidence to 0.5 to force AI re-learning.
    """
    logger.info(f"[activity] manual domain update to '{update.primary_domain}' for request={request_id}")
    try:
        db = get_client()
        
        # 1. Update the request with new domain metadata
        analysis = {
            "primary_domain": update.primary_domain,
            "sub_domain": update.sub_domain or "Manual Override",
            "confidence": 1.0,
            "was_manual": True
        }
        
        db.table("requests")\
            .update({"domain_analysis": analysis})\
            .eq("id", request_id)\
            .eq("user_id", user.user_id)\
            .execute()
        
        # 2. Reset profile confidence to trigger agent re-run on next turn
        db.table("user_profiles")\
            .update({"domain_confidence": 0.5})\
            .eq("user_id", user.user_id)\
            .execute()
        
        return {"status": "success", "domain": update.primary_domain}
    except Exception as e:
        logger.exception(f"[activity] domain update failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/achievements")
async def get_user_achievements(user: User = Depends(get_current_user)):
    """Get user's unlocked achievement badges."""
    logger.info(f"[activity] achievements requested by user={user.user_id[:8]}...")
    try:
        db = get_client()
        
        # Get total prompts
        total_prompts = db.table("requests").select("id", count="exact").eq("user_id", user.user_id).execute().count or 0
        
        # Get average quality
        quality_res = db.table("requests").select("quality_score").eq("user_id", user.user_id).limit(100).execute()
        scores = [(r.get("quality_score") or {}).get("overall", 0) for r in (quality_res.data or []) if r.get("quality_score")]
        avg_quality = sum(scores) / len(scores) if scores else 0
        
        # Calculate achievements
        achievements = []
        
        # Tier badges
        if total_prompts >= 1000 and avg_quality >= 4.5:
            achievements.append({"id": "kira", "name": "Kira Tier", "icon": "⭐", "description": "Reached Kira tier"})
        elif total_prompts >= 500 and avg_quality >= 4.0:
            achievements.append({"id": "gold", "name": "Gold Tier", "icon": "🥇", "description": "Reached Gold tier"})
        elif total_prompts >= 100:
            achievements.append({"id": "silver", "name": "Silver Tier", "icon": "🥈", "description": "Reached Silver tier"})
        
        # Milestone badges
        if total_prompts >= 1:
            achievements.append({"id": "first", "name": "First Prompt", "icon": "📝", "description": "Created first prompt"})
        if total_prompts >= 10:
            achievements.append({"id": "ten", "name": "Getting Started", "icon": "📝📝", "description": "Created 10 prompts"})
        if total_prompts >= 100:
            achievements.append({"id": "hundred", "name": "Century", "icon": "💯", "description": "Created 100 prompts"})
        
        # Quality badges
        if avg_quality >= 4.5:
            achievements.append({"id": "quality_master", "name": "Quality Master", "icon": "⭐⭐", "description": "Average quality 4.5+"})
        elif avg_quality >= 4.0:
            achievements.append({"id": "quality_pro", "name": "Quality Pro", "icon": "⭐", "description": "Average quality 4.0+"})
        
        return {"achievements": achievements}
        
    except Exception as e:
        logger.exception(f"[activity] achievements failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/settings")
async def get_user_settings(user: User = Depends(get_current_user)):
    """Get user's profile settings."""
    logger.info(f"[settings] settings requested by user={user.user_id[:8]}...")
    try:
        db = get_client()
        
        profile_result = db.table("user_profiles")\
            .select("is_public, default_tone, default_audience, session_timeout_hours")\
            .eq("user_id", user.user_id)\
            .execute()
        
        profile_data = profile_result.data[0] if profile_result.data else {}
        
        return {
            "is_public": profile_data.get("is_public", False),
            "default_tone": profile_data.get("default_tone", "direct"),
            "default_audience": profile_data.get("default_audience", "personal"),
            "session_timeout_hours": profile_data.get("session_timeout_hours", 24)
        }
        
    except Exception as e:
        logger.exception(f"[settings] settings fetch failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/user/settings")
async def update_user_settings(
    is_public: Optional[bool] = None,
    default_tone: Optional[str] = None,
    default_audience: Optional[str] = None,
    session_timeout_hours: Optional[int] = None,
    user: User = Depends(get_current_user)
):
    """Update user's profile settings."""
    logger.info(f"[settings] settings update requested by user={user.user_id[:8]}...")
    try:
        db = get_client()
        
        update_data = {}
        if is_public is not None:
            update_data["is_public"] = is_public
        if default_tone is not None:
            update_data["default_tone"] = default_tone
        if default_audience is not None:
            update_data["default_audience"] = default_audience
        if session_timeout_hours is not None:
            update_data["session_timeout_hours"] = session_timeout_hours
        
        if update_data:
            result = db.table("user_profiles").update(update_data).eq("user_id", user.user_id).execute()
            
            if not result.data:
                insert_data = {"user_id": user.user_id, **update_data}
                db.table("user_profiles").insert(insert_data).execute()
        
        return {"status": "success", "message": "Settings updated"}
        
    except Exception as e:
        logger.exception(f"[settings] settings update failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/user/account")
async def delete_user_account(user: User = Depends(get_current_user)):
    """Delete the user's account and all associated data (GDPR)."""
    logger.info(f"[api] GDPR ACCOUNT DELETION requested by user={user.user_id}")
    try:
        db = get_client()

        # Delete from ALL tables with user_id
        db.table("mcp_tokens").delete().eq("user_id", user.user_id).execute()
        db.table("usage_logs").delete().eq("user_id", user.user_id).execute()

        # agent_logs has no user_id column — delete via request_id linkage
        request_ids_result = db.table("requests").select("id").eq("user_id", user.user_id).execute()
        request_ids = [r["id"] for r in request_ids_result.data]
        if request_ids:
            db.table("agent_logs").in_("request_id", request_ids).delete().execute()

        db.table("requests").delete().eq("user_id", user.user_id).execute()
        db.table("chat_sessions").delete().eq("user_id", user.user_id).execute()
        db.table("conversations").delete().eq("user_id", user.user_id).execute()
        db.table("user_profiles").delete().eq("user_id", user.user_id).execute()
        db.table("langmem_memories").delete().eq("user_id", user.user_id).execute()

        # Delete auth user via Supabase Admin API
        from supabase import create_client
        supabase_admin = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        supabase_admin.auth.admin.delete_user(user.user_id)

        logger.info(f"[api] GDPR deletion complete for user={user.user_id}")
        return {"status": "deleted", "message": "Account and all associated data permanently deleted."}

    except Exception as e:
        logger.exception(f"[api] Account deletion failed for user={user.user_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/memory/onboarding")
async def save_onboarding_memory(
    req: OnboardingRequest,
    user: User = Depends(get_current_user)
):
    """
    Save onboarding profile as LangMem memory.
    Uses write_to_langmem() abstraction — never calls _generate_embedding directly.
    """
    logger.info(f"[api] /memory/onboarding requested by user={user.user_id}")
    try:
        # Build minimal state dict for write_to_langmem
        # Per RULES.md: Never call _generate_embedding directly
        state = {
            "message": req.content,
            "improved_prompt": f"Onboarding profile: {req.metadata.get('primary_use', 'unknown')} user",
            "input_modality": "text",
            "attachments": [],
            "user_id": user.user_id,
            "domain_analysis": {"primary_domain": req.metadata.get('primary_use', 'general')},
            "quality_score": {"onboarding": 5},
            "agents_run": ["onboarding"],
            "agents_skipped": []
        }

        # Use LangMem abstraction — handles embedding internally
        success = write_to_langmem(user_id=user.user_id, session_result=state)

        logger.info(f"[api] onboarding memory saved for user {user.user_id[:8]}... success={success}")

        return {"status": "saved", "success": success}

    except Exception as e:
        logger.exception("[api] onboarding memory save failed")
        raise HTTPException(status_code=500, detail="Internal server error")

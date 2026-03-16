# routes/history.py
# ─────────────────────────────────────────────
# History, Search, Analytics, and Version Control Endpoints
#   GET  /history              → Past prompts
#   GET  /conversation         → Full chat history
#   POST /history/search       → Semantic/keyword search
#   GET  /history/analytics    → Usage analytics
#   GET  /history/sessions     → Grouped by session
#   POST /history/version      → Create prompt version
#   GET  /history/version/{id} → Version history
#   POST /history/version/{id}/rollback → Rollback
#   GET  /history/compare      → Side-by-side diff
#
# RULES.md: <500 lines, type hints, docstrings
# ─────────────────────────────────────────────

import uuid
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from auth import User, get_current_user
from database import get_history, get_conversation_history, get_client
from service import compute_diff
from utils import calculate_overall_quality

logger = logging.getLogger(__name__)

router = APIRouter(tags=["History"])


# ── Schemas ───────────────────────────────────

class SearchQuery(BaseModel):
    """Search query schema for /history/search"""
    query: str
    use_rag: bool = True
    domains: Optional[list[str]] = []
    min_quality: int = 0
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 20


class CreateVersionRequest(BaseModel):
    """Schema for creating new prompt version"""
    raw_prompt: str
    improved_prompt: str
    change_summary: str
    session_id: str


class VersionHistoryResponse(BaseModel):
    """Response for version history query"""
    versions: list[dict]
    total: int
    current_version: int


# ── Basic History ─────────────────────────────

@router.get("/history")
def history(
    session_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user)
):
    """Get prompt history — requires JWT."""
    logger.info(f"[api] /history user_id={user.user_id} session={session_id} limit={limit}")
    data = get_history(session_id=session_id, limit=limit, user_id=user.user_id)
    return {"count": len(data), "history": data}


@router.get("/conversation")
def conversation(
    session_id: str = Query(..., description="Session ID to retrieve"),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user)
):
    """Returns full conversation history for a session — requires JWT."""
    logger.info(f"[api] /conversation user_id={user.user_id} session={session_id}")
    data = get_conversation_history(session_id=session_id, limit=limit)
    return {"count": len(data), "conversation": data}


# ── Search ────────────────────────────────────

@router.post("/history/search", response_model=dict)
async def search_history(
    search_query: SearchQuery,
    user: User = Depends(get_current_user)
):
    """Semantic search across user's prompt history with RAG toggle."""
    try:
        logger.info(f"[api] /history/search user_id={user.user_id[:8]}... query='{search_query.query[:30]}...' rag={search_query.use_rag}")
        
        if search_query.use_rag:
            from memory.langmem import query_langmem
            memories = query_langmem(
                user_id=user.user_id,
                query=search_query.query,
                top_k=search_query.limit * 2,
                surface="web_app"
            )
            results = memories
            logger.info(f"[api] RAG search returned {len(results)} memories")
        else:
            db = get_client()
            query = db.table("requests")\
                .select("*")\
                .eq("user_id", user.user_id)\
                .ilike("raw_prompt", f"%{search_query.query}%")\
                .limit(search_query.limit)
            
            if search_query.date_from:
                query = query.gte("created_at", search_query.date_from)
            if search_query.date_to:
                query = query.lte("created_at", search_query.date_to)
            
            result = query.execute()
            results = result.data or []
            logger.info(f"[api] keyword search returned {len(results)} results")
        
        # Apply filters
        filtered = results
        if search_query.domains:
            filtered = [r for r in filtered 
                       if r.get('domain_analysis', {}).get('primary_domain', '') in search_query.domains]
            filtered = [r for r in filtered if calculate_overall_quality(r.get('quality_score', {})) >= search_query.min_quality]
        
        filtered = filtered[:search_query.limit]
        logger.info(f"[api] filtered results: {len(filtered)}")
        
        return {"results": filtered, "total": len(filtered)}
    
    except Exception as e:
        logger.exception(f"[api] /history/search failed")
        raise HTTPException(status_code=500, detail="Search failed")


# ── Analytics ─────────────────────────────────

@router.get("/history/analytics", response_model=dict)
async def get_history_analytics(
    days: int = Query(default=30, ge=1, le=90),
    user: User = Depends(get_current_user)
):
    """Get user's prompt analytics and insights."""
    try:
        logger.info(f"[api] /history/analytics user_id={user.user_id[:8]}... days={days}")
        
        db = get_client()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        prompts_result = db.table("requests")\
            .select("*")\
            .eq("user_id", user.user_id)\
            .gte("created_at", cutoff.isoformat())\
            .execute()
        
        prompts = prompts_result.data or []
        total_prompts = len(prompts)
        
        quality_scores = [
            p.get("quality_score", {}).get("overall", 0)
            for p in prompts if p.get("quality_score")
        ]
        avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0
        
        domains = [p.get("domain_analysis", {}).get("primary_domain", "general") for p in prompts]
        unique_domains = len(set(domains))
        hours_saved = round((total_prompts * 5) / 60, 1)
        
        # Quality trend (daily averages)
        daily_quality = {}
        for p in prompts:
            date = p["created_at"][:10]
            if date not in daily_quality:
                daily_quality[date] = []
            qs = p.get("quality_score", {})
            if qs:
                daily_quality[date].append(calculate_overall_quality(qs))
        
        quality_trend = [
            {"date": date, "avg_quality": round(sum(scores) / len(scores), 2) if scores else 0, "prompt_count": len(scores)}
            for date, scores in sorted(daily_quality.items())
        ]
        
        # Domain distribution
        domain_counts = {}
        for d in domains:
            domain_counts[d] = domain_counts.get(d, 0) + 1
        
        # Session activity
        daily_activity = {}
        for p in prompts:
            date = p["created_at"][:10]
            daily_activity[date] = daily_activity.get(date, 0) + 1
        
        session_activity = [{"date": date, "count": count} for date, count in sorted(daily_activity.items())]
        
        return {
            "total_prompts": total_prompts,
            "avg_quality": avg_quality,
            "unique_domains": unique_domains,
            "hours_saved": hours_saved,
            "quality_trend": quality_trend,
            "domain_distribution": domain_counts,
            "session_activity": session_activity
        }
    
    except Exception as e:
        logger.exception(f"[api] /history/analytics failed")
        raise HTTPException(status_code=500, detail="Failed to load analytics")


@router.get("/history/sessions", response_model=dict)
async def get_history_sessions(
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Get prompt history grouped by chat sessions."""
    try:
        logger.info(f"[api] /history/sessions user_id={user.user_id[:8]}... limit={limit}")
        
        db = get_client()
        sessions_result = db.table("chat_sessions")\
            .select("id, title, created_at, last_activity")\
            .eq("user_id", user.user_id)\
            .order("last_activity", desc=True)\
            .limit(limit)\
            .execute()
        
        sessions = []
        for session in sessions_result.data or []:
            prompts_result = db.table("requests")\
                .select("*")\
                .eq("session_id", session["id"])\
                .eq("user_id", user.user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            quality_scores = [
                r.get("quality_score", {}).get("overall", 0)
                for r in prompts_result.data or [] if r.get("quality_score")
            ]
            avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0
            
            domains = [r.get("domain_analysis", {}).get("primary_domain", "general") for r in prompts_result.data or []]
            primary_domain = max(set(domains), key=domains.count) if domains else "general"
            
            sessions.append({
                "session_id": session["id"],
                "title": session["title"] or "Untitled Chat",
                "prompt_count": len(prompts_result.data or []),
                "avg_quality": avg_quality,
                "domain": primary_domain,
                "prompts": prompts_result.data or [],
                "created_at": session["created_at"],
                "last_activity": session["last_activity"]
            })
        
        return {"sessions": sessions}

    except Exception as e:
        logger.exception(f"[api] /history/sessions failed")
        raise HTTPException(status_code=500, detail="Failed to load sessions")


# ── Version Control ───────────────────────────

@router.post("/history/version", response_model=dict)
async def create_prompt_version(
    req: CreateVersionRequest,
    user: User = Depends(get_current_user)
):
    """Create a new version of an existing prompt."""
    try:
        logger.info(f"[api] create_version user_id={user.user_id[:8]}... session={req.session_id[:8]}...")
        db = get_client()

        latest = db.table("requests")\
            .select("id, version_id, version_number")\
            .eq("session_id", req.session_id)\
            .eq("user_id", user.user_id)\
            .order("version_number", desc=True)\
            .limit(1)\
            .execute()

        if not latest.data:
            version_id = str(uuid.uuid4())
            version_number = 1
            parent_version_id = None
        else:
            version_id = latest.data[0]["version_id"]
            version_number = latest.data[0]["version_number"] + 1
            parent_version_id = latest.data[0]["id"]

        if parent_version_id:
            db.table("requests")\
                .update({"is_production": False})\
                .eq("id", parent_version_id)\
                .eq("user_id", user.user_id)\
                .execute()

        new_version = db.table("requests")\
            .insert({
                "user_id": user.user_id,
                "session_id": req.session_id,
                "version_id": version_id,
                "version_number": version_number,
                "parent_version_id": parent_version_id,
                "raw_prompt": req.raw_prompt,
                "improved_prompt": req.improved_prompt,
                "change_summary": req.change_summary,
                "is_production": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })\
            .execute()

        logger.info(f"[api] created version {version_number} for {version_id[:8]}...")
        return {"version_id": version_id, "version_number": version_number, "id": new_version.data[0]["id"]}

    except Exception as e:
        logger.exception(f"[api] create_version failed")
        raise HTTPException(status_code=500, detail="Failed to create version")


@router.get("/history/version/{version_id}", response_model=dict)
async def get_version_history(
    version_id: str,
    user: User = Depends(get_current_user)
):
    """Get all versions of a specific prompt."""
    try:
        logger.info(f"[api] get_version_history user_id={user.user_id[:8]}... version={version_id[:8]}...")
        db = get_client()

        versions = db.table("requests")\
            .select("*")\
            .eq("version_id", version_id)\
            .eq("user_id", user.user_id)\
            .order("version_number", asc=True)\
            .execute()

        return {
            "versions": versions.data or [],
            "total": len(versions.data or []),
            "current_version": max([v["version_number"] for v in versions.data], default=0)
        }

    except Exception as e:
        logger.exception(f"[api] get_version_history failed")
        raise HTTPException(status_code=500, detail="Failed to get version history")


@router.post("/history/version/{version_id}/rollback", response_model=dict)
async def rollback_to_version(
    version_id: str,
    target_version_number: int = Query(..., ge=1),
    user: User = Depends(get_current_user)
):
    """Rollback to a previous version."""
    try:
        logger.info(f"[api] rollback user_id={user.user_id[:8]}... version={version_id[:8]}... target={target_version_number}")
        db = get_client()

        target = db.table("requests")\
            .select("*")\
            .eq("version_id", version_id)\
            .eq("version_number", target_version_number)\
            .eq("user_id", user.user_id)\
            .execute()

        if not target.data:
            raise HTTPException(status_code=404, detail="Version not found")

        db.table("requests")\
            .update({"is_production": False})\
            .eq("version_id", version_id)\
            .eq("user_id", user.user_id)\
            .execute()

        db.table("requests")\
            .update({"is_production": True})\
            .eq("id", target.data[0]["id"])\
            .eq("user_id", user.user_id)\
            .execute()

        logger.info(f"[api] rolled back to version {target_version_number}")
        return {"success": True, "rolled_back_to": target_version_number}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[api] rollback failed")
        raise HTTPException(status_code=500, detail="Failed to rollback")


@router.get("/history/compare", response_model=dict)
async def compare_versions(
    version_id: str,
    v1: int = Query(..., ge=1),
    v2: int = Query(..., ge=1),
    user: User = Depends(get_current_user)
):
    """Compare two versions side-by-side."""
    try:
        logger.info(f"[api] compare_versions user_id={user.user_id[:8]}... v1={v1} v2={v2}")
        db = get_client()

        versions = db.table("requests")\
            .select("*")\
            .eq("version_id", version_id)\
            .eq("user_id", user.user_id)\
            .in_("version_number", [v1, v2])\
            .order("version_number", asc=True)\
            .execute()

        if len(versions.data or []) < 2:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        return {
            "version_1": versions.data[0],
            "version_2": versions.data[1],
            "diff": compute_diff(
                versions.data[0]["improved_prompt"],
                versions.data[1]["improved_prompt"]
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[api] compare_versions failed")
        raise HTTPException(status_code=500, detail="Failed to compare versions")

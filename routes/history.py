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
    offset: int = 0


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

# ── Search ────────────────────────────────────

@router.post("/history/search", response_model=dict)
async def search_history(
    search_query: SearchQuery,
    user: User = Depends(get_current_user)
):
    """
    Robust search across user's prompt history.
    Unifies RAG and Keyword results and fixes legacy filtering bugs.
    """
    try:
        logger.info(f"[api] /history/search user_id={user.user_id[:8]}... query='{search_query.query[:30]}...' rag={search_query.use_rag}")
        
        results = []
        mode_used = "rag" if search_query.use_rag else "keyword"

        # ═══ Branch 1: Semantic Search (RAG) ═══
        if search_query.use_rag:
            from memory.langmem import query_langmem
            memories = query_langmem(
                user_id=user.user_id,
                query=search_query.query,
                top_k=search_query.limit * 2,
                surface="web_app"
            )
            
            # Map memory objects to unified SearchResult shape
            for m in memories:
                results.append({
                    "id": m.get("id"),
                    "raw_prompt": m.get("content", ""),
                    "improved_prompt": m.get("improved_content", ""),
                    "domain": m.get("domain", "general"),
                    "quality_score": m.get("quality_score", {}),
                    "created_at": m.get("created_at"),
                    "search_score": m.get("similarity_score", 0),
                    "session_id": m.get("session_id")
                })

        # ═══ Branch 2: Keyword Search (or Fallback) ═══
        if not results:  # (Either Keyword mode was picked OR RAG returned zero results)
            if search_query.use_rag and memories: # RAG was used but all filtered by similarity
                logger.info(f"[api] RAG similarity too low → falling back to keyword search")
            
            mode_used = "keyword"
            db = get_client()
            # Escape SQL wildcards to prevent injection
            sanitized_query = search_query.query.replace('%', '\\%').replace('_', '\\_')
            query_obj = db.table("requests")\
                .select("*")\
                .eq("user_id", user.user_id)\
                .ilike("raw_prompt", f"%{sanitized_query}%")\
                .limit(search_query.limit)
            
            if search_query.date_from:
                query_obj = query_obj.gte("created_at", search_query.date_from)
            if search_query.date_to:
                query_obj = query_obj.lte("created_at", search_query.date_to)
            
            # Sub-200ms Paginated Query
            query_obj = query_obj.range(search_query.offset, search_query.offset + search_query.limit - 1)
            
            db_res = query_obj.execute()
            for r in (db_res.data or []):
                # Map DB row to unified SearchResult shape
                results.append({
                    "id": r.get("id"),
                    "raw_prompt": r.get("raw_prompt", ""),
                    "improved_prompt": r.get("improved_prompt", ""),
                    # FIX: Handle None domain_analysis safely
                    "domain": (r.get("domain_analysis") or {}).get("primary_domain", "general"),
                    "quality_score": r.get("quality_score", {}),
                    "created_at": r.get("created_at"),
                    "search_score": 1.0,
                    "session_id": r.get("session_id"),
                    "is_favorite": r.get("is_favorite", False)
                })

        # ═══ Robust Filtering ═══
        filtered = results
        
        # Domain Filter (Now uses unified 'domain' key)
        if search_query.domains:
            filtered = [r for r in filtered if r.get("domain") in search_query.domains]
        
        # Quality Filter
        if search_query.min_quality > 0:
            filtered = [r for r in filtered if calculate_overall_quality(r.get("quality_score", {})) >= search_query.min_quality]
        
        # Sort and truncate
        filtered.sort(key=lambda x: x.get("search_score", 0), reverse=True)
        final_results = filtered[:search_query.limit]
        
        logger.info(f"[api] search complete. Mode: {mode_used}, Found: {len(results)}, Filtered: {len(final_results)}")
        
        return {
            "results": final_results,
            "total": len(final_results),
            "search_mode": mode_used
        }

    except Exception as e:
        logger.exception(f"[api] /history/search robust failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Search engine failed")


@router.get("/history/sessions", response_model=dict)
async def get_history_sessions(
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Get prompt history grouped by chat sessions.
    [SENIOR DEV FIX]: Eliminates N+1 query problem using single-query batch retrieval.
    """
    try:
        logger.info(f"[api] /history/sessions user_id={user.user_id[:8]}... limit={limit} offset={offset}")
        
        db = get_client()
        sessions_result = db.table("chat_sessions")\
            .select("id, title, created_at, last_activity")\
            .eq("user_id", user.user_id)\
            .order("last_activity", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        if not sessions_result.data:
            return {"sessions": [], "total": 0}

        session_ids = [s["id"] for s in sessions_result.data]

        # 🚀 BATCH FETCH: Get all prompts for these sessions in ONE query
        prompts_result = db.table("requests")\
            .select("*")\
            .in_("session_id", session_ids)\
            .eq("user_id", user.user_id)\
            .order("created_at", desc=True)\
            .execute()

        # Group prompts by session_id in Python memory (O(N) efficiency)
        prompts_by_session = {}
        for r in (prompts_result.data or []):
            sid = r["session_id"]
            if sid not in prompts_by_session:
                prompts_by_session[sid] = []
            prompts_by_session[sid].append(r)

        sessions = []
        for session in sessions_result.data:
            session_prompts = prompts_by_session.get(session["id"], [])
            
            quality_scores = [
                calculate_overall_quality(r.get("quality_score", {}))
                for r in session_prompts
            ]
            avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0

            # FIX: Handle None domain_analysis safely
            domains = [
                (r.get("domain_analysis") or {}).get("primary_domain", "general")
                for r in session_prompts
            ]
            primary_domain = max(set(domains), key=domains.count) if domains else "general"
            
            sessions.append({
                "session_id": session["id"],
                "title": session["title"] or "Untitled Chat",
                "prompt_count": len(session_prompts),
                "avg_quality": avg_quality,
                "domain": primary_domain,
                "prompts": session_prompts,
                "created_at": session["created_at"],
                "last_activity": session["last_activity"]
            })
        
        return {"sessions": sessions, "total": len(sessions)}

    except Exception as e:
        logger.exception(f"[api] /history/sessions batch failed")
        raise HTTPException(status_code=500, detail="Failed to load sessions")


@router.patch("/history/session/{session_id}", response_model=dict)
async def rename_session(
    session_id: str,
    title: str = Query(..., min_length=1),
    user: User = Depends(get_current_user)
):
    """Rename a conversation session."""
    try:
        db = get_client()
        db.table("chat_sessions")\
            .update({"title": title})\
            .eq("id", session_id)\
            .eq("user_id", user.user_id)\
            .execute()
        return {"success": True, "new_title": title}
    except Exception as e:
        logger.exception(f"[api] rename_session failed")
        raise HTTPException(status_code=500, detail="Failed to rename session")


class BulkDeleteRequest(BaseModel):
    ids: list[str]

@router.post("/history/bulk-delete", response_model=dict)
async def bulk_delete_prompts(
    req: BulkDeleteRequest,
    user: User = Depends(get_current_user)
):
    """Delete multiple prompts at once."""
    try:
        db = get_client()
        db.table("requests")\
            .delete()\
            .in_("id", req.ids)\
            .eq("user_id", user.user_id)\
            .execute()
        return {"success": True, "deleted_count": len(req.ids)}
    except Exception as e:
        logger.exception(f"[api] bulk_delete failed")
        raise HTTPException(status_code=500, detail="Bulk delete failed")


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
            .order("version_number", desc=False)\
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
            .order("version_number", desc=False)\
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

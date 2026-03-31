# routes/analytics.py
# ─────────────────────────────────────────────
# Analytics & Persona Intelligence Endpoints
#   GET  /analytics/summary     → Main dashboard metrics
#   GET  /analytics/heatmap     → 365-day activity grid
#
# RULES.md: <500 lines, type hints, docstring, high performance
# ─────────────────────────────────────────────

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query

from auth import User, get_current_user
from database import get_client
from utils import calculate_overall_quality

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics"])

@router.get("/analytics/summary", response_model=dict)
async def get_analytics_summary(
    days: int = Query(default=30, ge=1, le=90),
    user: User = Depends(get_current_user)
):
    """
    Get user's consolidated analytics and insights.
    Replaces the legacy /history/analytics with optimized logic.
    """
    try:
        logger.info(f"[api] /analytics/summary user_id={user.user_id[:8]}... days={days}")
        
        db = get_client()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Batch fetch prompts for the period
        prompts_result = db.table("requests")\
            .select("id, created_at, quality_score, domain_analysis")\
            .eq("user_id", user.user_id)\
            .gte("created_at", cutoff.isoformat())\
            .execute()
        
        prompts = prompts_result.data or []
        total_prompts = len(prompts)
        
        # Calculate base metrics
        quality_scores = [
            calculate_overall_quality(p.get("quality_score", {}))
            for p in prompts if p.get("quality_score")
        ]
        avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0
        
        # Domain distribution (Skill vs Volume)
        domain_data = {}
        for p in prompts:
            d = (p.get("domain_analysis") or {}).get("primary_domain", "general")
            if d not in domain_data:
                domain_data[d] = {"count": 0, "total_quality": 0, "quality_count": 0}
            
            domain_data[d]["count"] += 1
            qs = p.get("quality_score")
            if qs:
                domain_data[d]["total_quality"] += calculate_overall_quality(qs)
                domain_data[d]["quality_count"] += 1
        
        domain_distribution = {
            d: {
                "count": stats["count"],
                "avg_quality": round(stats["total_quality"] / stats["quality_count"], 2) if stats["quality_count"] > 0 else 0
            }
            for d, stats in domain_data.items()
        }

        # Optimized unique domains count
        unique_domains = len(domain_distribution)
        hours_saved = round((total_prompts * 5) / 60, 1)

        return {
            "total_prompts": total_prompts,
            "avg_quality": avg_quality,
            "unique_domains": unique_domains,
            "hours_saved": hours_saved,
            "domain_distribution": domain_distribution
        }
    
    except Exception as e:
        logger.exception(f"[api] /analytics/summary failed")
        raise HTTPException(status_code=500, detail="Failed to load analytics summary")

@router.get("/analytics/heatmap", response_model=dict)
async def get_activity_heatmap(user: User = Depends(get_current_user)):
    """
    High-Performance Activity Aggregator for 365-day contributions.
    Fact: Only fetches created_at to minimize data transfer.
    """
    try:
        logger.info(f"[api] /analytics/heatmap user_id={user.user_id[:8]}...")
        
        db = get_client()
        # Fetch only what is needed for the heatmap (last 365 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        
        result = db.table("requests")\
            .select("created_at")\
            .eq("user_id", user.user_id)\
            .gte("created_at", cutoff.isoformat())\
            .execute()
        
        daily_activity = {}
        for row in result.data:
            date = row["created_at"][:10]
            daily_activity[date] = daily_activity.get(date, 0) + 1
            
        heatmap_data = [{"date": d, "count": c} for d, c in sorted(daily_activity.items())]
        
        return {
            "heatmap": heatmap_data,
            "total_year_prompts": sum(daily_activity.values()),
            "max_daily": max(daily_activity.values()) if daily_activity else 0
        }
        
    except Exception as e:
        logger.exception(f"[api] /analytics/heatmap failed")
        raise HTTPException(status_code=500, detail="Failed to load activity heatmap")

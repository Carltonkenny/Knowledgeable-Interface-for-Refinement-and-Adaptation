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
            if stats["count"] > 0  # Only show used domains
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
    PHASE 5 UPDATE: Now includes average quality score per day for intensity coloring.
    
    Returns:
        {
            "heatmap": [
                {"date": "2026-03-31", "count": 5, "avg_quality": 4.2},
                ...
            ],
            "total_year_prompts": 150,
            "max_daily": 12
        }
    """
    try:
        logger.info(f"[api] /analytics/heatmap user_id={user.user_id[:8]}...")

        db = get_client()
        # Fetch only what is needed for the heatmap (last 365 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)

        result = db.table("requests")\
            .select("created_at, quality_score")\
            .eq("user_id", user.user_id)\
            .gte("created_at", cutoff.isoformat())\
            .execute()

        # PHASE 5: Aggregate both count AND quality per day
        daily_data = {}
        for row in result.data:
            date = row["created_at"][:10]
            if date not in daily_data:
                daily_data[date] = {"count": 0, "quality_sum": 0.0, "quality_count": 0}
            
            daily_data[date]["count"] += 1
            
            # Aggregate quality scores
            qs = row.get("quality_score")
            if qs:
                quality = calculate_overall_quality(qs)
                daily_data[date]["quality_sum"] += quality
                daily_data[date]["quality_count"] += 1

        # Build response with avg_quality per day
        heatmap_data = []
        for date, data in sorted(daily_data.items()):
            avg_quality = (
                round(data["quality_sum"] / data["quality_count"], 2)
                if data["quality_count"] > 0 else 0.0
            )
            heatmap_data.append({
                "date": date,
                "count": data["count"],
                "avg_quality": avg_quality  # PHASE 5: New field
            })

        return {
            "heatmap": heatmap_data,
            "total_year_prompts": sum(d["count"] for d in heatmap_data),
            "max_daily": max(d["count"] for d in heatmap_data) if heatmap_data else 0,
            "avg_quality_overall": round(
                sum(d["avg_quality"] for d in heatmap_data) / len(heatmap_data), 2
            ) if heatmap_data else 0.0
        }

    except Exception as e:
        logger.exception(f"[api] /analytics/heatmap failed")
        raise HTTPException(status_code=500, detail="Failed to load activity heatmap")

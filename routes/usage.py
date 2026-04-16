# routes/usage.py
# ─────────────────────────────────────────────
# Usage Tracking Endpoints
#   GET /usage/current → Get current usage stats
#   GET /usage/history → Get usage history
#
# RULES.md: <500 lines, type hints, docstrings
# ─────────────────────────────────────────────

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from auth import User, get_current_user
from database import get_user_usage, get_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Usage"])


# ── Response Models ───────────────────────────

class UsageLimit(BaseModel):
    """Usage limit with used, remaining, and percentage."""
    used: int
    limit: int
    remaining: int
    percentage: float


class UsageResponse(BaseModel):
    """Current usage stats response."""
    user_id: str
    daily: UsageLimit
    monthly: UsageLimit
    hourly_limit: int


class HistoryEntry(BaseModel):
    """Single day usage history entry."""
    date: str
    requests: int


class UsageHistoryResponse(BaseModel):
    """Usage history response."""
    user_id: str
    days: int
    total_requests: int
    avg_per_day: float
    history: list[HistoryEntry]


# ── Endpoints ──────────────────────────────────

@router.get("/usage/current", response_model=UsageResponse)
async def get_current_usage(user: User = Depends(get_current_user)):
    """
    Get current usage stats for authenticated user.

    Returns daily and monthly usage with limits.

    **Use cases:**
    - User checks remaining requests for today
    - Display usage progress in UI
    - Warn when approaching limits

    **Example response:**
    ```json
    {
      "user_id": "abc123...",
      "daily": {
        "used": 25,
        "limit": 50,
        "remaining": 25,
        "percentage": 50.0
      },
      "monthly": {
        "used": 800,
        "limit": 1500,
        "remaining": 700,
        "percentage": 53.3
      },
      "hourly_limit": 10
    }
    ```
    """
    logger.info(f"[api] /usage/current user_id={user.user_id[:8]}...")

    usage = get_user_usage(user.user_id)

    # Calculate percentages safely (avoid division by zero)
    daily_pct = round(
        (usage["daily_count"] / usage["daily_limit"]) * 100
        if usage["daily_limit"] > 0 else 0.0, 2
    )
    monthly_pct = round(
        (usage["monthly_count"] / usage["monthly_limit"]) * 100
        if usage["monthly_limit"] > 0 else 0.0, 2
    )

    return UsageResponse(
        user_id=user.user_id[:8] + "...",
        daily=UsageLimit(
            used=usage["daily_count"],
            limit=usage["daily_limit"],
            remaining=max(0, usage["daily_limit"] - usage["daily_count"]),
            percentage=daily_pct
        ),
        monthly=UsageLimit(
            used=usage["monthly_count"],
            limit=usage["monthly_limit"],
            remaining=max(0, usage["monthly_limit"] - usage["monthly_count"]),
            percentage=monthly_pct
        ),
        hourly_limit=usage["hourly_limit"]
    )


@router.get("/usage/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    days: Optional[int] = 30,
    user: User = Depends(get_current_user)
):
    """
    Get usage history for specified number of days.

    **Args:**
        days: Number of days to retrieve (default: 30, max: 90)

    **Use cases:**
    - User views usage trends over time
    - Identify heavy usage days
    - Export usage data for analysis

    **Example response:**
    ```json
    {
      "user_id": "abc123...",
      "days": 7,
      "total_requests": 175,
      "avg_per_day": 25.0,
      "history": [
        {"date": "2026-03-24", "requests": 30},
        {"date": "2026-03-23", "requests": 25},
        ...
      ]
    }
    ```
    """
    # Validate days parameter
    if days is None or days < 1:
        days = 30
    elif days > 90:
        days = 90  # Cap at 90 days to prevent excessive queries

    logger.info(f"[api] /usage/history user_id={user.user_id[:8]}... days={days}")

    try:
        db = get_client()
        today = datetime.now(timezone.utc).date()
        start_date = (today - timedelta(days=days)).isoformat()

        result = db.table("usage_logs").select(
            "date, requests_count"
        ).eq(
            "user_id", user.user_id
        ).gte(
            "date", start_date
        ).order(
            "date", desc=True
        ).execute()

        # Group by date (in case there are multiple entries per day)
        history_dict = {}
        for row in result.data:
            date = row["date"]
            history_dict[date] = history_dict.get(date, 0) + row["requests_count"]

        # Convert to list
        history_list = [
            HistoryEntry(date=date, requests=count)
            for date, count in sorted(history_dict.items(), reverse=True)
        ]

        # Calculate totals
        total_requests = sum(h.requests for h in history_list)
        avg_per_day = round(total_requests / len(history_list), 2) if history_list else 0.0

        return UsageHistoryResponse(
            user_id=user.user_id[:8] + "...",
            days=days,
            total_requests=total_requests,
            avg_per_day=avg_per_day,
            history=history_list
        )

    except Exception as e:
        logger.error(f"[api] /usage/history failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch usage history: {str(e)}")

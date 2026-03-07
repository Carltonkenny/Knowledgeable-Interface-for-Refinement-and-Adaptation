# memory/profile_updater.py
# ─────────────────────────────────────────────
# Profile Updater — Background agent for profile evolution
#
# RULES.md Compliance:
# - Trigger: Every 5th interaction OR 30min inactivity
# - Background task (user NEVER waits)
# - Supabase RLS (user_id = auth.uid())
# - No hardcoded secrets (all from .env)
# - Type hints on all functions
# - Silent fail (safe to fail)
#
# Trigger Conditions:
# 1. Every 5th interaction in session
# 2. 30 minutes of inactivity
# 3. Explicit session end
# ─────────────────────────────────────────────

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from database import get_client, get_user_profile, save_user_profile
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ═══ CONFIGURATION ═══════════════════════════

# Trigger thresholds
INTERACTION_THRESHOLD = 5  # Update every 5th interaction
INACTIVITY_MINUTES = 30    # Update after 30min inactivity


# ═══ PROFILE UPDATER ═════════════════════════

def update_user_profile(
    user_id: str,
    session_data: Dict[str, Any],
    interaction_count: int,
    last_activity: Optional[datetime] = None
) -> bool:
    """
    Update user profile based on session analysis.
    
    RULES.md: Background task (user NEVER waits), silent fail
    
    Args:
        user_id: User UUID from JWT
        session_data: Current session result data
        interaction_count: Total interactions in session
        last_activity: Last activity timestamp
        
    Returns:
        True if successful, False otherwise (silent fail)
        
    Trigger Conditions:
    - interaction_count % 5 == 0 (every 5th interaction)
    - last_activity > 30 minutes ago
    - Explicit session end (not implemented here)
    """
    try:
        # ═══ CHECK TRIGGER CONDITIONS ═══
        should_update = False
        
        # Trigger 1: Every 5th interaction
        if interaction_count % INTERACTION_THRESHOLD == 0:
            logger.info(f"[profile] trigger: every {INTERACTION_THRESHOLD}th interaction ({interaction_count})")
            should_update = True
        
        # Trigger 2: 30 minutes inactivity
        if last_activity:
            # Use timezone-aware datetime
            now = datetime.now(timezone.utc)
            # Handle both timezone-aware and naive datetimes
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
            inactivity = now - last_activity
            if inactivity > timedelta(minutes=INACTIVITY_MINUTES):
                logger.info(f"[profile] trigger: {INACTIVITY_MINUTES}min inactivity")
                should_update = True
        
        if not should_update:
            return True  # No update needed, not an error
        
        # ═══ LOAD EXISTING PROFILE ═══
        existing_profile = get_user_profile(user_id) or {
            "dominant_domains": [],
            "prompt_quality_trend": "stable",
            "clarification_rate": 0.0,
            "preferred_tone": "direct",
            "notable_patterns": [],
            "total_sessions": 0,
        }
        
        # ═══ ANALYZE SESSION DATA ═══
        domain = session_data.get("domain_analysis", {}).get("primary_domain", "general")
        quality_score = session_data.get("quality_score", {})
        clarification_needed = session_data.get("pending_clarification", False)
        
        # Update dominant domains
        dominant_domains = existing_profile.get("dominant_domains", [])
        if domain and domain not in dominant_domains:
            dominant_domains.append(domain)
            # Keep only top 3
            dominant_domains = dominant_domains[-3:]
        
        # Update quality trend
        avg_quality = sum([
            quality_score.get("specificity", 3),
            quality_score.get("clarity", 3),
            quality_score.get("actionability", 3),
        ]) / 3
        
        if avg_quality >= 4.0:
            quality_trend = "improving"
        elif avg_quality >= 3.0:
            quality_trend = "stable"
        else:
            quality_trend = "declining"
        
        # Update clarification rate
        current_rate = existing_profile.get("clarification_rate", 0.0)
        if clarification_needed:
            current_rate = min(1.0, current_rate + 0.1)
        else:
            current_rate = max(0.0, current_rate - 0.05)
        
        # ═══ BUILD UPDATED PROFILE ═══
        updated_profile = {
            "dominant_domains": dominant_domains,
            "prompt_quality_trend": quality_trend,
            "clarification_rate": current_rate,
            "preferred_tone": existing_profile.get("preferred_tone", "direct"),
            "notable_patterns": existing_profile.get("notable_patterns", []),
            "total_sessions": existing_profile.get("total_sessions", 0) + 1,
        }
        
        # ═══ SAVE TO DATABASE ═══
        success = save_user_profile(user_id, updated_profile)
        
        if success:
            logger.info(f"[profile] updated for user {user_id[:8]}... domains={dominant_domains}")
        else:
            logger.warning(f"[profile] save failed for user {user_id[:8]}...")
        
        return success
        
    except Exception as e:
        # SILENT FAIL (RULES.md: background task, safe to fail)
        logger.error(f"[profile] update failed (non-blocking): {e}", exc_info=True)
        return False


# ═══ HELPER: CHECK IF UPDATE NEEDED ══════════

def should_trigger_update(
    interaction_count: int,
    last_activity: Optional[datetime] = None
) -> bool:
    """
    Check if profile update should be triggered.

    Call this at the end of each session to decide whether
    to add profile update to background tasks.

    Args:
        interaction_count: Total interactions in session
        last_activity: Last activity timestamp

    Returns:
        True if update should be triggered, False otherwise
    """
    # Trigger 1: Every 5th interaction
    if interaction_count % INTERACTION_THRESHOLD == 0:
        return True

    # Trigger 2: 30 minutes inactivity
    if last_activity:
        # Use timezone-aware datetime
        now = datetime.now(timezone.utc)
        # Handle both timezone-aware and naive datetimes
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)
        if now - last_activity > timedelta(minutes=INACTIVITY_MINUTES):
            return True

    return False

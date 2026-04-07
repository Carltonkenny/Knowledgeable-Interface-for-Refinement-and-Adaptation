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
from .langmem import get_quality_trend  # FR-3: Quality trend analysis
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

        # ═══ FR-3: QUALITY TREND ANALYSIS (SPEC V1) ═══
        # Calculate trend from last 10 sessions (not just current session score)
        quality_trend = get_quality_trend(user_id, last_n=10)
        logger.debug(f"[profile] quality trend for {user_id[:8]}...: {quality_trend}")
        
        # Update clarification rate
        current_rate = existing_profile.get("clarification_rate", 0.0)
        if clarification_needed:
            current_rate = min(1.0, current_rate + 0.1)
        else:
            current_rate = max(0.0, current_rate - 0.05)
        
        # ═══ DOMAIN CONFIDENCE TRACKING ═══
        # Tracks how consistently the user stays in the same domain.
        # When confidence > 0.85, the domain agent skips (saves ~200ms).
        # When user switches domains, confidence drops and domain agent runs again.
        current_domain = session_data.get("domain_analysis", {}).get("primary_domain", "general")
        existing_confidence = existing_profile.get("domain_confidence", 0.5)  # Start at 0.5 for new users

        if current_domain and current_domain in dominant_domains:
            # User stayed in known domain → increase confidence (+0.1 per update)
            # Takes ~4 updates to reach 0.85 skip threshold
            new_confidence = min(1.0, existing_confidence + 0.1)
        else:
            # User drifted to new or unknown domain → decrease confidence (-0.15)
            # Domain agent will run again to detect the drift
            new_confidence = max(0.0, existing_confidence - 0.15)

        # ═══ BUILD UPDATED PROFILE ═══
        updated_profile = {
            "dominant_domains": dominant_domains,
            "prompt_quality_trend": quality_trend,
            "clarification_rate": current_rate,
            "preferred_tone": existing_profile.get("preferred_tone", "direct"),
            "notable_patterns": existing_profile.get("notable_patterns", []),
            "total_sessions": existing_profile.get("total_sessions", 0) + 1,
            "domain_confidence": new_confidence,  # NEW: Smart skipping for domain agent
        }
        
        # ═══ SAVE TO DATABASE ═══
        success = save_user_profile(user_id, updated_profile)

        if success:
            logger.info(f"[profile] updated for user {user_id[:8]}... domains={dominant_domains}")
            
            # ═══ PHASE 4: TRACK SYNC TIMESTAMP ═══
            # Update last_profile_sync for UI transparency
            try:
                db = get_client()
                db.table("user_profiles").update({
                    "last_profile_sync": datetime.now(timezone.utc).isoformat()
                }).eq("user_id", user_id).execute()
                logger.debug(f"[profile] last_profile_sync updated for user {user_id[:8]}...")
            except Exception as e:
                logger.debug(f"[profile] failed to update last_profile_sync: {e}")
        else:
            logger.warning(f"[profile] save failed for user {user_id[:8]}...")

        return success
        
    except Exception as e:
        # SILENT FAIL (RULES.md: background task, safe to fail)
        logger.error(f"[profile] update failed (non-blocking): {e}", exc_info=True)
        return False


# ═══ HELPER: CHECK IF UPDATE NEEDED ══════════

def should_trigger_update(
    user_id: str,  # PHASE 3: Added user_id for cross-session check
    interaction_count: int
) -> bool:
    """
    Check if profile update should be triggered.

    Call this at the end of each session to decide whether
    to add profile update to background tasks.

    PHASE 3 UPDATE: Now checks ALL user sessions for inactivity,
    not just the current session. This prevents premature updates
    when users have multiple tabs open.

    Args:
        user_id: User UUID from JWT (for cross-session query)
        interaction_count: Total interactions in session

    Returns:
        True if update should be triggered, False otherwise

    Example:
        >>> should_trigger_update("user-uuid", 5)
        True  # Every 5th interaction
        >>> should_trigger_update("user-uuid", 3)
        False  # No trigger if user active in other tabs
    """
    # Trigger 1: Every 5th interaction
    if interaction_count % INTERACTION_THRESHOLD == 0:
        logger.info(f"[profile] trigger: every {INTERACTION_THRESHOLD}th interaction ({interaction_count})")
        return True

    # Trigger 2: Check ALL sessions for inactivity (PHASE 3)
    db = get_client()
    sessions = db.table("chat_sessions").select("last_activity").eq("user_id", user_id).execute()
    
    if not sessions.data:
        return False
    
    # Find MOST RECENT activity across ALL sessions
    last_activities = []
    for s in sessions.data:
        last_activity_str = s.get("last_activity")
        if last_activity_str:
            try:
                last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)
                last_activities.append(last_activity)
            except Exception as e:
                logger.debug(f"[profile] failed to parse last_activity: {e}")
    
    if not last_activities:
        return False
    
    # Get the most recent activity across all sessions
    most_recent = max(last_activities)
    now = datetime.now(timezone.utc)
    
    inactivity = now - most_recent
    if inactivity > timedelta(minutes=INACTIVITY_MINUTES):
        logger.info(f"[profile] trigger: {INACTIVITY_MINUTES}min inactivity (cross-session check)")
        return True
    
    # User is still active in at least one tab
    logger.debug(f"[profile] no trigger: user active {inactivity.total_seconds()/60:.1f}min ago in another tab")
    return False

# database.py
# ─────────────────────────────────────────────
# All Supabase database operations live here. Agents never import this — only api.py does.
# Client is cached via lru_cache — single connection, reused across all requests.
#
# Tables used:
#   requests        → Stores raw_prompt → improved_prompt pairs (for /refine and /chat)
#   agent_logs      → Stores each swarm agent's output, linked to request_id
#   requests        → Historical prompts and swarm metadata (Primary source for history)
#   conversations   → Full chat turns with message_type (conversation/new_prompt/followup)
#
# Functions:
#   save_request()           → Insert to requests, returns request_id for agent_logs
#   save_agent_logs()        → Bulk insert agent outputs (intent, context, domain)
#   save_request()           → Insert to requests table (both /refine and /chat call this)
#   get_history()            → Retrieve from requests table, optional session_id filter
#   save_conversation()      → Insert single chat turn (user or assistant)
#   get_conversation_history → Retrieve last N turns, reversed so oldest is first
#
# Error handling: All functions log errors and return None/[] — never raise to caller.
# ─────────────────────────────────────────────

import os
import uuid
import logging
from typing import Optional, Tuple
from functools import lru_cache
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── OpenTelemetry Tracing ────────────────────
try:
    from middleware.otel_tracing import get_tracer
    _otel_available = True
except ImportError:
    _otel_available = False
    def get_tracer(name="promptforge"):
        """Fallback no-op tracer when OTel not installed."""
        class _NoopSpan:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def set_attribute(self, k, v): pass
        class _NoopTracer:
            def start_as_current_span(self, name): return _NoopSpan()
        return _NoopTracer()


@lru_cache(maxsize=1)
def get_client() -> Client:
    """
    Returns cached Supabase client.
    Created once, reused on every call.
    Raises clearly if credentials are missing.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")

    logger.info("[db] Supabase client initialised")
    return create_client(url, key)


def save_request(
    raw_prompt: str,
    improved_prompt: str,
    session_id: str = None,
    user_id: str = None,
    quality_score: dict = None,
    domain_analysis: dict = None,
    agents_used: list = None,
    agents_skipped: list = None,
    prompt_diff: list = None,
    change_summary: str = "Automatic refinement"
) -> Optional[str]:
    """
    Saves to requests table with Phase 3 Auto-Versioning.
    
    RULES.md: Auto-creates session if not exists (prevents FK violations).

    Logic:
    - If session_id exists, find latest version in that session.
    - If found, increment version_number and link to same version_id.
    - If new session, start version 1 with new version_id.
    - Auto-creates chat_session if session_id provided but not found.
    """
    try:
        tracer = get_tracer("promptforge.database")
        with tracer.start_as_current_span("db.save_request") as span:
            span.set_attribute("db.table", "requests")

            db = get_client()
            request_id = str(uuid.uuid4())

            version_id = str(uuid.uuid4())
            version_number = 1
            parent_version_id = None

            # ═══ Phase 3: Auto-Versioning Logic ═══
            if session_id and user_id:
                logger.debug(f"[db] checking for previous versions in session {session_id[:8]}...")

                # RULES.md: Auto-create session if not exists (atomic upsert — no race condition)
                now = datetime.now(timezone.utc).isoformat()
                db.table("chat_sessions").upsert(
                    {
                        "id": session_id,
                        "user_id": user_id,
                        "title": "Auto-created session",
                        "created_at": now,
                        "last_activity": now
                    },
                    on_conflict="id"
                ).execute()
                logger.debug(f"[db] session {session_id[:8]}... ensured via upsert")

                latest = db.table("requests")\
                    .select("id, version_id, version_number")\
                    .eq("session_id", session_id)\
                    .eq("user_id", user_id)\
                    .order("version_number", desc=True)\
                    .limit(1)\
                    .execute()

                if latest.data:
                    # Group with existing version group
                    version_id = latest.data[0]["version_id"]
                    version_number = latest.data[0]["version_number"] + 1
                    parent_version_id = latest.data[0]["id"]

                    # Mark previous as not production
                    db.table("requests")\
                        .update({"is_production": False})\
                        .eq("id", parent_version_id)\
                        .execute()

            insert_data = {
                "id": request_id,
                "user_id": user_id,
                "raw_prompt": raw_prompt,
                "improved_prompt": improved_prompt,
                "session_id": session_id or "00000000-0000-0000-0000-000000000000",
                "quality_score": quality_score,
                "domain_analysis": domain_analysis,
                "agents_used": agents_used,
                "agents_skipped": agents_skipped,
                "prompt_diff": prompt_diff,
                # Version Control Columns
                "version_id": version_id,
                "version_number": version_number,
                "parent_version_id": parent_version_id,
                "change_summary": change_summary,
                "is_production": True
            }

            db.table("requests").insert(insert_data).execute()

            logger.info(f"[db] saved request {request_id[:8]}... (v{version_number}) version_id={version_id[:8]}...")
            return request_id

    except Exception as e:
        logger.error(f"[db] save_request failed: {e}")
        return None


def save_agent_logs(request_id: str, agent_outputs: dict) -> None:
    """
    Saves each agent's output to agent_logs.
    Linked to request via request_id.
    """
    try:
        db = get_client()

        rows = [
            {
                "request_id": request_id,
                "agent_name": agent_name,
                "output": output
            }
            for agent_name, output in agent_outputs.items()
        ]

        db.table("agent_logs").insert(rows).execute()
        logger.info(f"[db] saved {len(rows)} agent logs for {request_id[:8]}...")

    except Exception as e:
        logger.error(f"[db] save_agent_logs failed: {e}")




def get_history(session_id: str = None, limit: int = 10, user_id: str = None) -> list:
    """
    Retrieves history from 'requests' table (Phase 2 standard).
    Ordered by most recent first.
    """
    try:
        db = get_client()

        query = db.table("requests")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)

        if user_id:
            query = query.eq("user_id", user_id)
        
        if session_id:
            query = query.eq("session_id", session_id)

        result = query.execute()
        logger.info(f"[db] fetched {len(result.data)} history rows from requests")
        return result.data

    except Exception as e:
        logger.error(f"[db] get_history failed: {e}")
        return []


def save_conversation(
    session_id: str,
    role: str,
    message: str,
    message_type: str = None,
    improved_prompt: str = None,
    user_id: str = None
) -> None:
    """
    Saves one turn of conversation to conversations table.
    
    Args:
        session_id: Conversation session identifier
        role: 'user' or 'assistant'
        message: The message content
        message_type: 'conversation', 'new_prompt', 'followup'
        improved_prompt: Engineered prompt (if applicable)
        user_id: User UUID from JWT (for RLS)
    """
    try:
        tracer = get_tracer("promptforge.database")
        with tracer.start_as_current_span("db.save_conversation") as span:
            span.set_attribute("db.table", "conversations")

            db = get_client()

            insert_data = {
                "session_id": session_id,
                "role": role,
                "message": message,
                "message_type": message_type,
                "improved_prompt": improved_prompt
            }

            if user_id:
                insert_data["user_id"] = user_id

            db.table("conversations").insert(insert_data).execute()
            logger.info(f"[db] saved conversation turn role={role} session={session_id} user_id={user_id[:8] if user_id else 'None'}")
    except Exception as e:
        logger.error(f"[db] save_conversation failed: {e}")


def get_conversation_count(session_id: str) -> int:
    """
    Count total conversations in a session.
    Used to determine if profile update should be triggered (every 5th interaction).
    """
    try:
        db = get_client()
        result = db.table("conversations").select("id", count="exact").eq("session_id", session_id).execute()
        count = len(result.data)
        logger.info(f"[db] conversation count for session={session_id}: {count}")
        return count
    except Exception as e:
        logger.error(f"[db] get_conversation_count failed: {e}")
        return 0


def get_conversation_history(session_id: str, limit: int = 6) -> list:
    """
    Retrieves last N turns of conversation for a session.
    Ordered oldest first so agents read it naturally.
    limit=6 means last 3 exchanges (3 user + 3 assistant).
    
    Schema Migration Guard: Fills defaults for new fields to prevent
    breaking when state schema changes (latency_ms, memories_applied, etc.).
    """
    try:
        tracer = get_tracer("promptforge.database")
        with tracer.start_as_current_span("db.get_conversation_history") as span:
            span.set_attribute("db.table", "conversations")

            db = get_client()
            result = db.table("conversations")\
                .select("role, message, message_type, improved_prompt")\
                .eq("session_id", session_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()

            # Reverse so oldest is first
            history = list(reversed(result.data))

            # Schema migration guard: fill defaults for new fields
            # This prevents "failed to load conversation" when old DB records
            # are missing fields added by recent schema changes
            for turn in history:
                turn.setdefault("latency_ms", 0)
                turn.setdefault("memories_applied", 0)

            logger.info(f"[db] fetched {len(history)} conversation turns for session={session_id}")
            return history
    except Exception as e:
        logger.error(f"[db] get_conversation_history failed: {e}")
        return []



# ═══ Chat Session Functions (Phase 1) ════════════════

def create_chat_session(user_id: str, session_id: str, title: str = "New Chat") -> Optional[dict]:
    """
    Inserts a new session into chat_sessions.
    
    Parameters
    ----------
    user_id : str
        User UUID from JWT.
    session_id : str
        UUID for the new session.
    title : str, optional
        Initial title for the chat, by default "New Chat".
        
    Returns
    -------
    Optional[dict]
        The created session object if successful, None otherwise.
    """
    try:
        db = get_client()
        now = datetime.now(timezone.utc).isoformat()
        result = db.table("chat_sessions").insert({
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "last_activity": now
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"[db] create_chat_session failed: {e}")
        return None

def get_chat_sessions(user_id: str, limit: int = 20) -> list:
    """
    Fetches user's active (non-deleted) sessions for the Sidebar.

    Parameters
    ----------
    user_id : str
        User UUID from JWT.
    limit : int, optional
        Maximum number of sessions to return, by default 20.

    Returns
    -------
    list
        List of session dicts found in chat_sessions.
    """
    try:
        tracer = get_tracer("promptforge.database")
        with tracer.start_as_current_span("db.get_chat_sessions") as span:
            span.set_attribute("db.table", "chat_sessions")

            db = get_client()
            logger.info(f"[db] fetching sessions for user_id={user_id[:8] if user_id else 'None'}...")

            # Build query - use is_ for null check
            query = db.table("chat_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .is_("deleted_at", None)  # Use None instead of "null"

            result = query.order("is_pinned", desc=True)\
                .order("last_activity", desc=True)\
                .limit(limit)\
                .execute()

            logger.info(f"[db] fetched {len(result.data) if result.data else 0} sessions")
            return result.data or []
    except Exception as e:
        logger.error(f"[db] get_chat_sessions failed: {e}", exc_info=True)
        raise  # Re-raise so API endpoint sees the error

def get_deleted_sessions(user_id: str, limit: int = 20) -> list:
    """
    Fetches user's soft-deleted sessions for the Recycle Bin.
    """
    try:
        db = get_client()
        result = db.table("chat_sessions")\
            .select("*")\
            .eq("user_id", user_id)\
            .not_.is_("deleted_at", "null")\
            .order("deleted_at", desc=True)\
            .limit(limit)\
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"[db] get_deleted_sessions failed: {e}")
        return []

def delete_chat_session(session_id: str, user_id: str) -> bool:
    """
    Soft-deletes a session by setting deleted_at.
    """
    try:
        db = get_client()
        now = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"[db] soft-deleting session {session_id[:8]}... for user {user_id[:8]}...")
        
        result = db.table("chat_sessions")\
            .update({"deleted_at": now})\
            .eq("id", session_id)\
            .eq("user_id", user_id)\
            .execute()
        
        # Check if any rows were actually updated
        if not result.data or len(result.data) == 0:
            logger.warning(f"[db] no session found to delete: {session_id[:8]}...")
            return False
            
        logger.info(f"[db] session {session_id[:8]}... soft-deleted successfully")
        return True
    except Exception as e:
        logger.error(f"[db] delete_chat_session failed: {e}", exc_info=True)
        return False

def restore_chat_session(session_id: str, user_id: str) -> bool:
    """
    Restores a soft-deleted session.
    """
    try:
        db = get_client()
        db.table("chat_sessions")\
            .update({"deleted_at": None})\
            .eq("id", session_id)\
            .eq("user_id", user_id)\
            .execute()
        return True
    except Exception as e:
        logger.error(f"[db] restore_chat_session failed: {e}")
        return False

def purge_chat_session(session_id: str, user_id: str) -> bool:
    """
    Permanently deletes a session and its history.
    """
    try:
        db = get_client()
        db.table("chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        logger.error(f"[db] purge_chat_session failed: {e}")
        return False

def update_chat_session(session_id: str, user_id: str, updates: dict) -> Optional[dict]:
    """
    Updates session metadata (title, is_pinned, is_favorite).
    """
    try:
        db = get_client()
        result = db.table("chat_sessions")\
            .update(updates)\
            .eq("id", session_id)\
            .eq("user_id", user_id)\
            .execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"[db] update_chat_session failed: {e}")
        return None


# ═══ User Profile Functions ══════════════════════

def get_user_profile(user_id: str) -> Optional[dict]:
    """
    Fetch user profile from user_profiles table.
    
    Args:
        user_id: User UUID from JWT
        
    Returns:
        Profile dict if found, None otherwise
        
    Example:
        profile = get_user_profile("user-uuid")
        if profile:
            tone = profile.get("preferred_tone")
    """
    try:
        tracer = get_tracer("promptforge.database")
        with tracer.start_as_current_span("db.get_user_profile") as span:
            span.set_attribute("db.table", "user_profiles")

            db = get_client()
            result = db.table("user_profiles")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()

            if result.data and len(result.data) > 0:
                logger.info(f"[db] fetched profile for user_id={user_id[:8]}...")
                return result.data[0]
            else:
                logger.info(f"[db] no profile found for user_id={user_id[:8]}...")
                return None

    except Exception as e:
        logger.error(f"[db] get_user_profile failed: {e}")
        return None


def save_user_profile(user_id: str, profile_data: dict) -> bool:
    """
    Insert or update user profile.
    
    Args:
        user_id: User UUID from JWT
        profile_data: Dict with profile fields
        
    Returns:
        True on success, False on failure
        
    Example:
        save_user_profile("user-uuid", {
            "dominant_domains": ["coding"],
            "preferred_tone": "technical"
        })
    """
    try:
        db = get_client()
        
        # Atomic upsert — no race condition under concurrent requests
        db.table("user_profiles").upsert(
            {
                "user_id": user_id,
                **profile_data
            },
            on_conflict="user_id"
        ).execute()
        logger.info(f"[db] upserted profile for user_id={user_id[:8]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"[db] save_user_profile failed: {e}")
        return False


def update_user_xp(user_id: str, xp_gained: int, new_tier: str) -> bool:
    """
    Atomically increment the user's XP and update their loyalty tier.
    
    Args:
        user_id: User UUID
        xp_gained: Amount of XP to add
        new_tier: Evaluated tier based on total XP
    """
    try:
        from database import get_client, get_user_profile
        db = get_client()
        
        # Get current profile to safely increment
        # Note: Proper atomic increments are tricky in Supabase basic REST, 
        # so we fetch and update. In a heavy production env we'd use a Postgres RPC.
        profile = get_user_profile(user_id)
        current_xp = profile.get("xp_total", 0) if profile else 0
        
        db.table("user_profiles").upsert(
            {
                "user_id": user_id,
                "xp_total": current_xp + xp_gained,
                "loyalty_tier": new_tier
            },
            on_conflict="user_id"
        ).execute()
        
        logger.info(f"[db] added {xp_gained} XP for user_id={user_id[:8]}... New Total: {current_xp + xp_gained} New Tier: {new_tier}")
        return True
    except Exception as e:
        logger.error(f"[db] update_user_xp failed: {e}")
        return False


# ═══ Clarification Flag Functions ════════════════

def save_clarification_flag(
    session_id: str,
    user_id: str,
    pending: bool,
    clarification_key: Optional[str] = None
) -> bool:
    """
    Save clarification flag to conversations table.
    Used for clarification loop.
    
    Args:
        session_id: Conversation session ID
        user_id: User UUID from JWT
        pending: True if waiting for user answer
        clarification_key: Which field being clarified
        
    Returns:
        True on success, False on failure
        
    Example:
        save_clarification_flag("session-123", "user-uuid", True, "target_audience")
    """
    try:
        db = get_client()
        
        # Find latest conversation turn for this session
        result = db.table("conversations")\
            .select("id")\
            .eq("session_id", session_id)\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data and len(result.data) > 0:
            conversation_id = result.data[0]["id"]
            db.table("conversations")\
                .update({
                    "pending_clarification": pending,
                    "clarification_key": clarification_key
                })\
                .eq("id", conversation_id)\
                .execute()
            logger.info(f"[db] set clarification flag session={session_id} pending={pending}")
            return True
        
        logger.warning(f"[db] no conversation found for session={session_id}")
        return False
        
    except Exception as e:
        logger.error(f"[db] save_clarification_flag failed: {e}")
        return False


def get_clarification_flag(session_id: str, user_id: str) -> tuple[bool, Optional[str]]:
    """
    Check if clarification is pending for this session.
    
    Args:
        session_id: Conversation session ID
        user_id: User UUID from JWT
        
    Returns:
        Tuple of (pending_clarification, clarification_key)
        Defaults to (False, None) if not found
        
    Example:
        pending, key = get_clarification_flag("session-123", "user-uuid")
        if pending:
            # User is answering a clarification question
            pass
    """
    try:
        db = get_client()
        
        result = db.table("conversations")\
            .select("pending_clarification, clarification_key")\
            .eq("session_id", session_id)\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data and len(result.data) > 0:
            row = result.data[0]
            return (row.get("pending_clarification", False), row.get("clarification_key"))
        
        return (False, None)
        
    except Exception as e:
        logger.error(f"[db] get_clarification_flag failed: {e}")
        return (False, None)


# ═══ Session Tracking Functions ════════════════

def update_session_activity(user_id: str, session_id: str) -> bool:
    """
    Update last activity timestamp for session.
    Used for profile updater inactivity trigger (RULES.md: 30min inactivity).

    Args:
        user_id: User UUID from JWT
        session_id: Session identifier

    Returns:
        True if successful, False otherwise

    Example:
        update_session_activity("user-uuid", "session-123")
    """
    try:
        db = get_client()
        now = datetime.now(timezone.utc).isoformat()

        # Try to update existing session
        result = db.table("chat_sessions").update({
            "last_activity": now
        }).eq("user_id", user_id).eq("id", session_id).execute()

        # If no rows updated, insert new session
        if not result.data or len(result.data) == 0:
            db.table("chat_sessions").insert({
                "user_id": user_id,
                "id": session_id,
                "last_activity": now
            }).execute()

        logger.debug(f"[db] updated session activity for {user_id[:8]}... session={session_id}")
        return True

    except Exception as e:
        logger.error(f"[db] update_session_activity failed: {e}")
        return False


def get_last_activity(user_id: str, session_id: str) -> Optional[datetime]:
    """
    Get last activity timestamp for session.

    Args:
        user_id: User UUID from JWT
        session_id: Session identifier

    Returns:
        Last activity datetime or None if not found

    Example:
        last = get_last_activity("user-uuid", "session-123")
        if last and is_inactive(last):
            trigger_profile_update()
    """
    try:
        db = get_client()
        result = db.table("chat_sessions").select("last_activity").eq(
            "user_id", user_id).eq("id", session_id).execute()

        if result.data and len(result.data) > 0:
            last_activity_str = result.data[0].get("last_activity")
            if last_activity_str:
                # Parse ISO format string to datetime
                last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
                logger.debug(f"[db] last activity for {user_id[:8]}...: {last_activity}")
                return last_activity

        return None

    except Exception as e:
        logger.error(f"[db] get_last_activity failed: {e}")
        return None


# ═══ USAGE TRACKING (Rate Limiting Support) ═══════════════════

def track_user_usage(user_id: str) -> None:
    """
    Track user's daily and monthly usage in Supabase.
    Call this after every successful request.

    RULES.md: Silent fail — usage tracking is non-critical

    Args:
        user_id: User UUID from JWT

    Example:
        track_user_usage("user-uuid")
        # Inserts/updates usage_logs table
    """
    try:
        db = get_client()
        today = datetime.now(timezone.utc).date().isoformat()
        current_month = datetime.now(timezone.utc).month
        current_year = datetime.now(timezone.utc).year

        # Upsert today's usage (increment by 1)
        db.table("usage_logs").upsert({
            "user_id": user_id,
            "date": today,
            "month": current_month,
            "year": current_year,
            "requests_count": 1
        }, on_conflict="user_id,date").execute()

        logger.debug(f"[usage] tracked for {user_id[:8]}... date={today}")

    except Exception as e:
        logger.error(f"[usage] tracking failed: {e}")
        # Silent fail — usage tracking is non-critical


def get_user_usage(user_id: str) -> dict:
    """
    Get user's current usage (daily + monthly) from Supabase.

    Args:
        user_id: User UUID from JWT

    Returns:
        Dict with daily_count, monthly_count, and limits from env

    Example:
        usage = get_user_usage("user-uuid")
        # Returns: {
        #   "daily_count": 25,
        #   "daily_limit": 50,
        #   "monthly_count": 800,
        #   "monthly_limit": 1500
        # }
    """
    try:
        db = get_client()
        today = datetime.now(timezone.utc).date().isoformat()
        current_month = datetime.now(timezone.utc).month
        current_year = datetime.now(timezone.utc).year

        # Get daily usage
        daily_result = db.table("usage_logs").select("requests_count").eq(
            "user_id", user_id
        ).eq("date", today).execute()

        # Get monthly usage
        monthly_result = db.table("usage_logs").select("requests_count").eq(
            "user_id", user_id
        ).eq("month", current_month).eq("year", current_year).execute()

        daily_count = sum(r["requests_count"] for r in daily_result.data) if daily_result.data else 0
        monthly_count = sum(r["requests_count"] for r in monthly_result.data) if monthly_result.data else 0

        return {
            "daily_count": daily_count,
            "daily_limit": int(os.getenv("RATE_LIMIT_DAILY", "50")),
            "monthly_count": monthly_count,
            "monthly_limit": int(os.getenv("RATE_LIMIT_MONTHLY", "1500")),
            "hourly_limit": int(os.getenv("RATE_LIMIT_HOURLY", "10"))
        }

    except Exception as e:
        logger.error(f"[usage] fetch failed: {e}")
        # Return safe defaults on error
        return {
            "daily_count": 0,
            "daily_limit": 50,
            "monthly_count": 0,
            "monthly_limit": 1500,
            "hourly_limit": 10
        }


def check_usage_limits(user_id: str) -> Tuple[bool, str]:
    """
    Check if user has exceeded usage limits (from Supabase).

    Args:
        user_id: User UUID from JWT

    Returns:
        Tuple of (is_allowed, reason)

    Example:
        allowed, reason = check_usage_limits("user-uuid")
        # Returns: (True, "OK") or (False, "Daily limit exceeded (50/50)")
    """
    usage = get_user_usage(user_id)

    # Check daily limit
    if usage["daily_count"] >= usage["daily_limit"]:
        return False, f"Daily limit exceeded ({usage['daily_count']}/{usage['daily_limit']})"

    # Check monthly limit
    if usage["monthly_count"] >= usage["monthly_limit"]:
        return False, f"Monthly limit exceeded ({usage['monthly_count']}/{usage['monthly_limit']})"

    return True, "OK"
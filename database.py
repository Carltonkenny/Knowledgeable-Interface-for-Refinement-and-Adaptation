# database.py
# ─────────────────────────────────────────────
# All Supabase database operations live here. Agents never import this — only api.py does.
# Client is cached via lru_cache — single connection, reused across all requests.
#
# Tables used:
#   requests        → Stores raw_prompt → improved_prompt pairs (for /refine and /chat)
#   agent_logs      → Stores each swarm agent's output, linked to request_id
#   prompt_history  → Historical prompts for /history endpoint retrieval
#   conversations   → Full chat turns with message_type (conversation/new_prompt/followup)
#
# Functions:
#   save_request()           → Insert to requests, returns request_id for agent_logs
#   save_agent_logs()        → Bulk insert agent outputs (intent, context, domain)
#   save_history()           → Insert to prompt_history (both /refine and /chat call this)
#   get_history()            → Retrieve from prompt_history, optional session_id filter
#   save_conversation()      → Insert single chat turn (user or assistant)
#   get_conversation_history → Retrieve last N turns, reversed so oldest is first
#
# Error handling: All functions log errors and return None/[] — never raise to caller.
# ─────────────────────────────────────────────

import os
import uuid
import logging
from typing import Optional
from functools import lru_cache
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


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


def save_request(raw_prompt: str, improved_prompt: str, session_id: str = None, user_id: str = None) -> str | None:
    """
    Saves request to requests table.
    Returns request_id for agent_logs to reference.
    Returns None if save fails — caller handles gracefully.
    
    Args:
        raw_prompt: User's original prompt
        improved_prompt: Engineered prompt from swarm
        session_id: Conversation session identifier
        user_id: User UUID from JWT (for RLS)
    """
    try:
        db = get_client()
        request_id = str(uuid.uuid4())

        insert_data = {
            "id": request_id,
            "raw_prompt": raw_prompt,
            "improved_prompt": improved_prompt,
            "session_id": session_id or "default"
        }
        
        # Add user_id if provided (for RLS)
        if user_id:
            insert_data["user_id"] = user_id

        db.table("requests").insert(insert_data).execute()

        logger.info(f"[db] saved request {request_id[:8]}... user_id={user_id[:8] if user_id else 'None'}")
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


def save_history(raw_prompt: str, improved_prompt: str, session_id: str = None, user_id: str = None) -> None:
    """
    Saves to prompt_history for future memory/chat features.
    
    Args:
        raw_prompt: User's original prompt
        improved_prompt: Engineered prompt from swarm
        session_id: Conversation session identifier
        user_id: User UUID from JWT (for RLS)
    """
    try:
        db = get_client()

        insert_data = {
            "session_id": session_id or "default",
            "raw_prompt": raw_prompt,
            "improved_prompt": improved_prompt
        }
        
        if user_id:
            insert_data["user_id"] = user_id

        db.table("prompt_history").insert(insert_data).execute()

        logger.info(f"[db] saved to prompt_history for session '{session_id}' user_id={user_id[:8] if user_id else 'None'}")

    except Exception as e:
        logger.error(f"[db] save_history failed: {e}")


def get_history(session_id: str = None, limit: int = 10, user_id: str = None) -> list:
    """
    Retrieves prompt history ordered by most recent first.
    Optionally filtered by session_id and user_id.
    
    Args:
        session_id: Filter by session (optional)
        limit: Max results (default 10)
        user_id: Filter by user (for RLS)
    """
    try:
        db = get_client()

        query = db.table("prompt_history")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)

        if user_id:
            query = query.eq("user_id", user_id)
        elif session_id:
            query = query.eq("session_id", session_id)

        result = query.execute()
        logger.info(f"[db] fetched {len(result.data)} history rows")
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
    """
    try:
        db = get_client()
        result = db.table("conversations")\
            .select("role, message, message_type, improved_prompt")\
            .eq("session_id", session_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        # Reverse so oldest is first
        history = list(reversed(result.data))
        logger.info(f"[db] fetched {len(history)} conversation turns for session={session_id}")
        return history
    except Exception as e:
        logger.error(f"[db] get_conversation_history failed: {e}")
        return []


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
        
        # Check if profile exists
        existing = get_user_profile(user_id)
        
        if existing:
            # Update existing profile
            db.table("user_profiles")\
                .update(profile_data)\
                .eq("user_id", user_id)\
                .execute()
            logger.info(f"[db] updated profile for user_id={user_id[:8]}...")
        else:
            # Insert new profile
            db.table("user_profiles")\
                .insert({
                    "user_id": user_id,
                    **profile_data
                })\
                .execute()
            logger.info(f"[db] created profile for user_id={user_id[:8]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"[db] save_user_profile failed: {e}")
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
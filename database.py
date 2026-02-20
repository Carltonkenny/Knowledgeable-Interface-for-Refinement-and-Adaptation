# database.py
# ─────────────────────────────────────────────
# All Supabase logic lives here.
# Agents never import this — only api.py does.
#
# 3 operations:
#   1. save_request()   → saves prompt in/out to requests table
#   2. save_agent_logs()→ saves each agent's output to agent_logs
#   3. save_history()   → saves to prompt_history for future memory
# ─────────────────────────────────────────────

# database.py
# ─────────────────────────────────────────────
# All Supabase logic lives here.
# Client is cached — one connection, reused everywhere.
# All failures are logged, never silent.
# Agents never import this — only api.py does.
# ─────────────────────────────────────────────

import os
import uuid
import logging
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


def save_request(raw_prompt: str, improved_prompt: str, session_id: str = None) -> str | None:
    """
    Saves request to requests table.
    Returns request_id for agent_logs to reference.
    Returns None if save fails — caller handles gracefully.
    """
    try:
        db = get_client()
        request_id = str(uuid.uuid4())

        db.table("requests").insert({
            "id": request_id,
            "raw_prompt": raw_prompt,
            "improved_prompt": improved_prompt,
            "session_id": session_id or "default"
        }).execute()

        logger.info(f"[db] saved request {request_id[:8]}...")
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


def save_history(raw_prompt: str, improved_prompt: str, session_id: str = None) -> None:
    """
    Saves to prompt_history for future memory/chat features.
    """
    try:
        db = get_client()

        db.table("prompt_history").insert({
            "session_id": session_id or "default",
            "raw_prompt": raw_prompt,
            "improved_prompt": improved_prompt
        }).execute()

        logger.info(f"[db] saved to prompt_history for session '{session_id}'")

    except Exception as e:
        logger.error(f"[db] save_history failed: {e}")


def get_history(session_id: str = None, limit: int = 10) -> list:
    """
    Retrieves prompt history ordered by most recent first.
    Optionally filtered by session_id.
    """
    try:
        db = get_client()

        query = db.table("prompt_history")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)

        if session_id:
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
    improved_prompt: str = None
) -> None:
    """
    Saves one turn of conversation to conversations table.
    role = 'user' or 'assistant'
    message_type = 'conversation', 'new_prompt', 'followup'
    """
    try:
        db = get_client()
        db.table("conversations").insert({
            "session_id": session_id,
            "role": role,
            "message": message,
            "message_type": message_type,
            "improved_prompt": improved_prompt
        }).execute()
        logger.info(f"[db] saved conversation turn role={role} session={session_id}")
    except Exception as e:
        logger.error(f"[db] save_conversation failed: {e}")


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
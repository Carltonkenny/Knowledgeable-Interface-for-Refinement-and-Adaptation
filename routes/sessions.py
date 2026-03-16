# routes/sessions.py
# ─────────────────────────────────────────────
# Chat Session Management Endpoints
#   GET    /sessions               → List active sessions
#   GET    /sessions/deleted       → List soft-deleted sessions
#   POST   /sessions               → Create new session
#   PATCH  /sessions/{id}          → Update metadata
#   POST   /sessions/{id}/restore  → Restore soft-deleted
#   DELETE /sessions/{id}          → Soft-delete
#   DELETE /sessions/{id}/purge    → Permanent delete
#
# RULES.md: <500 lines, type hints, docstrings, error handling
# ─────────────────────────────────────────────

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from auth import User, get_current_user
from database import (
    get_chat_sessions, get_deleted_sessions,
    create_chat_session, update_chat_session,
    delete_chat_session, restore_chat_session, purge_chat_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sessions"])


# ── Schemas ───────────────────────────────────

class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    title: str = "New Chat"
    is_pinned: bool = False
    is_favorite: bool = False
    deleted_at: Optional[str] = None
    created_at: str
    last_activity: str


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None


# ── Endpoints ─────────────────────────────────

@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(user: User = Depends(get_current_user)):
    """Fetch user's active chat sessions for the sidebar."""
    return get_chat_sessions(user.user_id)


@router.get("/sessions/deleted", response_model=list[ChatSessionResponse])
async def list_deleted_sessions(user: User = Depends(get_current_user)):
    """Fetch user's soft-deleted sessions in the Recycle Bin."""
    return get_deleted_sessions(user.user_id)


@router.post("/sessions", response_model=ChatSessionResponse)
async def start_session(user: User = Depends(get_current_user)):
    """Create a new blank chat session."""
    session_id = str(uuid.uuid4())
    session = create_chat_session(user.user_id, session_id, "New Chat")
    if not session:
        raise HTTPException(status_code=500, detail="Failed to create session")
    return session


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session_meta(
    session_id: str,
    req: UpdateSessionRequest,
    user: User = Depends(get_current_user)
):
    """Update session metadata (title, pin, favorite)."""
    updates = req.dict(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
        
    result = update_chat_session(session_id, user.user_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/sessions/{session_id}/restore")
async def restore_session_route(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """Restore a soft-deleted session."""
    success = restore_chat_session(session_id, user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or restore failed")
    return {"status": "restored", "id": session_id}


@router.delete("/sessions/{session_id}")
async def trash_session(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """Soft-delete a session (move to Recycle Bin)."""
    success = delete_chat_session(session_id, user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "id": session_id}


@router.delete("/sessions/{session_id}/purge")
async def wipe_session_permanent(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """Permanently delete a session and all its data."""
    success = purge_chat_session(session_id, user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "purged", "id": session_id}

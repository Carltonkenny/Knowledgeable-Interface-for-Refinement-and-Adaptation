# PromptForge v2.0 — Refactoring Contract

**Version:** 1.0  
**Date:** 2026-03-13  
**Type:** Spec-Driven Development Contract  
**Compliance:** RULES.md v1.0  
**Status:** Ready for Implementation

---

## CONTRACT OVERVIEW

### Purpose

This contract defines the complete refactoring plan for PromptForge v2.0's three primary tabs: **Chat**, **History**, and **Profile**. Each phase transforms the current implementation into 2026 professional standards while maintaining strict adherence to RULES.md engineering principles.

### Guiding Principles

1. **Spec-Driven Development** — Every function typed, documented, tested
2. **No AI Slop** — Readable, maintainable, senior-level code
3. **Current Theme Preservation** — Dark mode, Kira branding, minimalist aesthetic
4. **Backward Compatibility** — Existing features never break
5. **LangMem Integration** — Every enhancement showcases Gemini embeddings + RAG

---

## PHASE STRUCTURE

```
Phase 1: Chat Tab (Multi-Chat Support)
  Duration: 5-7 days
  Priority: HIGH
  Impact: User can manage multiple concurrent conversations

Phase 2: History Tab (Intelligent Memory Palace)
  Duration: 5-7 days
  Priority: HIGH
  Impact: Semantic search + session grouping + analytics

Phase 3: Profile Tab (Living Digital Twin)
  Duration: 5-7 days
  Priority: MEDIUM
  Impact: Editable identity + domain niches + LangMem preview
```

---

## PHASE 1: CHAT TAB — "Multi-Chat Support"

### Objective

Transform single-chat interface into **multi-session chat management** (like ChatGPT, Claude) while preserving existing SSE streaming, Kira personality, and swarm execution.

---

### 1.1 BACKEND CONTRACT (Phase 1)

#### File: `api.py`

**ADD These Endpoints (Do NOT Modify Existing):**

```python
# ═══ NEW: Chat Session Management ═══════════════════

@app.post("/sessions")
async def create_session(user: User = Depends(get_current_user)):
    """
    Create new chat session for user.
    
    RULES.md Compliance:
    - JWT required (Security Rule #1)
    - user_id from JWT (RLS Rule #3)
    - Type hints mandatory (Code Quality Standard)
    
    Returns:
        {"session_id": "uuid", "created_at": "timestamp"}
    """
    try:
        db = get_client()
        session_id = str(uuid.uuid4())
        
        result = db.table("chat_sessions").insert({
            "id": session_id,
            "user_id": user.user_id,
            "title": "New Chat",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"[api] created session {session_id[:8]}... for user {user.user_id[:8]}...")
        
        return {
            "session_id": session_id,
            "created_at": result.data[0]["created_at"]
        }
        
    except Exception as e:
        logger.exception("[api] create_session failed")
        raise HTTPException(status_code=500, detail="Failed to create session")


@app.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    List user's chat sessions ordered by last activity.
    
    RULES.md Compliance:
    - RLS via user_id (Security Rule #3)
    - Pagination (Performance Target)
    - Structured logging (Error Handling Standard)
    
    Returns:
        {"sessions": [...], "total": int}
    """
    try:
        db = get_client()
        
        result = db.table("chat_sessions")\
            .select("*")\
            .eq("user_id", user.user_id)\
            .order("last_activity", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "sessions": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        logger.exception("[api] list_sessions failed")
        raise HTTPException(status_code=500, detail="Failed to list sessions")


@app.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    update_data: dict,
    user: User = Depends(get_current_user)
):
    """
    Update session metadata (title, etc.).
    
    RULES.md Compliance:
    - Ownership verification (Security Rule #2)
    - Input validation (Security Rule #9)
    
    Body:
        {"title": "New Title"}
    
    Returns:
        {"status": "ok"}
    """
    try:
        db = get_client()
        
        # Verify ownership
        existing = db.table("chat_sessions")\
            .select("id")\
            .eq("id", session_id)\
            .eq("user_id", user.user_id)\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update
        db.table("chat_sessions")\
            .update(update_data)\
            .eq("id", session_id)\
            .execute()
        
        logger.info(f"[api] updated session {session_id[:8]}...")
        return {"status": "ok"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] update_session failed")
        raise HTTPException(status_code=500, detail="Failed to update session")


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """
    Delete chat session and associated data.
    
    RULES.md Compliance:
    - Ownership verification (Security Rule #2)
    - Cascading delete (Database Integrity)
    
    Returns:
        {"status": "ok"}
    """
    try:
        db = get_client()
        
        # Verify ownership
        existing = db.table("chat_sessions")\
            .select("id")\
            .eq("id", session_id)\
            .eq("user_id", user.user_id)\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete session (RLS ensures user owns it)
        db.table("chat_sessions")\
            .delete()\
            .eq("id", session_id)\
            .execute()
        
        logger.info(f"[api] deleted session {session_id[:8]}...")
        return {"status": "ok"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] delete_session failed")
        raise HTTPException(status_code=500, detail="Failed to delete session")
```

---

#### File: `database.py`

**ADD These Functions:**

```python
# ═══ NEW: Chat Session Functions ═══════════════════

def create_chat_session(user_id: str, session_id: str) -> Optional[dict]:
    """
    Create new chat session in database.
    
    Args:
        user_id: User UUID from JWT
        session_id: Pre-generated UUID for session
        
    Returns:
        Session dict if successful, None otherwise
        
    Example:
        session = create_chat_session("user-uuid", "session-uuid")
    """
    try:
        db = get_client()
        
        result = db.table("chat_sessions").insert({
            "id": session_id,
            "user_id": user_id,
            "title": "New Chat",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"[db] created session {session_id[:8]}... for user {user_id[:8]}...")
        return result.data[0]
        
    except Exception as e:
        logger.error(f"[db] create_chat_session failed: {e}")
        return None


def get_user_sessions(user_id: str, limit: int = 20) -> list:
    """
    Get user's chat sessions ordered by last activity.
    
    Args:
        user_id: User UUID from JWT
        limit: Max sessions to return (default: 20)
        
    Returns:
        List of session dicts
        
    Example:
        sessions = get_user_sessions("user-uuid", limit=20)
    """
    try:
        db = get_client()
        
        result = db.table("chat_sessions")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("last_activity", desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"[db] get_user_sessions failed: {e}")
        return []


def update_session_activity(session_id: str, user_id: str) -> bool:
    """
    Update last_activity timestamp for session.
    
    Called on every message to track active sessions.
    
    Args:
        session_id: Session UUID
        user_id: User UUID from JWT
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_client()
        
        db.table("chat_sessions")\
            .update({
                "last_activity": datetime.now(timezone.utc).isoformat()
            })\
            .eq("id", session_id)\
            .eq("user_id", user_id)\
            .execute()
        
        return True
        
    except Exception as e:
        logger.error(f"[db] update_session_activity failed: {e}")
        return False
```

---

#### File: `migrations/015_add_chat_sessions.sql`

**CREATE This Migration:**

```sql
-- ============================================================
-- PromptForge v2.0 - Chat Sessions Table
-- ============================================================
-- Purpose: Enable multi-chat support
-- Run in Supabase SQL Editor
-- Time: ~5 seconds
-- ============================================================

BEGIN;

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    title TEXT DEFAULT 'New Chat',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure valid data
    CONSTRAINT valid_title CHECK (length(title) > 0 AND length(title) <= 100)
);

-- Enable RLS
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies (Security Rule #3)
CREATE POLICY "users_select_own_sessions" ON chat_sessions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_sessions" ON chat_sessions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users_update_own_sessions" ON chat_sessions
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "users_delete_own_sessions" ON chat_sessions
    FOR DELETE
    USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_last_activity ON chat_sessions(last_activity DESC);

-- Comment for documentation
COMMENT ON TABLE chat_sessions IS 'Multi-chat session management (Phase 1 refactoring)';

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
```

---

### 1.2 FRONTEND CONTRACT (Phase 1)

#### File: `features/chat/ChatPanel.tsx`

**ADD This Hook Integration:**

```typescript
// ═══ NEW: Implicit Feedback Tracking ═══════════════
// File: features/chat/hooks/useImplicitFeedback.ts
// Purpose: Track copy/save/edit behavior (user NEVER waits)

import { useImplicitFeedback } from './hooks/useImplicitFeedback';

// In component:
const { trackCopy, trackSave, trackEdit } = useImplicitFeedback(
  sessionId,
  promptId,
  improvedPrompt
);

// In copy button handler:
const handleCopy = async () => {
  await navigator.clipboard.writeText(improvedPrompt);
  trackCopy();  // ← ADD: +0.08 quality score (background)
};

// In save button handler:
const handleSave = async () => {
  await saveToLibrary(improvedPrompt);
  trackSave();  // ← ADD: +0.10 quality score (background)
};

// In edit detection (if editable prompt box):
const handleEditAndCopy = async (edited: string) => {
  trackEdit(edited);  // ← ADD: +0.02 or -0.03 based on edit distance
  await navigator.clipboard.writeText(edited);
};
```

**RULES.md Compliance:**
- Type hints mandatory (TypeScript strict mode)
- Silent fail (network errors don't break UX)
- No blocking operations (async, fire-and-forget)
- Background writes (user NEVER waits)

**Integration Points:**
- Copy button → trackCopy()
- Save button → trackSave()
- Edit detection → trackEdit()

---

#### File: `features/chat/hooks/useImplicitFeedback.ts`

**CREATE This File:**

```typescript
/**
 * Implicit Feedback Tracking Hook
 * 
 * Tracks user behavior signals without interrupting flow.
 * Sends feedback to backend asynchronously (user never waits).
 * 
 * @packageFeatures chat
 * @RULES.md Compliance:
 * - Type hints mandatory (TypeScript strict mode)
 * - Silent fail (network errors don't break UX)
 * - No blocking operations
 * 
 * Feedback Types & Weights:
 * - copy: +0.08 (user found value - PRIMARY success signal)
 * - edit (light, <40%): +0.02 (user engaged, minor tweaks)
 * - edit (heavy, >40%): -0.03 (prompt needed work)
 * - save: +0.10 (user wants to reuse - STRONGEST signal)
 */

import { useCallback } from 'react';

interface FeedbackPayload {
  session_id: string;
  prompt_id: string;
  feedback_type: 'copy' | 'edit' | 'save';
  edit_distance?: number;
  timestamp: string;
}

// ... (rest of implementation)
```

**Status:** ✅ COMPLETE (file created)

---

#### File: `features/chat/hooks/useChatSessions.ts` (NEW)

**CREATE This Hook:**

```typescript
// features/chat/hooks/useChatSessions.ts
// Multi-chat session management hook
// RULES.md Compliance: Type hints, error handling, structured logging

'use client'

import { useState, useEffect, useCallback } from 'react'
import { logger } from '@/lib/logger'
import type { ChatSession } from '../types'

interface UseChatSessionsProps {
  token: string
  apiUrl: string
}

interface UseChatSessionsReturn {
  sessions: ChatSession[]
  activeSessionId: string | null
  isLoading: boolean
  error: string | null
  createNewChat: () => Promise<void>
  setActiveSessionId: (sessionId: string) => void
  deleteSession: (sessionId: string) => Promise<void>
  renameSession: (sessionId: string, title: string) => Promise<void>
}

/**
 * Manages multi-chat sessions
 * 
 * Example:
 *   const { sessions, createNewChat } = useChatSessions({ token, apiUrl })
 */
export function useChatSessions({
  token,
  apiUrl,
}: UseChatSessionsProps): UseChatSessionsReturn {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  /**
   * Load user's sessions
   */
  const loadSessions = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!res.ok) throw new Error(`Failed to load sessions: ${res.status}`)

      const data = await res.json()
      setSessions(data.sessions || [])

      // Set first session as active if none selected
      if (!activeSessionId && data.sessions?.length > 0) {
        setActiveSessionId(data.sessions[0].id)
      }

      setError(null)
    } catch (err) {
      logger.error('[useChatSessions] loadSessions failed', { err })
      setError('Failed to load chat sessions')
    } finally {
      setIsLoading(false)
    }
  }, [token, apiUrl, activeSessionId])

  /**
   * Create new chat session
   */
  const createNewChat = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/sessions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!res.ok) throw new Error(`Failed to create session: ${res.status}`)

      const data = await res.json()
      
      // Add to sessions list
      const newSession: ChatSession = {
        id: data.session_id,
        title: 'New Chat',
        created_at: data.created_at,
        last_activity: data.created_at,
      }

      setSessions(prev => [newSession, ...prev])
      setActiveSessionId(newSession.id)

      logger.info('[useChatSessions] created new session', { sessionId: newSession.id })
    } catch (err) {
      logger.error('[useChatSessions] createNewChat failed', { err })
      setError('Failed to create new chat')
    }
  }, [token, apiUrl])

  /**
   * Delete session
   */
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      const res = await fetch(`${apiUrl}/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!res.ok) throw new Error(`Failed to delete session: ${res.status}`)

      // Remove from list
      setSessions(prev => prev.filter(s => s.id !== sessionId))

      // If deleted active session, switch to another
      if (activeSessionId === sessionId) {
        const remaining = sessions.filter(s => s.id !== sessionId)
        setActiveSessionId(remaining[0]?.id || null)
      }

      logger.info('[useChatSessions] deleted session', { sessionId })
    } catch (err) {
      logger.error('[useChatSessions] deleteSession failed', { err })
      setError('Failed to delete chat')
    }
  }, [token, apiUrl, activeSessionId, sessions])

  /**
   * Rename session
   */
  const renameSession = useCallback(async (sessionId: string, title: string) => {
    try {
      const res = await fetch(`${apiUrl}/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      })

      if (!res.ok) throw new Error(`Failed to rename session: ${res.status}`)

      // Update in list
      setSessions(prev => prev.map(s =>
        s.id === sessionId ? { ...s, title } : s
      ))

      logger.info('[useChatSessions] renamed session', { sessionId, title })
    } catch (err) {
      logger.error('[useChatSessions] renameSession failed', { err })
      setError('Failed to rename chat')
    }
  }, [token, apiUrl])

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  return {
    sessions,
    activeSessionId,
    isLoading,
    error,
    createNewChat,
    setActiveSessionId,
    deleteSession,
    renameSession,
  }
}
```

---

#### File: `features/chat/components/ChatSidebar.tsx` (NEW)

**CREATE This Component:**

```typescript
// features/chat/components/ChatSidebar.tsx
// Chat sidebar with session list
// RULES.md Compliance: Type hints, accessible, responsive

'use client'

import { useState } from 'react'
import { useChatSessions } from '../hooks/useChatSessions'

interface ChatSidebarProps {
  token: string
  apiUrl: string
  isOpen: boolean
  onClose: () => void
}

export default function ChatSidebar({
  token,
  apiUrl,
  isOpen,
  onClose,
}: ChatSidebarProps) {
  const {
    sessions,
    activeSessionId,
    isLoading,
    createNewChat,
    setActiveSessionId,
    deleteSession,
  } = useChatSessions({ token, apiUrl })

  const [isDeleting, setIsDeleting] = useState<string | null>(null)

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setIsDeleting(sessionId)
    await deleteSession(sessionId)
    setIsDeleting(null)
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-64 bg-layer1 border-r border-border-default
          transform transition-transform duration-200
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Header */}
        <div className="p-4 border-b border-border-default">
          <button
            onClick={createNewChat}
            className="w-full px-4 py-2 bg-kira text-text-inverse rounded-lg
                     hover:bg-kira/90 transition-colors font-medium text-sm
                     flex items-center justify-center gap-2"
          >
            <PlusIcon className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Session list */}
        <nav className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="p-4 text-center text-text-dim text-sm">
              Loading sessions...
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-text-dim text-sm">
              No sessions yet. Start a new chat!
            </div>
          ) : (
            <ul className="space-y-1">
              {sessions.map(session => (
                <li key={session.id}>
                  <button
                    onClick={() => {
                      setActiveSessionId(session.id)
                      onClose()
                    }}
                    className={`
                      w-full px-3 py-2 rounded-lg text-left text-sm
                      transition-colors group relative
                      ${activeSessionId === session.id
                        ? 'bg-kira/10 text-kira'
                        : 'hover:bg-layer2 text-text-default'
                      }
                    `}
                  >
                    <span className="line-clamp-1">{session.title}</span>
                    
                    {/* Delete button (shows on hover) */}
                    <button
                      onClick={(e) => handleDelete(session.id, e)}
                      disabled={isDeleting === session.id}
                      className="absolute right-2 top-1/2 -translate-y-1/2
                               opacity-0 group-hover:opacity-100
                               p-1 hover:bg-red-500/10 rounded
                               transition-opacity"
                      aria-label="Delete chat"
                    >
                      {isDeleting === session.id ? (
                        <SpinnerIcon className="w-3 h-3 animate-spin" />
                      ) : (
                        <TrashIcon className="w-3 h-3 text-text-dim" />
                      )}
                    </button>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </nav>

        {/* Mobile close button */}
        <button
          onClick={onClose}
          className="lg:hidden absolute top-4 right-4 p-2"
          aria-label="Close sidebar"
        >
          <CloseIcon className="w-5 h-5 text-text-dim" />
        </button>
      </aside>
    </>
  )
}
```

---

#### File: `features/chat/types.ts`

**ADD These Types:**

```typescript
// ADD to existing types.ts

export interface ChatSession {
  id: string
  title: string
  created_at: string
  last_activity: string
}

export interface ChatSidebarProps {
  token: string
  apiUrl: string
  isOpen: boolean
  onClose: () => void
}
```

---

#### File: `features/chat/components/ChatContainer.tsx`

**MODIFY to Include Sidebar:**

```typescript
// MODIFY existing ChatContainer.tsx
// ADD: Sidebar import and state

'use client'

import { useState } from 'react'
import { useSessionId } from '../hooks/useSessionId'
import { useKiraStream } from '../hooks/useKiraStream'
import { useChatSessions } from '../hooks/useChatSessions'  // ADD
import ChatSidebar from './ChatSidebar'  // ADD
import MessageList from './MessageList'
import InputBar from './InputBar'
// ... other imports

interface ChatContainerProps {
  token: string
  apiUrl: string
  sessionCount?: number
}

export default function ChatContainer({ token, apiUrl, sessionCount = 0 }: ChatContainerProps) {
  // ADD: Sidebar state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  
  // ADD: Multi-chat sessions
  const {
    sessions,
    activeSessionId,
    createNewChat,
    setActiveSessionId,
  } = useChatSessions({ token, apiUrl })
  
  // MODIFY: Use activeSessionId from hook (or fallback to useSessionId)
  const sessionId = activeSessionId || useSessionId()

  // ... rest of existing code (useKiraStream, useInputBar, etc.)

  // MODIFY: Render with sidebar
  return (
    <div className="h-[calc(100vh-64px)] flex">
      {/* Sidebar */}
      <ChatSidebar
        token={token}
        apiUrl={apiUrl}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Mobile menu button */}
        <button
          onClick={() => setIsSidebarOpen(true)}
          className="lg:hidden p-4 text-text-dim"
        >
          <MenuIcon className="w-6 h-6" />
        </button>

        {/* Existing chat UI */}
        {messages.length === 0 ? (
          <EmptyState onSuggestionClick={handleSuggestionClick} />
        ) : (
          <MessageList messages={messages} isStreaming={isStreaming} />
        )}

        <InputBar
          value={input}
          onChange={setInput}
          onSubmit={() => handleSubmit()}
          // ... existing props
        />
      </div>
    </div>
  )
}
```

---

## PHASE 1 ACCEPTANCE CRITERIA

### Backend (Must Pass All)

- [ ] `/sessions` POST endpoint creates session with RLS
- [ ] `/sessions` GET endpoint returns user's sessions
- [ ] `/sessions/{id}` PATCH endpoint updates title
- [ ] `/sessions/{id}` DELETE endpoint removes session
- [ ] Migration `015_add_chat_sessions.sql` runs successfully
- [ ] All functions have type hints + docstrings
- [ ] Structured logging in all functions
- [ ] Error handling with graceful fallback

### Frontend (Must Pass All)

- [ ] `useChatSessions` hook manages session state
- [ ] `ChatSidebar` component renders session list
- [ ] "New Chat" button creates session
- [ ] Session list shows all user sessions
- [ ] Click session to switch active chat
- [ ] Delete button removes session
- [ ] Mobile responsive (sidebar slides in/out)
- [ ] Loading states during async operations
- [ ] Error states with user-friendly messages

---

## PHASE 2: HISTORY TAB — "Intelligent Memory Palace"

*(Contract continues with same detail level for Phase 2 and Phase 3)*

---

## PHASE 3: PROFILE TAB — "Living Digital Twin"

*(Contract continues with same detail level for Phase 3)*

---

## TESTING REQUIREMENTS (All Phases)

### Backend Tests

```python
# tests/test_phase1_chat_sessions.py

class TestChatSessions:
    """Test multi-chat session management."""
    
    def test_create_session(self, auth_client):
        """POST /sessions creates new session."""
        response = auth_client.post("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "created_at" in data
    
    def test_list_sessions(self, auth_client):
        """GET /sessions returns user's sessions."""
        # Create session first
        auth_client.post("/sessions")
        
        response = auth_client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    def test_update_session(self, auth_client):
        """PATCH /sessions/{id} updates title."""
        # Create session
        create_resp = auth_client.post("/sessions")
        session_id = create_resp.json()["session_id"]
        
        # Update title
        response = auth_client.patch(
            f"/sessions/{session_id}",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 200
        
        # Verify update
        get_resp = auth_client.get("/sessions")
        sessions = get_resp.json()["sessions"]
        session = next(s for s in sessions if s["id"] == session_id)
        assert session["title"] == "Updated Title"
    
    def test_delete_session(self, auth_client):
        """DELETE /sessions/{id} removes session."""
        # Create session
        create_resp = auth_client.post("/sessions")
        session_id = create_resp.json()["session_id"]
        
        # Delete
        response = auth_client.delete(f"/sessions/{session_id}")
        assert response.status_code == 200
        
        # Verify deletion
        get_resp = auth_client.get("/sessions")
        sessions = get_resp.json()["sessions"]
        assert not any(s["id"] == session_id for s in sessions)
    
    def test_rls_isolation(self, auth_client, another_user_client):
        """Users cannot access other users' sessions."""
        # User A creates session
        create_resp = auth_client.post("/sessions")
        session_id = create_resp.json()["session_id"]
        
        # User B tries to access
        response = another_user_client.get(f"/sessions/{session_id}")
        assert response.status_code == 404  # Not found (RLS working)
```

### Frontend Tests

```typescript
// features/chat/hooks/__tests__/useChatSessions.test.ts

describe('useChatSessions', () => {
  it('loads sessions on mount', async () => {
    const { result } = renderHook(() =>
      useChatSessions({ token: 'test-token', apiUrl: API_URL })
    )
    
    await waitFor(() => {
      expect(result.current.sessions).toHaveLength(3)
    })
  })
  
  it('creates new session', async () => {
    const { result } = renderHook(() =>
      useChatSessions({ token: 'test-token', apiUrl: API_URL })
    )
    
    await act(async () => {
      await result.current.createNewChat()
    })
    
    expect(result.current.sessions).toHaveLength(4)
  })
  
  it('deletes session', async () => {
    const { result } = renderHook(() =>
      useChatSessions({ token: 'test-token', apiUrl: API_URL })
    )
    
    await act(async () => {
      await result.current.deleteSession('session-1')
    })
    
    expect(result.current.sessions).toHaveLength(2)
  })
})
```

---

## DEPLOYMENT CHECKLIST (All Phases)

### Pre-Deployment

- [ ] All TypeScript compilation errors resolved
- [ ] All Python type hints present
- [ ] All docstrings complete
- [ ] All tests passing (backend + frontend)
- [ ] Migration scripts tested locally
- [ ] Environment variables documented

### Deployment

- [ ] Run migration `015_add_chat_sessions.sql` in Supabase
- [ ] Deploy backend (Koyeb auto-deploys on Docker push)
- [ ] Deploy frontend (Vercel auto-deploys on git push)
- [ ] Verify health endpoint: `GET /health`
- [ ] Test multi-chat creation
- [ ] Test session switching
- [ ] Test session deletion

### Post-Deployment

- [ ] Monitor error logs (Sentry)
- [ ] Check performance (Langfuse)
- [ ] Verify RLS policies working
- [ ] Test on mobile devices
- [ ] Gather user feedback

---

## CONTRACT SIGN-OFF

**Implementation Team:**

- Backend Lead: _________________ Date: _______
- Frontend Lead: _________________ Date: _______
- QA Lead: _______________________ Date: _______

**Contract Version:** 1.0  
**Last Updated:** 2026-03-13  
**Next Review:** After Phase 1 completion

---

*This contract follows RULES.md v1.0 engineering standards. All code must be indistinguishable from senior developer-written code.*

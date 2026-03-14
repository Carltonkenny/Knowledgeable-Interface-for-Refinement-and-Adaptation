-- ============================================================
-- PromptForge v2.0 - Unified Chat Sessions Migration
-- ============================================================
-- Purpose: Merge inactivity tracking with multi-chat support.
-- This replaces the "old" user_sessions with the "new" chat_sessions.
-- Run in Supabase SQL Editor.
-- ============================================================

BEGIN;

-- 1. Rename existing table if it exists (Modular Step 1.1)
-- If Migration 011 was already run, we rename it to stay consistent.
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'user_sessions') THEN
        ALTER TABLE user_sessions RENAME TO chat_sessions;
    END IF;
END $$;

-- 2. Ensure table and columns exist (Modular Step 1.1)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'New Chat',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_title CHECK (length(title) <= 100)
);

-- If the table was renamed from user_sessions, it has a redundant 'session_id' column.
-- We must DROP it because the 'id' (UUID) is now our master Session ID.
ALTER TABLE chat_sessions DROP COLUMN IF EXISTS session_id;
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title TEXT DEFAULT 'New Chat';

-- 3. Data Scrubbing (The "Cleaning" Fact)
-- We must remove rows with invalid UUID strings OR non-existent users.

-- A. Scrub "Ghost Users" (Users not in auth.users)
-- This prevents foreign key violations during session creation.
DELETE FROM agent_logs WHERE request_id IN (SELECT id FROM requests WHERE user_id NOT IN (SELECT id FROM auth.users));
DELETE FROM prompt_history WHERE user_id NOT IN (SELECT id FROM auth.users);
DELETE FROM conversations WHERE user_id NOT IN (SELECT id FROM auth.users);
DELETE FROM requests WHERE user_id NOT IN (SELECT id FROM auth.users);

-- B. Clean agent_logs second (they depend on requests)
DELETE FROM agent_logs 
WHERE request_id IN (
    SELECT id FROM requests 
    WHERE session_id IS NULL OR session_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
);

-- B. Clean requests
DELETE FROM requests 
WHERE session_id IS NULL OR session_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- C. Clean conversations
DELETE FROM conversations 
WHERE session_id IS NULL OR session_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- D. Clean prompt_history (if exists)
DELETE FROM prompt_history 
WHERE session_id IS NULL OR session_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- 4. Backfill Missing Sessions (The "Orphan" Fact)
-- We have messages that have valid UUIDs, but those sessions aren't in chat_sessions yet.
-- We must "backfill" them so the Foreign Key constraint doesn't fail.

-- Insert missing sessions from conversations
INSERT INTO chat_sessions (id, user_id, title)
SELECT DISTINCT session_id::UUID, COALESCE(user_id, '00000000-0000-0000-0000-000000000000'), 'Restored Chat'
FROM conversations
WHERE session_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
ON CONFLICT (id) DO NOTHING;

-- Insert missing sessions from requests
INSERT INTO chat_sessions (id, user_id, title)
SELECT DISTINCT session_id::UUID, COALESCE(user_id, '00000000-0000-0000-0000-000000000000'), 'Restored Chat'
FROM requests
WHERE session_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
ON CONFLICT (id) DO NOTHING;

-- 5. Modify existing tables to link to chat_sessions
-- Now that data and its children are clean, and parents are backfilled, the cast will succeed.

-- Update conversations table
ALTER TABLE conversations 
    ALTER COLUMN session_id TYPE UUID USING session_id::UUID;

ALTER TABLE conversations
    ADD CONSTRAINT fk_conversations_session 
    FOREIGN KEY (session_id) 
    REFERENCES chat_sessions(id) 
    ON DELETE CASCADE;

-- Update requests table (for prompt history)
ALTER TABLE requests 
    ALTER COLUMN session_id TYPE UUID USING session_id::UUID;

ALTER TABLE requests
    ADD CONSTRAINT fk_requests_session 
    FOREIGN KEY (session_id) 
    REFERENCES chat_sessions(id) 
    ON DELETE CASCADE;

-- 4. Re-enable RLS
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_manage_own_sessions" ON chat_sessions
    FOR ALL USING (auth.uid() = user_id);

-- 5. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_last ON chat_sessions(user_id, last_activity DESC);

COMMIT;

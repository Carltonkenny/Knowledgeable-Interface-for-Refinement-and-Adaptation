-- migration: 017_recycle_bin.sql
-- Adds soft-delete (Recycle Bin) support to chat_sessions

ALTER TABLE chat_sessions 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Update RLS policies to handle deleted sessions
-- Professional sessions should be hidden from standard views but visible in the recycle bin.
-- We don't need to change existing policies as they check ownership, 
-- we will handle filtering in the database functions via '.is("deleted_at", "null")'.

COMMENT ON COLUMN chat_sessions.deleted_at IS 'When the session was soft-deleted. NULL means it is active.';

-- Index for performance on filtering deleted items
CREATE INDEX IF NOT EXISTS idx_chat_sessions_deleted_at ON chat_sessions(deleted_at) WHERE deleted_at IS NOT NULL;

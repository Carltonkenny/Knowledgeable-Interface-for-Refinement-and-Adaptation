-- ============================================================
-- PromptForge v2.0 - Add user_sessions Table for Inactivity Tracking
-- ============================================================
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
--
-- What this does:
--   1. Creates user_sessions table for tracking session activity
--   2. Enables profile updater to trigger on 30min inactivity
--   3. Adds RLS policies for user isolation
--
-- Time: ~10 seconds
-- ============================================================

BEGIN;

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    session_id text NOT NULL,
    last_activity timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity DESC);

-- Enable RLS
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "users_select_own_sessions" ON user_sessions
  FOR SELECT
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_insert_own_sessions" ON user_sessions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_update_own_sessions" ON user_sessions
  FOR UPDATE
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_delete_own_sessions" ON user_sessions
  FOR DELETE
  USING (auth.uid() = user_id OR user_id IS NULL);

COMMENT ON TABLE user_sessions IS 'Session activity tracking for profile updater inactivity trigger (RULES.md)';
COMMENT ON COLUMN user_sessions.last_activity IS 'Last activity timestamp - used for 30min inactivity trigger';

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
--
-- Expected Results:
--   ✅ user_sessions table created
--   ✅ RLS policies enabled
--   ✅ Indexes created for performance
--
-- Next Steps:
--   1. Verify in Dashboard: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
--   2. Profile updater will now trigger on 30min inactivity
--
-- ============================================================

-- ============================================================
-- PromptForge v2.0 - Phase 4 Profile Enhancements
-- ============================================================
-- Purpose: Add username tracking and GDPR cascade deletes.
-- ============================================================

BEGIN;

-- 1. Add username to user_profiles
ALTER TABLE IF EXISTS user_profiles
ADD COLUMN IF NOT EXISTS username TEXT;

-- 2. Add unique index for username (ensure it's unique across all users)
-- Note: We make it unique globally, not just per user, so usernames can be handles
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profiles_username
ON user_profiles(username)
WHERE username IS NOT NULL;

-- 3. Add cascade deletes for GDPR compliance
-- If these foreign keys already exist without CASCADE, we must drop and recreate them.

-- A. requests table -> auth.users
ALTER TABLE requests DROP CONSTRAINT IF EXISTS requests_user_id_fkey;
ALTER TABLE requests DROP CONSTRAINT IF EXISTS fk_requests_user;
ALTER TABLE requests
ADD CONSTRAINT fk_requests_user
FOREIGN KEY (user_id) REFERENCES auth.users(id)
ON DELETE CASCADE;

-- B. chat_sessions table -> auth.users
ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey;
ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS fk_chat_sessions_user;
ALTER TABLE chat_sessions
ADD CONSTRAINT fk_chat_sessions_user
FOREIGN KEY (user_id) REFERENCES auth.users(id)
ON DELETE CASCADE;

-- C. conversations table -> auth.users
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_user_id_fkey;
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS fk_conversations_user;
ALTER TABLE conversations
ADD CONSTRAINT fk_conversations_user
FOREIGN KEY (user_id) REFERENCES auth.users(id)
ON DELETE CASCADE;

-- D. user_profiles table -> auth.users
ALTER TABLE user_profiles DROP CONSTRAINT IF EXISTS user_profiles_user_id_fkey;
ALTER TABLE user_profiles DROP CONSTRAINT IF EXISTS fk_user_profiles_user;
ALTER TABLE user_profiles
ADD CONSTRAINT fk_user_profiles_user
FOREIGN KEY (user_id) REFERENCES auth.users(id)
ON DELETE CASCADE;

-- E. agent_logs -> requests -> auth.users (Indirect cascading)
-- agent_logs should cascade when requests are deleted.
ALTER TABLE agent_logs DROP CONSTRAINT IF EXISTS agent_logs_request_id_fkey;
ALTER TABLE agent_logs DROP CONSTRAINT IF EXISTS fk_agent_logs_request;
ALTER TABLE agent_logs
ADD CONSTRAINT fk_agent_logs_request
FOREIGN KEY (request_id) REFERENCES requests(id)
ON DELETE CASCADE;


COMMIT;

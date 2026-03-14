-- migration: 016_session_enhancements.sql
-- Adds pinning and favoriting support to chat_sessions

ALTER TABLE chat_sessions 
ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT FALSE;

-- Ensure RLS is still correct (should be inherited from chat_sessions policy)
-- But just in case, verify users can only update their own pins
DROP POLICY IF EXISTS "Users can update their own sessions" ON chat_sessions;
CREATE POLICY "Users can update their own sessions" ON chat_sessions
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

COMMENT ON COLUMN chat_sessions.is_pinned IS 'Allows user to pin sessions to the top of the sidebar';
COMMENT ON COLUMN chat_sessions.is_favorite IS 'Marks session as a favorite for easy filtering';

-- ============================================================
-- Migration 013: Create mcp_tokens Table
-- ============================================================
-- Long-lived MCP access tokens (365 days)
-- RULES.md: JWT authentication for MCP surface
-- Time: ~5 seconds
-- ============================================================

BEGIN;

-- Step 1: Create mcp_tokens table
CREATE TABLE IF NOT EXISTS mcp_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    token_hash text NOT NULL,
    token_type text DEFAULT 'mcp_access' CHECK (token_type IN ('mcp_access')),
    expires_at timestamp with time zone NOT NULL,
    revoked boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT mcp_tokens_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Step 2: Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_mcp_tokens_user_id ON mcp_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_tokens_hash ON mcp_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_mcp_tokens_expires ON mcp_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_mcp_tokens_revoked ON mcp_tokens(revoked);

-- Step 3: Enable Row Level Security (RLS)
ALTER TABLE mcp_tokens ENABLE ROW LEVEL SECURITY;

-- Step 4: Create RLS policies
CREATE POLICY "users_select_own_tokens" ON mcp_tokens
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_tokens" ON mcp_tokens
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users_update_own_tokens" ON mcp_tokens
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "users_delete_own_tokens" ON mcp_tokens
    FOR DELETE
    USING (auth.uid() = user_id);

-- Admin can revoke any token (for security)
CREATE POLICY "admin_revoke_any_token" ON mcp_tokens
    FOR UPDATE
    USING (true)
    WITH CHECK (revoked = true);

-- Step 5: Add comments for documentation
COMMENT ON TABLE mcp_tokens IS 'Long-lived MCP access tokens (365 days) - RULES.md Section 9';
COMMENT ON COLUMN mcp_tokens.token_hash IS 'SHA-256 hash of JWT token (for revocation check)';
COMMENT ON COLUMN mcp_tokens.token_type IS 'Token type: mcp_access (long-lived MCP JWT)';
COMMENT ON COLUMN mcp_tokens.expires_at IS 'Token expiration timestamp (365 days from creation)';
COMMENT ON COLUMN mcp_tokens.revoked IS 'True if token has been revoked by user or admin';

COMMIT;

-- ============================================================
-- Verification Queries
-- ============================================================

-- Check table was created
SELECT 
    tablename as table_name,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'mcp_tokens';

-- Check columns
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'mcp_tokens'
ORDER BY ordinal_position;

-- Check policies
SELECT 
    policyname as policy_name,
    cmd as operation
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'mcp_tokens'
ORDER BY policyname;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
--
-- Expected Results:
--   ✅ mcp_tokens table created
--   ✅ 4 indexes created
--   ✅ 5 RLS policies created
--   ✅ Ready for /mcp/generate-token endpoint
--
-- Next Steps:
--   1. Verify in Supabase Dashboard
--   2. Deploy /mcp/generate-token endpoint
--   3. Update MCP server to validate long-lived JWT
-- ============================================================

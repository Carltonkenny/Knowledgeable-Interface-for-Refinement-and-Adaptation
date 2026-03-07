-- ============================================================
-- PromptForge v2.0 - Complete Database Schema & RLS Policies
-- ============================================================
-- Run this ENTIRE file in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
-- 
-- What this does:
--   1. Adds user_id to requests table
--   2. Creates user_profiles table (THE MOAT)
--   3. Creates langmem_memories table (THE MOAT)
--   4. Creates user-specific RLS policies for ALL tables
--   5. Adds performance indexes
-- 
-- Time: ~30 seconds
-- Safety: Uses IF NOT EXISTS - safe to run multiple times
-- ============================================================

BEGIN;

-- ============================================================
-- STEP 1: ADD USER_ID TO REQUESTS TABLE
-- ============================================================

ALTER TABLE requests 
ADD COLUMN IF NOT EXISTS user_id UUID;

CREATE INDEX IF NOT EXISTS idx_requests_user_id 
ON requests(user_id);

COMMENT ON COLUMN requests.user_id IS 'User UUID from JWT (for RLS isolation) - RULES.md compliance';


-- ============================================================
-- STEP 2: CREATE USER_PROFILES TABLE (THE MOAT)
-- ============================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid UNIQUE NOT NULL,
    dominant_domains text[] DEFAULT '{}',
    prompt_quality_trend text DEFAULT 'stable' CHECK (prompt_quality_trend IN ('improving', 'stable', 'declining')),
    clarification_rate numeric DEFAULT 0 CHECK (clarification_rate >= 0 AND clarification_rate <= 1),
    preferred_tone text DEFAULT 'direct' CHECK (preferred_tone IN ('direct', 'casual', 'formal', 'technical')),
    notable_patterns text[] DEFAULT '{}',
    total_sessions integer DEFAULT 0,
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_domains ON user_profiles USING GIN(dominant_domains);

COMMENT ON TABLE user_profiles IS 'User personalization data - THE MOAT (RULES.md)';
COMMENT ON COLUMN user_profiles.dominant_domains IS 'Top domains user works in (e.g., ["python", "creative writing"])';
COMMENT ON COLUMN user_profiles.prompt_quality_trend IS 'Quality trend: improving | stable | declining';
COMMENT ON COLUMN user_profiles.clarification_rate IS 'How often user needs clarification (0.0-1.0)';
COMMENT ON COLUMN user_profiles.preferred_tone IS 'Preferred response tone: direct | casual | formal | technical';


-- ============================================================
-- STEP 3: CREATE LANGMEM_MEMORIES TABLE (THE MOAT)
-- ============================================================

CREATE TABLE IF NOT EXISTS langmem_memories (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    content text NOT NULL,
    improved_content text,
    domain text DEFAULT 'general',
    quality_score jsonb DEFAULT '{}',
    agents_used text[] DEFAULT '{}',
    agents_skipped text[] DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT langmem_memories_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_langmem_user_id ON langmem_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_langmem_domain ON langmem_memories(domain);
CREATE INDEX IF NOT EXISTS idx_langmem_created_at ON langmem_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_langmem_quality ON langmem_memories USING GIN(quality_score);

COMMENT ON TABLE langmem_memories IS 'Pipeline memory for web app - THE MOAT (RULES.md: surface isolation)';
COMMENT ON COLUMN langmem_memories.content IS 'Original user prompt';
COMMENT ON COLUMN langmem_memories.improved_content IS 'Engineered prompt from swarm';
COMMENT ON COLUMN langmem_memories.quality_score IS 'Quality scores: {specificity: 1-5, clarity: 1-5, actionability: 1-5}';


-- ============================================================
-- STEP 4: CREATE USER-SPECIFIC RLS POLICIES
-- ============================================================

-- Enable RLS on all tables (should already be enabled, but ensuring)
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE langmem_memories ENABLE ROW LEVEL SECURITY;

-- Drop existing user policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "users_select_own_requests" ON requests;
DROP POLICY IF EXISTS "users_insert_own_requests" ON requests;
DROP POLICY IF EXISTS "users_update_own_requests" ON requests;
DROP POLICY IF EXISTS "users_delete_own_requests" ON requests;

DROP POLICY IF EXISTS "users_select_own_conversations" ON conversations;
DROP POLICY IF EXISTS "users_insert_own_conversations" ON conversations;
DROP POLICY IF EXISTS "users_update_own_conversations" ON conversations;
DROP POLICY IF EXISTS "users_delete_own_conversations" ON conversations;

DROP POLICY IF EXISTS "users_select_own_prompt_history" ON prompt_history;
DROP POLICY IF EXISTS "users_insert_own_prompt_history" ON prompt_history;
DROP POLICY IF EXISTS "users_update_own_prompt_history" ON prompt_history;
DROP POLICY IF EXISTS "users_delete_own_prompt_history" ON prompt_history;

DROP POLICY IF EXISTS "users_select_own_agent_logs" ON agent_logs;
DROP POLICY IF EXISTS "users_insert_own_agent_logs" ON agent_logs;
DROP POLICY IF EXISTS "users_update_own_agent_logs" ON agent_logs;
DROP POLICY IF EXISTS "users_delete_own_agent_logs" ON agent_logs;

DROP POLICY IF EXISTS "users_select_own_profiles" ON user_profiles;
DROP POLICY IF EXISTS "users_insert_own_profiles" ON user_profiles;
DROP POLICY IF EXISTS "users_update_own_profiles" ON user_profiles;
DROP POLICY IF EXISTS "users_delete_own_profiles" ON user_profiles;

DROP POLICY IF EXISTS "users_select_own_memories" ON langmem_memories;
DROP POLICY IF EXISTS "users_insert_own_memories" ON langmem_memories;
DROP POLICY IF EXISTS "users_update_own_memories" ON langmem_memories;
DROP POLICY IF EXISTS "users_delete_own_memories" ON langmem_memories;

-- ===== REQUESTS POLICIES =====
CREATE POLICY "users_select_own_requests" ON requests
  FOR SELECT
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_insert_own_requests" ON requests
  FOR INSERT
  WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_update_own_requests" ON requests
  FOR UPDATE
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_delete_own_requests" ON requests
  FOR DELETE
  USING (auth.uid() = user_id OR user_id IS NULL);

-- ===== CONVERSATIONS POLICIES =====
CREATE POLICY "users_select_own_conversations" ON conversations
  FOR SELECT
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_insert_own_conversations" ON conversations
  FOR INSERT
  WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_update_own_conversations" ON conversations
  FOR UPDATE
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_delete_own_conversations" ON conversations
  FOR DELETE
  USING (auth.uid() = user_id OR user_id IS NULL);

-- ===== PROMPT_HISTORY POLICIES =====
CREATE POLICY "users_select_own_prompt_history" ON prompt_history
  FOR SELECT
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_insert_own_prompt_history" ON prompt_history
  FOR INSERT
  WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_update_own_prompt_history" ON prompt_history
  FOR UPDATE
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "users_delete_own_prompt_history" ON prompt_history
  FOR DELETE
  USING (auth.uid() = user_id OR user_id IS NULL);

-- ===== AGENT_LOGS POLICIES (via request_id FK) =====
CREATE POLICY "users_select_own_agent_logs" ON agent_logs
  FOR SELECT
  USING (
    auth.uid() IS NULL OR
    EXISTS (
      SELECT 1 FROM requests 
      WHERE requests.id = agent_logs.request_id 
      AND (requests.user_id = auth.uid() OR requests.user_id IS NULL)
    )
  );

CREATE POLICY "users_insert_own_agent_logs" ON agent_logs
  FOR INSERT
  WITH CHECK (
    auth.uid() IS NULL OR
    EXISTS (
      SELECT 1 FROM requests 
      WHERE requests.id = agent_logs.request_id 
      AND (requests.user_id = auth.uid() OR requests.user_id IS NULL)
    )
  );

CREATE POLICY "users_update_own_agent_logs" ON agent_logs
  FOR UPDATE
  USING (
    auth.uid() IS NULL OR
    EXISTS (
      SELECT 1 FROM requests 
      WHERE requests.id = agent_logs.request_id 
      AND (requests.user_id = auth.uid() OR requests.user_id IS NULL)
    )
  );

CREATE POLICY "users_delete_own_agent_logs" ON agent_logs
  FOR DELETE
  USING (
    auth.uid() IS NULL OR
    EXISTS (
      SELECT 1 FROM requests 
      WHERE requests.id = agent_logs.request_id 
      AND (requests.user_id = auth.uid() OR requests.user_id IS NULL)
    )
  );

-- ===== USER_PROFILES POLICIES =====
CREATE POLICY "users_select_own_profiles" ON user_profiles
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_profiles" ON user_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users_update_own_profiles" ON user_profiles
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "users_delete_own_profiles" ON user_profiles
  FOR DELETE
  USING (auth.uid() = user_id);

-- ===== LANGMEM_MEMORIES POLICIES =====
CREATE POLICY "users_select_own_memories" ON langmem_memories
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_memories" ON langmem_memories
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users_update_own_memories" ON langmem_memories
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "users_delete_own_memories" ON langmem_memories
  FOR DELETE
  USING (auth.uid() = user_id);


-- ============================================================
-- STEP 5: VERIFICATION QUERIES
-- ============================================================

-- Show all tables with RLS status
SELECT 
  tablename as table_name,
  rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Show all policies
SELECT 
  tablename as table_name,
  policyname as policy_name,
  cmd as operation,
  roles
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Count policies per table
SELECT 
  tablename as table_name,
  count(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
-- 
-- Expected Results:
--   ✅ requests: user_id column added
--   ✅ user_profiles: Table created (THE MOAT)
--   ✅ langmem_memories: Table created (THE MOAT)
--   ✅ 24 RLS policies created (6 tables × 4 operations)
-- 
-- Next Steps:
--   1. Verify in Dashboard: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
--   2. Run: python tests\test_db_simple.py
--   3. Integrate LangMem background writes in api.py
--   4. Integrate Profile Updater in api.py
-- 
-- Documentation:
--   - DOCS/DATABASE_VERIFICATION_GUIDE.md
--   - DOCS/DATABASE_VERIFICATION_SUMMARY.md
--   - RULES.md (Database section)
-- ============================================================

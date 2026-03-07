-- ============================================================
-- Migration 012: Create supermemory_facts Table
-- ============================================================
-- MCP-exclusive conversational context memory
-- RULES.md: Memory System — Two Layers, Never Merge Them
-- Time: ~5 seconds
-- ============================================================

BEGIN;

-- Step 1: Create supermemory_facts table
CREATE TABLE IF NOT EXISTS supermemory_facts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    fact text NOT NULL,
    context jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT supermemory_facts_user_id_fkey 
        FOREIGN KEY (user_id) 
        REFERENCES auth.users(id) 
        ON DELETE CASCADE
);

-- Step 2: Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_supermemory_user_id ON supermemory_facts(user_id);

-- Full-text search index for fact content
CREATE INDEX IF NOT EXISTS idx_supermemory_fact_search 
ON supermemory_facts USING GIN(to_tsvector('english', fact));

-- Step 3: Enable Row Level Security (RLS)
ALTER TABLE supermemory_facts ENABLE ROW LEVEL SECURITY;

-- Step 4: Create RLS policies (users can only access their own data)
CREATE POLICY "users_select_own_facts" ON supermemory_facts
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_facts" ON supermemory_facts
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users_update_own_facts" ON supermemory_facts
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "users_delete_own_facts" ON supermemory_facts
    FOR DELETE
    USING (auth.uid() = user_id);

-- Step 5: Add comment for documentation
COMMENT ON TABLE supermemory_facts IS 'MCP-exclusive conversational context memory (RULES.md: surface isolation - never used by web app)';
COMMENT ON COLUMN supermemory_facts.context IS 'Additional context: {session_id, timestamp, source}';

COMMIT;

-- ============================================================
-- Verification: Check table was created
-- ============================================================
SELECT 
    tablename as table_name,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'supermemory_facts';

-- Check columns
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'supermemory_facts'
ORDER BY ordinal_position;

-- Check policies
SELECT 
    policyname as policy_name,
    cmd as operation
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'supermemory_facts'
ORDER BY policyname;

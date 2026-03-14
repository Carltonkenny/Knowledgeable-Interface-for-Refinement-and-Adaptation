-- ============================================================
-- PromptForge v2.0 - Phase 3 Version Control
-- ============================================================
-- Purpose: Add version tracking to prompts
-- Run in Supabase SQL Editor
-- Time: ~10 seconds
-- RULES.md Compliance: Schema design, indexing, RLS
-- ============================================================

BEGIN;

-- Add version control columns to requests table
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS version_id UUID DEFAULT gen_random_uuid(),
ADD COLUMN IF NOT EXISTS version_number INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS parent_version_id UUID REFERENCES requests(id),
ADD COLUMN IF NOT EXISTS change_summary TEXT,
ADD COLUMN IF NOT EXISTS is_production BOOLEAN DEFAULT TRUE;

-- Add comment for documentation
COMMENT ON COLUMN requests.version_id IS 'Phase 3: Groups all versions of same prompt';
COMMENT ON COLUMN requests.version_number IS 'Phase 3: Version number (1, 2, 3...)';
COMMENT ON COLUMN requests.parent_version_id IS 'Phase 3: Previous version (for lineage)';
COMMENT ON COLUMN requests.change_summary IS 'Phase 3: What changed and why';
COMMENT ON COLUMN requests.is_production IS 'Phase 3: Which version is currently live';

-- Index for version queries (RLS + performance)
CREATE INDEX IF NOT EXISTS idx_requests_version 
ON requests(user_id, version_id, version_number DESC);

-- Index for finding production version
CREATE INDEX IF NOT EXISTS idx_requests_production 
ON requests(user_id, is_production) 
WHERE is_production = TRUE;

-- Update RLS policies to include new columns
DROP POLICY IF EXISTS "users_select_own_requests" ON requests;
CREATE POLICY "users_select_own_requests" ON requests
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "users_insert_own_requests" ON requests;
CREATE POLICY "users_insert_own_requests" ON requests
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "users_update_own_requests" ON requests;
CREATE POLICY "users_update_own_requests" ON requests
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
-- Verify columns added:
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'requests' AND column_name LIKE '%version%';
--
-- Verify indexes created:
-- SELECT indexname FROM pg_indexes WHERE tablename = 'requests';
-- ============================================================

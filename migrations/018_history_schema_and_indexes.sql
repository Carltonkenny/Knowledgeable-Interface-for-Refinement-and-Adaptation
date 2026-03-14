-- ============================================================
-- PromptForge v2.0 - Phase 2 History Schema Update
-- ============================================================
-- Purpose: Add missing columns to requests table for analytics
-- Run in Supabase SQL Editor
-- Time: ~15 seconds
-- RULES.md Compliance: Performance optimization
-- ============================================================

BEGIN;

-- ============================================================
-- STEP 1: ADD MISSING COLUMNS TO REQUESTS TABLE
-- ============================================================

-- Add quality_score column (JSONB)
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS quality_score jsonb DEFAULT '{}'::jsonb;

-- Add domain_analysis column (JSONB)
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS domain_analysis jsonb DEFAULT '{}'::jsonb;

-- Add agents_used column (TEXT array)
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS agents_used text[] DEFAULT '{}';

-- Add agents_skipped column (TEXT array)
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS agents_skipped text[] DEFAULT '{}';

-- Add prompt_diff column (JSONB)
ALTER TABLE requests
ADD COLUMN IF NOT EXISTS prompt_diff jsonb DEFAULT '[]'::jsonb;

COMMENT ON COLUMN requests.quality_score IS 'Phase 2: Quality scores {specificity, clarity, actionability}';
COMMENT ON COLUMN requests.domain_analysis IS 'Phase 2: Domain analysis {primary_domain, confidence}';
COMMENT ON COLUMN requests.agents_used IS 'Phase 2: Which agents ran for this request';
COMMENT ON COLUMN requests.agents_skipped IS 'Phase 2: Which agents were skipped + reasons';
COMMENT ON COLUMN requests.prompt_diff IS 'Phase 2: Diff between original and improved prompt';

-- ============================================================
-- STEP 2: CREATE PERFORMANCE INDEXES
-- ============================================================

-- Index for quality score queries (analytics)
CREATE INDEX IF NOT EXISTS idx_requests_quality_score
ON requests USING GIN (quality_score);

-- Index for domain analysis queries (filtering)
CREATE INDEX IF NOT EXISTS idx_requests_domain
ON requests USING GIN (domain_analysis);

-- Composite index for user + date queries (RLS + date filtering)
CREATE INDEX IF NOT EXISTS idx_requests_user_date
ON requests(user_id, created_at DESC);

-- Composite index for user + session queries (session grouping)
CREATE INDEX IF NOT EXISTS idx_requests_user_session
ON requests(user_id, session_id);

-- Full-text search index for keyword search (without RAG)
CREATE INDEX IF NOT EXISTS idx_requests_raw_prompt_search
ON requests USING GIN (to_tsvector('english', raw_prompt));

-- Comment for documentation
COMMENT ON INDEX idx_requests_quality_score IS
  'Phase 2: History analytics optimization';

COMMENT ON INDEX idx_requests_domain IS
  'Phase 2: Domain filtering optimization';

COMMENT ON INDEX idx_requests_user_date IS
  'Phase 2: User + date range queries';

COMMENT ON INDEX idx_requests_user_session IS
  'Phase 2: Session grouping queries';

COMMENT ON INDEX idx_requests_raw_prompt_search IS
  'Phase 2: Keyword search (non-RAG)';

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
-- Verify columns added:
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'requests' ORDER BY ordinal_position;
--
-- Verify indexes created:
-- SELECT indexname FROM pg_indexes WHERE tablename = 'requests';
-- ============================================================

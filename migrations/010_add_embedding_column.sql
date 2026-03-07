-- ============================================================
-- PromptForge v2.0 - Add Embedding Column to langmem_memories
-- ============================================================
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
--
-- What this does:
--   1. Adds embedding column (vector type) for semantic search
--   2. Creates index for fast similarity search
--   3. Enables pgvector extension if not already enabled
--
-- Time: ~10 seconds
-- ============================================================

BEGIN;

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to langmem_memories
ALTER TABLE langmem_memories
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_langmem_embedding 
ON langmem_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON COLUMN langmem_memories.embedding IS 'Embedding vector for semantic search (1536 dimensions, text-embedding-3-small)';

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
--
-- Expected Results:
--   ✅ embedding column added to langmem_memories
--   ✅ Index created for fast similarity search
--
-- Next Steps:
--   1. Verify in Dashboard: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
--   2. Test semantic search: python tests\test_langmem.py
--
-- ============================================================

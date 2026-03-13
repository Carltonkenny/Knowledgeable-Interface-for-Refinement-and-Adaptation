-- ============================================================
-- PromptForge v2.0 - Update Embedding for Gemini (HNSW Index)
-- ============================================================
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
--
-- IVFFlat index has 2000 dimension limit
-- HNSW supports up to 4096 dimensions (perfect for Gemini's 3072)
--
-- Time: ~15 seconds
-- ============================================================

BEGIN;

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop old embedding column if it exists
ALTER TABLE langmem_memories
DROP COLUMN IF EXISTS embedding;

-- Add new embedding column with 3072 dimensions for Gemini
ALTER TABLE langmem_memories
ADD COLUMN embedding vector(3072);

-- Drop old index if exists
DROP INDEX IF EXISTS idx_langmem_embedding;

-- Create HNSW index (supports high dimensions, faster than IVFFlat for 3072)
CREATE INDEX idx_langmem_embedding
ON langmem_memories USING hnsw (embedding vector_cosine_ops);

COMMENT ON COLUMN langmem_memories.embedding IS 'Embedding vector for semantic search (3072 dimensions, Gemini gemini-embedding-001)';

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================

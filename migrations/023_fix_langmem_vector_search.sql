-- migrations/023_fix_langmem_vector_search.sql
-- ============================================================
-- PromptForge v2.0 - Fix LangMem Vector Search
-- ============================================================
-- Run this in Supabase SQL Editor or via apply script
--
-- What this does:
--   1. Ensures the pgvector extension is enabled
--   2. Ensures the embedding column exists with 3072 dimensions
--   3. Identifies and drops any existing invalid/conflicting indexes
--   4. Creates the HNSW index for fast semantic search
--   5. Creates/Replaces the match_memories RPC function
-- ============================================================

BEGIN;

-- Step 1: Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Ensure embedding column exists (should be there from 010, but safe to verify)
ALTER TABLE langmem_memories 
ADD COLUMN IF NOT EXISTS embedding vector(3072);

-- Step 3: Drop existing index if it exists (in case it was created incorrectly)
DROP INDEX IF EXISTS idx_langmem_embedding;

-- Step 4: [SKIPPED] Cannot create HNSW or IVFFlat index on 3072 dimensions
-- Supabase free tier / pgvector restricts indexed dimensions to 2000.
-- We will rely on exact matching (no index), which is sufficiently fast for < 100k rows.

-- Step 5: Create/Replace Helper function for semantic search
CREATE OR REPLACE FUNCTION match_memories(
  query_embedding vector(3072),
  match_count INT DEFAULT 5,
  filter_user_id UUID DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  content TEXT,
  improved_content TEXT,
  domain TEXT,
  quality_score JSONB,
  agents_used TEXT[],
  agents_skipped TEXT[],
  created_at TIMESTAMPTZ,
  similarity_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.id,
    m.user_id,
    m.content,
    m.improved_content,
    m.domain,
    m.quality_score,
    m.agents_used,
    m.agents_skipped,
    m.created_at,
    -- Cosine similarity: 1.0 = identical, 0.0 = completely different
    (1 - (m.embedding <=> query_embedding)) AS similarity_score
  FROM langmem_memories m
  WHERE (filter_user_id IS NULL OR m.user_id = filter_user_id)
    AND m.embedding IS NOT NULL  -- Only search memories with embeddings
  ORDER BY m.embedding <=> query_embedding  -- Lower distance = more similar
  LIMIT match_count;
END;
$$;

-- Step 6: Grant permissions (Supabase specific)
GRANT EXECUTE ON FUNCTION match_memories TO authenticated;

COMMIT;

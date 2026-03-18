-- ============================================================
-- Migration 024: Fix Embedding Dimensions for Supabase Free Tier
-- ============================================================
-- Purpose: Switch from gemini-embedding-001 (3072 dims) to 
--          text-embedding-004 (768 dims) to stay under 2000 dim limit
-- Risk: Requires backfilling all existing embeddings
-- ============================================================
BEGIN;

-- Step 1: Null out old embeddings first (can't truncate vectors)
UPDATE langmem_memories SET embedding = NULL;

-- Step 2: Alter embedding column to new dimension
ALTER TABLE langmem_memories 
ALTER COLUMN embedding TYPE vector(768);

-- Step 3: Drop old HNSW index (3072 dims)
DROP INDEX IF EXISTS idx_langmem_embedding;

-- Step 4: Recreate HNSW index for 768 dimensions
CREATE INDEX idx_langmem_embedding
ON langmem_memories
USING hnsw (embedding vector_cosine_ops);

-- Step 5: Drop ALL existing match_memories functions (may have multiple signatures)
DROP FUNCTION IF EXISTS match_memories(vector(3072), INT, UUID);
DROP FUNCTION IF EXISTS match_memories(vector(3072), UUID, INT);
DROP FUNCTION IF EXISTS match_memories(vector(3072), INT);
DROP FUNCTION IF EXISTS match_memories(vector(768), INT, UUID);
DROP FUNCTION IF EXISTS match_memories(vector(768), UUID, INT);
DROP FUNCTION IF EXISTS match_memories(vector(768), INT);

-- Recreate match_memories RPC with correct signature (no metadata column)
CREATE OR REPLACE FUNCTION match_memories(
  query_embedding vector(768),
  filter_user_id UUID,
  match_count INT DEFAULT 5
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
    (1 - (m.embedding <=> query_embedding)) AS similarity_score
  FROM langmem_memories m
  WHERE m.user_id = filter_user_id
    AND m.embedding IS NOT NULL
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Step 6: Grant permissions
GRANT EXECUTE ON FUNCTION match_memories TO authenticated;
GRANT EXECUTE ON FUNCTION match_memories TO service_role;

-- Step 7: Update column comment
COMMENT ON COLUMN langmem_memories.embedding IS 'Google Gemini text-embedding-004 vector (768 dim) for semantic search';

COMMIT;

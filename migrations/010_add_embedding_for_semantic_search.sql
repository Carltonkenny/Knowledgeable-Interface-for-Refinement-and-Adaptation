-- migrations/010_add_embedding_for_semantic_search.sql
-- ─────────────────────────────────────────────
-- Add pgvector embedding column for semantic search
--
-- RULES.md Compliance:
-- - Enables fast semantic search via cosine similarity
-- - Uses Gemini embeddings (3072 dimensions)
-- - Uses HNSW index (supports >2000 dimensions)
-- ─────────────────────────────────────────────

-- Step 1: Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add embedding column to langmem_memories
ALTER TABLE langmem_memories 
ADD COLUMN IF NOT EXISTS embedding vector(3072);

-- Step 3: Add HNSW index for FAST semantic search
-- HNSW supports >2000 dimensions (unlike IVFFlat which maxes at 2000)
-- This is slower to build but faster for queries
CREATE INDEX IF NOT EXISTS idx_langmem_embedding 
ON langmem_memories 
USING hnsw (embedding vector_cosine_ops);

-- Step 4: Add comment for documentation
COMMENT ON COLUMN langmem_memories.embedding IS 'Gemini embedding vector (3072 dim) for semantic search';

-- Step 5: Create helper function for semantic search
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
  metadata JSONB,
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
    m.metadata,
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

-- Done!
-- Usage example:
-- SELECT * FROM match_memories(
--   '[0.0051, 0.0033, ...]'::vector,  -- Your query embedding
--   5,                                  -- Return top 5 matches
--   'user-uuid-here'                   -- Filter by user (optional)
-- );

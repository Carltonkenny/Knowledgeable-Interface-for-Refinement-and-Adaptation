-- migrations/010_add_embedding_storage.sql
-- ─────────────────────────────────────────────
-- Add embedding column for storage (no index on Supabase free tier)
--
-- Supabase Free Tier Limitation:
-- - Max 200 dimensions for indexed vectors
-- - Gemini embeddings are 3072 dimensions
-- - Solution: Store without index, use exact search
-- ─────────────────────────────────────────────

-- Step 1: Add embedding column (no index)
ALTER TABLE langmem_memories 
ADD COLUMN IF NOT EXISTS embedding vector(3072);

-- Step 2: Add comment
COMMENT ON COLUMN langmem_memories.embedding IS 'Gemini embedding (3072 dim) - stored for future use';

-- Step 3: Create simple search function (exact, not indexed)
CREATE OR REPLACE FUNCTION match_memories_simple(
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
    (1 - (m.embedding <=> query_embedding)) AS similarity_score
  FROM langmem_memories m
  WHERE (filter_user_id IS NULL OR m.user_id = filter_user_id)
    AND m.embedding IS NOT NULL
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION match_memories_simple TO authenticated;

-- Verify
SELECT column_name, data_type, udt_name 
FROM information_schema.columns 
WHERE table_name = 'langmem_memories' 
  AND column_name = 'embedding';

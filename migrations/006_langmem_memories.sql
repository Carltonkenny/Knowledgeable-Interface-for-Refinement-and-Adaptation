-- migrations/006_langmem_memories.sql
-- ─────────────────────────────────────────────
-- LangMem Memories Table — Persistent memory storage
--
-- RULES.md Compliance:
-- - RLS enabled (user_id = auth.uid())
-- - Indexes for performance
-- - Stores prompt pairs with quality scores
-- ─────────────────────────────────────────────

-- Create langmem_memories table
CREATE TABLE IF NOT EXISTS langmem_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    improved_content TEXT,
    domain TEXT DEFAULT 'general',
    quality_score JSONB DEFAULT '{}',
    agents_used TEXT[] DEFAULT '{}',
    agents_skipped TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure user_id is valid
    CONSTRAINT valid_user_id CHECK (user_id IS NOT NULL)
);

-- Enable RLS
ALTER TABLE langmem_memories ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own memories
CREATE POLICY "users_select_own_memories" ON langmem_memories
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS Policy: Users can only insert their own memories
CREATE POLICY "users_insert_own_memories" ON langmem_memories
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can only update their own memories
CREATE POLICY "users_update_own_memories" ON langmem_memories
    FOR UPDATE
    USING (auth.uid() = user_id);

-- RLS Policy: Users can only delete their own memories
CREATE POLICY "users_delete_own_memories" ON langmem_memories
    FOR DELETE
    USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX idx_langmem_user_id ON langmem_memories(user_id);
CREATE INDEX idx_langmem_domain ON langmem_memories(domain);
CREATE INDEX idx_langmem_created_at ON langmem_memories(created_at DESC);
CREATE INDEX idx_langmem_quality ON langmem_memories USING GIN(quality_score);

-- Comment for documentation
COMMENT ON TABLE langmem_memories IS 'LangMem persistent memory storage for web app (RULES.md: surface isolation)';

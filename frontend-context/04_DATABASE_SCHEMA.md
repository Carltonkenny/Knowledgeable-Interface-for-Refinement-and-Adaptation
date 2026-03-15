# PromptForge v2.0 — Database Schema Reference

**Document Purpose:** Complete database schema documentation for understanding data models, relationships, and RLS policies.

**Database:** Supabase (PostgreSQL + pgvector)

---

## DATABASE OVERVIEW

### Tables (8 Total)

| Table | Purpose | RLS Policies |
|-------|---------|--------------|
| `requests` | Prompt pairs (raw → improved) | 5 |
| `conversations` | Full chat turns with classification | 5 |
| `agent_logs` | Agent analysis outputs | 4 |
| `prompt_history` | Historical prompts | 4 |
| `user_profiles` | User personalization (THE MOAT) | 5 |
| `langmem_memories` | Pipeline memory with embeddings | 5 |
| `chat_sessions` | Session management | 5 |
| `mcp_tokens` | Long-lived MCP JWT tokens | 5 |

**Total RLS Policies:** 38

---

## TABLE SCHEMAS

### requests

Stores raw prompt → improved prompt pairs with version control.

```sql
CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    raw_prompt TEXT NOT NULL,
    improved_prompt TEXT NOT NULL,
    session_id TEXT NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000',
    
    -- Quality & Analysis
    quality_score JSONB,
    domain_analysis JSONB,
    agents_used TEXT[],
    agents_skipped TEXT[],
    prompt_diff JSONB,
    
    -- Version Control (Phase 3 Auto-Versioning)
    version_id UUID NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    parent_version_id UUID REFERENCES requests(id),
    change_summary TEXT,
    is_production BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_requests_user_id ON requests(user_id);
CREATE INDEX idx_requests_session_id ON requests(session_id);
CREATE INDEX idx_requests_version_id ON requests(version_id);
CREATE INDEX idx_requests_created_at ON requests(created_at DESC);
```

**Usage:**
- `/refine` endpoint saves prompt pairs
- `/chat` endpoint saves prompt pairs (for NEW_PROMPT type)
- Version control: increments `version_number` within same session
- `is_production`: only latest version in session is marked production

---

### conversations

Full chat turns with message type classification.

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id TEXT NOT NULL,
    
    -- Message Content
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    message_type TEXT,
    improved_prompt TEXT,
    
    -- Clarification Loop
    pending_clarification BOOLEAN DEFAULT FALSE,
    clarification_key TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(session_id, created_at);
```

**Message Types:**
- `conversation`: Casual chat, greetings
- `new_prompt`: User wants new prompt engineered
- `followup`: User wants to modify previous prompt
- `clarification_question`: Kira asking for clarification
- `clarification_answer`: User answering clarification
- `prompt_improved`: Kira returning improved prompt

**Usage:**
- `/chat` endpoint saves both user and assistant turns
- Clarification loop: sets `pending_clarification` flag
- Session history: loaded for context in subsequent requests

---

### agent_logs

Stores each agent's analysis output, linked to request.

```sql
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    output JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agent_logs_request_id ON agent_logs(request_id);
CREATE INDEX idx_agent_logs_agent_name ON agent_logs(agent_name);
```

**Agent Names:**
- `intent_agent`
- `context_agent`
- `domain_agent`
- `prompt_engineer` (not logged, output in requests table)

**Usage:**
- `save_agent_logs()` bulk inserts after swarm completes
- Debugging: analyze agent behavior
- Analytics: track agent performance

---

### prompt_history

Historical prompts (legacy, kept for backward compatibility).

```sql
CREATE TABLE prompt_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id TEXT,
    raw_prompt TEXT NOT NULL,
    improved_prompt TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_prompt_history_user_id ON prompt_history(user_id);
CREATE INDEX idx_prompt_history_session_id ON prompt_history(session_id);
```

**Note:** Phase 2 standard uses `requests` table instead. This table is kept for backward compatibility.

---

### user_profiles

**THE MOAT** — User personalization data that improves over time.

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL,
    
    -- Domain & Expertise
    dominant_domains TEXT[],
    primary_use TEXT,
    audience TEXT,
    
    -- Tone & Style
    preferred_tone TEXT,
    ai_frustration TEXT,
    frustration_detail TEXT,
    
    -- Quality Tracking
    prompt_quality_trend TEXT,  -- 'improving' | 'stable' | 'declining'
    clarification_rate NUMERIC,
    domain_confidence NUMERIC DEFAULT 0.0,
    
    -- Patterns
    notable_patterns TEXT[],
    total_sessions INTEGER DEFAULT 0,
    
    -- Metadata
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `dominant_domains` | TEXT[] | User's most common domains (e.g., ["python", "creative_writing"]) |
| `primary_use` | TEXT | Main use case from onboarding |
| `audience` | TEXT | Target audience (technical, business, general, academic, creative) |
| `preferred_tone` | TEXT | Tone preference (direct, casual, technical, formal) |
| `ai_frustration` | TEXT | Main frustration (too_vague, too_wordy, too_brief, wrong_tone, repeats, misses_context) |
| `frustration_detail` | TEXT | Additional detail about frustration |
| `prompt_quality_trend` | TEXT | Quality trend over time |
| `clarification_rate` | NUMERIC | How often user needs clarification |
| `domain_confidence` | NUMERIC | System confidence in domain classification (0.0-1.0) |
| `notable_patterns` | TEXT[] | Observed patterns in user behavior |
| `total_sessions` | INTEGER | Total session count |

**Usage:**
- Onboarding: initial profile created
- Profile updater: updates every 5th interaction + 30min inactivity
- Kira orchestrator: reads for tone adaptation
- Prompt engineer: reads for style matching

---

### langmem_memories

**THE MOAT** — Pipeline memory with pgvector embeddings for semantic search.

```sql
CREATE TABLE langmem_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    
    -- Content
    content TEXT NOT NULL,
    improved_content TEXT,
    
    -- Classification
    domain TEXT,
    quality_score JSONB,
    
    -- Embeddings (pgvector)
    embedding VECTOR(3072),  -- Gemini gemini-embedding-001
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_langmem_memories_user_id ON langmem_memories(user_id);
CREATE INDEX idx_langmem_memories_domain ON langmem_memories(domain);

-- HNSW index for fast cosine similarity (required for 3072-dim embeddings)
CREATE INDEX idx_langmem_memories_embedding 
ON langmem_memories 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Usage:**
- Background write: after each session completes
- Semantic search: pgvector `<=>` operator for cosine similarity
- Style reference: prompt engineer reads user's best past prompts
- RAG pipeline: retrieve top 5 relevant memories per request

**Query Example:**
```sql
-- Semantic search for top 5 memories
SELECT
    id, content, improved_content, domain, quality_score,
    (1 - (embedding <=> $1::vector)) AS similarity_score
FROM langmem_memories
WHERE user_id = $2
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

---

### chat_sessions

Session management with soft delete support.

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    
    -- Metadata
    title TEXT DEFAULT 'New Chat',
    is_pinned BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    
    -- Activity Tracking
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_deleted_at ON chat_sessions(user_id, deleted_at);
CREATE INDEX idx_chat_sessions_last_activity ON chat_sessions(user_id, last_activity DESC);
```

**Usage:**
- Sidebar: lists active (non-deleted) sessions
- Soft delete: sets `deleted_at` instead of deleting
- Recycle bin: shows deleted sessions for restore/purge
- Activity tracking: `update_session_activity()` on every request

**Session Lifecycle:**
1. Create: on first message in new session
2. Update: `last_activity` on every request
3. Soft delete: user deletes session
4. Restore: user restores from recycle bin
5. Purge: permanent delete (user or system)

---

### mcp_tokens

Long-lived JWT tokens for MCP clients (Cursor, Claude Desktop).

```sql
CREATE TABLE mcp_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    
    -- Token
    token_hash TEXT NOT NULL,
    token_type TEXT DEFAULT 'mcp_access',
    
    -- Lifecycle
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_mcp_tokens_user_id ON mcp_tokens(user_id);
CREATE INDEX idx_mcp_tokens_token_hash ON mcp_tokens(token_hash);
```

**Usage:**
- MCP authentication: long-lived tokens (365 days)
- Revocable: admin can revoke without affecting web session
- Trust levels: 0 (cold), 1 (warm), 2 (tuned)

---

## ROW LEVEL SECURITY (RLS) POLICIES

### requests

```sql
-- Enable RLS
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;

-- Users can select their own data
CREATE POLICY users_select_own_requests ON requests
    FOR SELECT
    USING (user_id = auth.uid());

-- Users can insert their own data
CREATE POLICY users_insert_own_requests ON requests
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Users can update their own data
CREATE POLICY users_update_own_requests ON requests
    FOR UPDATE
    USING (user_id = auth.uid());

-- Users can delete their own data
CREATE POLICY users_delete_own_requests ON requests
    FOR DELETE
    USING (user_id = auth.uid());

-- Admin can manage all data
CREATE POLICY admin_manage_requests ON requests
    FOR ALL
    USING (auth.jwt()->>'role' = 'admin');
```

---

### conversations

```sql
-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Users can select their own data
CREATE POLICY users_select_own_conversations ON conversations
    FOR SELECT
    USING (user_id = auth.uid());

-- Users can insert their own data
CREATE POLICY users_insert_own_conversations ON conversations
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Users can update their own data
CREATE POLICY users_update_own_conversations ON conversations
    FOR UPDATE
    USING (user_id = auth.uid());

-- Users can delete their own data
CREATE POLICY users_delete_own_conversations ON conversations
    FOR DELETE
    USING (user_id = auth.uid());

-- Admin can manage all data
CREATE POLICY admin_manage_conversations ON conversations
    FOR ALL
    USING (auth.jwt()->>'role' = 'admin');
```

---

### user_profiles

```sql
-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can select their own profile
CREATE POLICY users_select_own_profiles ON user_profiles
    FOR SELECT
    USING (user_id = auth.uid());

-- Users can insert their own profile
CREATE POLICY users_insert_own_profiles ON user_profiles
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Users can update their own profile
CREATE POLICY users_update_own_profiles ON user_profiles
    FOR UPDATE
    USING (user_id = auth.uid());

-- Users can delete their own profile
CREATE POLICY users_delete_own_profiles ON user_profiles
    FOR DELETE
    USING (user_id = auth.uid());

-- Admin can manage all profiles
CREATE POLICY admin_manage_profiles ON user_profiles
    FOR ALL
    USING (auth.jwt()->>'role' = 'admin');
```

---

### langmem_memories

```sql
-- Enable RLS
ALTER TABLE langmem_memories ENABLE ROW LEVEL SECURITY;

-- Users can select their own memories
CREATE POLICY users_select_own_memories ON langmem_memories
    FOR SELECT
    USING (user_id = auth.uid());

-- Users can insert their own memories
CREATE POLICY users_insert_own_memories ON langmem_memories
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Users can update their own memories
CREATE POLICY users_update_own_memories ON langmem_memories
    FOR UPDATE
    USING (user_id = auth.uid());

-- Users can delete their own memories
CREATE POLICY users_delete_own_memories ON langmem_memories
    FOR DELETE
    USING (user_id = auth.uid());

-- Admin can manage all memories
CREATE POLICY admin_manage_memories ON langmem_memories
    FOR ALL
    USING (auth.jwt()->>'role' = 'admin');
```

---

### chat_sessions

```sql
-- Enable RLS
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- Users can select their own sessions
CREATE POLICY users_select_own_sessions ON chat_sessions
    FOR SELECT
    USING (user_id = auth.uid());

-- Users can insert their own sessions
CREATE POLICY users_insert_own_sessions ON chat_sessions
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Users can update their own sessions
CREATE POLICY users_update_own_sessions ON chat_sessions
    FOR UPDATE
    USING (user_id = auth.uid());

-- Users can delete their own sessions
CREATE POLICY users_delete_own_sessions ON chat_sessions
    FOR DELETE
    USING (user_id = auth.uid());

-- Admin can manage all sessions
CREATE POLICY admin_manage_sessions ON chat_sessions
    FOR ALL
    USING (auth.jwt()->>'role' = 'admin');
```

---

### agent_logs

```sql
-- Enable RLS
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Users can select their own logs (via request join)
CREATE POLICY users_select_own_agent_logs ON agent_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM requests
            WHERE requests.id = agent_logs.request_id
            AND requests.user_id = auth.uid()
        )
    );

-- System can insert logs
CREATE POLICY system_insert_agent_logs ON agent_logs
    FOR INSERT
    WITH CHECK (TRUE);

-- Users can delete their own logs (via request join)
CREATE POLICY users_delete_own_agent_logs ON agent_logs
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM requests
            WHERE requests.id = agent_logs.request_id
            AND requests.user_id = auth.uid()
        )
    );

-- Admin can manage all logs
CREATE POLICY admin_manage_agent_logs ON agent_logs
    FOR ALL
    USING (auth.jwt()->>'role' = 'admin');
```

---

### mcp_tokens

```sql
-- Enable RLS
ALTER TABLE mcp_tokens ENABLE ROW LEVEL SECURITY;

-- Users can select their own tokens
CREATE POLICY users_select_own_tokens ON mcp_tokens
    FOR SELECT
    USING (user_id = auth.uid());

-- Users can insert their own tokens
CREATE POLICY users_insert_own_tokens ON mcp_tokens
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Admin can revoke tokens
CREATE POLICY admin_revoke_tokens ON mcp_tokens
    FOR UPDATE
    USING (auth.jwt()->>'role' = 'admin')
    WITH CHECK (revoked = TRUE);

-- Users can delete their own tokens
CREATE POLICY users_delete_own_tokens ON mcp_tokens
    FOR DELETE
    USING (user_id = auth.uid());

-- Admin can manage all tokens
CREATE POLICY admin_manage_tokens ON mcp_tokens
    FOR ALL
    USING (auth.jwt()->>'role' = 'admin');
```

---

## DATABASE FUNCTIONS

### exec_sql (RPC for raw SQL)

Used by LangMem for pgvector similarity search.

```sql
-- Allows executing raw SQL with proper permissions
CREATE OR REPLACE FUNCTION exec_sql(sql TEXT)
RETURNS TABLE(result JSONB)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Execute SQL and return results
    -- Proper permissions and validation required
    RETURN QUERY EXECUTE sql;
END;
$$;
```

---

## MIGRATIONS

### Migration History

| Migration | Description | Tables |
|-----------|-------------|--------|
| 001-009 | Phase 1-2 tables + RLS | requests, conversations, agent_logs, prompt_history, user_profiles |
| 010 | LangMem embedding column | langmem_memories (VECTOR column) |
| 011 | User sessions table | user_sessions |
| 012 | Supermemory facts table | supermemory_facts |
| 013 | MCP tokens table | mcp_tokens |

---

## QUERY EXAMPLES

### Get User's Session History

```sql
SELECT
    c.id,
    c.role,
    c.message,
    c.message_type,
    c.improved_prompt,
    c.created_at
FROM conversations c
WHERE c.user_id = auth.uid()
  AND c.session_id = 'session-123'
ORDER BY c.created_at DESC
LIMIT 6;
```

### Get User's Profile

```sql
SELECT *
FROM user_profiles
WHERE user_id = auth.uid();
```

### Semantic Search (LangMem)

```sql
SELECT
    id,
    content,
    improved_content,
    domain,
    quality_score,
    (1 - (embedding <=> $1::vector)) AS similarity_score
FROM langmem_memories
WHERE user_id = $2
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

### Get Version History

```sql
SELECT
    id,
    raw_prompt,
    improved_prompt,
    version_number,
    change_summary,
    created_at
FROM requests
WHERE user_id = auth.uid()
  AND version_id = 'version-uuid'
ORDER BY version_number ASC;
```

### Get Active Sessions

```sql
SELECT *
FROM chat_sessions
WHERE user_id = auth.uid()
  AND deleted_at IS NULL
ORDER BY is_pinned DESC, last_activity DESC
LIMIT 20;
```

---

**End of Database Schema Reference**

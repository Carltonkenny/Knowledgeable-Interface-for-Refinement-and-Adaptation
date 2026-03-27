# PromptForge — Database Schema

**Supabase PostgreSQL schema with Row Level Security (RLS)**

---

## 📊 Tables Overview

| Table | Purpose | RLS |
|-------|---------|-----|
| `requests` | Prompt history | ✅ User isolation |
| `conversations` | Chat session turns | ✅ User isolation |
| `chat_sessions` | Session metadata | ✅ User isolation |
| `user_profiles` | User preferences | ✅ User isolation |
| `agent_logs` | Agent execution logs | ✅ User isolation |
| `langmem_memories` | Long-term memory | ✅ User isolation |
| `prompt_feedback` | Implicit feedback | ✅ User isolation |
| `mcp_tokens` | MCP auth tokens | ✅ User isolation |

---

## 🔐 Row Level Security (RLS)

All tables have RLS enabled with policies:

```sql
-- Example: requests table
CREATE POLICY "Users can view their own requests"
  ON requests FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own requests"
  ON requests FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

---

## 📋 Table Schemas

### `requests`

```sql
CREATE TABLE requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  raw_prompt text NOT NULL,
  improved_prompt text,
  quality_score jsonb,
  domain_analysis jsonb,
  session_id text,
  version_id uuid,
  version_number integer DEFAULT 1,
  created_at timestamptz DEFAULT now()
);
```

### `conversations`

```sql
CREATE TABLE conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  session_id text NOT NULL,
  role text NOT NULL,
  message text NOT NULL,
  message_type text NOT NULL,
  improved_prompt text,
  created_at timestamptz DEFAULT now()
);
```

### `chat_sessions`

```sql
CREATE TABLE chat_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  title text,
  is_pinned boolean DEFAULT false,
  is_favorite boolean DEFAULT false,
  deleted_at timestamptz,
  created_at timestamptz DEFAULT now(),
  last_activity timestamptz DEFAULT now()
);
```

### `user_profiles`

```sql
CREATE TABLE user_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) UNIQUE,
  primary_use text,
  audience text,
  ai_frustration text,
  preferred_tone text,
  prompt_quality_score float DEFAULT 0.5,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
```

---

## 🔧 Required Extensions

Enable in Supabase Dashboard → Database → Extensions:

- [ ] `pgvector` (for langmem_memories.embedding)
- [ ] `uuid-ossp` (for gen_random_uuid())

---

## 📈 Indexes

```sql
-- Performance indexes
CREATE INDEX idx_requests_user_id ON requests(user_id);
CREATE INDEX idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
```

---

**For questions, open an issue on GitHub.**

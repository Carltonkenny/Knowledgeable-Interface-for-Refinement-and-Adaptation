# Supabase Schema Checklist

## ✅ Required Tables for PromptForge v2.0

This document lists all database tables required by the application. Verify each table exists in your Supabase dashboard with the specified columns.

---

## 🔐 Auth Tables (Managed by Supabase)

These are automatically created by Supabase Auth - **DO NOT create manually**.

### `auth.users`
- ✅ `id` (uuid, primary key)
- ✅ `email` (text)
- ✅ `raw_user_meta_data` (jsonb) ← **Username stored here as `data.username`**
- ✅ `created_at` (timestamptz)

---

## 📊 Core Tables

### 1. `requests` (Prompt History)
```sql
CREATE TABLE IF NOT EXISTS requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  raw_prompt text NOT NULL,
  improved_prompt text,
  quality_score jsonb,
  domain_analysis jsonb,
  session_id text,
  version_id uuid,
  version_number integer DEFAULT 1,
  input_modality text,
  attachments jsonb,
  agents_used jsonb,
  agents_skipped jsonb,
  created_at timestamptz DEFAULT now()
);
```

**Required Columns:**
- [ ] `id` (uuid)
- [ ] `user_id` (uuid)
- [ ] `raw_prompt` (text)
- [ ] `improved_prompt` (text)
- [ ] `quality_score` (jsonb)
- [ ] `domain_analysis` (jsonb)
- [ ] `session_id` (text)
- [ ] `version_id` (uuid)
- [ ] `version_number` (integer)
- [ ] `created_at` (timestamptz)

---

### 2. `conversations` (Chat Sessions)
```sql
CREATE TABLE IF NOT EXISTS conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  session_id text NOT NULL,
  role text NOT NULL,
  message text NOT NULL,
  message_type text NOT NULL,
  improved_prompt text,
  memories_applied integer,
  latency_ms integer,
  created_at timestamptz DEFAULT now()
);
```

**Required Columns:**
- [ ] `id` (uuid)
- [ ] `user_id` (uuid)
- [ ] `session_id` (text)
- [ ] `role` (text)
- [ ] `message` (text)
- [ ] `message_type` (text)
- [ ] `improved_prompt` (text)
- [ ] `created_at` (timestamptz)

---

### 3. `chat_sessions` (Session Metadata)
```sql
CREATE TABLE IF NOT EXISTS chat_sessions (
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

**Required Columns:**
- [ ] `id` (uuid)
- [ ] `user_id` (uuid)
- [ ] `title` (text)
- [ ] `is_pinned` (boolean)
- [ ] `is_favorite` (boolean)
- [ ] `deleted_at` (timestamptz)
- [ ] `created_at` (timestamptz)
- [ ] `last_activity` (timestamptz)

---

### 4. `user_profiles`
```sql
CREATE TABLE IF NOT EXISTS user_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) UNIQUE,
  primary_use text,
  audience text,
  ai_frustration text,
  frustration_detail text,
  preferred_tone text,
  clarification_rate float,
  prompt_quality_score float DEFAULT 0.5,
  dominant_domains jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
```

**Required Columns:**
- [ ] `id` (uuid)
- [ ] `user_id` (uuid, unique)
- [ ] `primary_use` (text)
- [ ] `audience` (text)
- [ ] `ai_frustration` (text)
- [ ] `preferred_tone` (text)
- [ ] `prompt_quality_score` (float)
- [ ] `created_at` (timestamptz)
- [ ] `updated_at` (timestamptz)

---

### 5. `agent_logs`
```sql
CREATE TABLE IF NOT EXISTS agent_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  session_id text,
  request_id uuid REFERENCES requests(id),
  agent_name text NOT NULL,
  agent_type text,
  input jsonb,
  output jsonb,
  latency_ms integer,
  tokens_used jsonb,
  created_at timestamptz DEFAULT now()
);
```

**Required Columns:**
- [ ] `id` (uuid)
- [ ] `user_id` (uuid)
- [ ] `agent_name` (text)
- [ ] `output` (jsonb)
- [ ] `created_at` (timestamptz)

---

### 6. `langmem_memories` (Long-term Memory)
```sql
CREATE TABLE IF NOT EXISTS langmem_memories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  content text NOT NULL,
  domain text,
  quality_score jsonb,
  embedding vector(1536),
  created_at timestamptz DEFAULT now()
);
```

**Required Columns:**
- [ ] `id` (uuid)
- [ ] `user_id` (uuid)
- [ ] `content` (text)
- [ ] `domain` (text)
- [ ] `quality_score` (jsonb)
- [ ] `embedding` (vector) ← **Requires pgvector extension**
- [ ] `created_at` (timestamptz)

---

### 7. `prompt_feedback` (Implicit Feedback)
```sql
CREATE TABLE IF NOT EXISTS prompt_feedback (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  session_id text NOT NULL,
  prompt_id uuid REFERENCES requests(id),
  feedback_type text NOT NULL,
  edit_distance float,
  timestamp text,
  created_at timestamptz DEFAULT now()
);
```

**Required Columns:**
- [ ] `id` (uuid)
- [ ] `user_id` (uuid) ← **Can be NULL for anonymous feedback**
- [ ] `session_id` (text)
- [ ] `prompt_id` (uuid)
- [ ] `feedback_type` (text)
- [ ] `created_at` (timestamptz)

---

### 8. `mcp_tokens` (MCP Authentication)
```sql
CREATE TABLE IF NOT EXISTS mcp_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  token_hash text NOT NULL,
  token_type text DEFAULT 'bearer',
  expires_at timestamptz,
  revoked boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
```

**Required Columns:**
- [ ] `id` (uuid)
- [ ] `user_id` (uuid)
- [ ] `token_hash` (text)
- [ ] `expires_at` (timestamptz)
- [ ] `revoked` (boolean)
- [ ] `created_at` (timestamptz)

---

## 🔧 Required Extensions

Enable these in Supabase Dashboard → Database → Extensions:

- [ ] `pgvector` (for langmem_memories.embedding)
- [ ] `uuid-ossp` (for gen_random_uuid())

---

## 🔐 Row Level Security (RLS) Policies

All tables should have RLS enabled with policies like:

```sql
-- Example for requests table
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own requests"
  ON requests FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own requests"
  ON requests FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own requests"
  ON requests FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own requests"
  ON requests FOR DELETE
  USING (auth.uid() = user_id);
```

**Repeat similar policies for:**
- [ ] `conversations`
- [ ] `chat_sessions`
- [ ] `user_profiles`
- [ ] `agent_logs`
- [ ] `langmem_memories`
- [ ] `prompt_feedback`
- [ ] `mcp_tokens`

---

## 🧪 Quick Verification Script

Run this in Supabase SQL Editor to check all tables exist:

```sql
SELECT 
  table_name,
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = t.table_name AND column_name = 'user_id') 
    THEN '✓' 
    ELSE '✗' 
  END as has_user_id
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN (
    'requests', 'conversations', 'chat_sessions', 
    'user_profiles', 'agent_logs', 'langmem_memories',
    'prompt_feedback', 'mcp_tokens'
  )
ORDER BY table_name;
```

---

## 🚨 Common Issues & Fixes

### 1. `update_user_by_id() got an unexpected keyword argument 'user_id'`
**Fixed in code:** Now passes `user_id` as positional argument, not keyword.

### 2. `403 Forbidden on /feedback`
**Fixed in code:** Auth is now optional for feedback endpoint.

### 3. `relation "X" does not exist`
**Fix:** Create the missing table using the schemas above.

### 4. `permission denied for table X`
**Fix:** Enable RLS and create policies as shown above.

### 5. `type "vector" does not exist`
**Fix:** Enable pgvector extension in Supabase dashboard.

---

## 📋 Post-Migration Checklist

After verifying schema:

1. [ ] All 8 tables exist
2. [ ] All tables have `user_id` column
3. [ ] All tables have `created_at` column
4. [ ] pgvector extension enabled
5. [ ] RLS enabled on all tables
6. [ ] RLS policies created for SELECT/INSERT/UPDATE/DELETE
7. [ ] Test username update in Profile page
8. [ ] Test feedback (copy button) - no 403 errors
9. [ ] Test chat functionality
10. [ ] Check backend logs for database errors

---

**Last Updated:** 2026-03-24  
**Version:** 2.0.0-rc1

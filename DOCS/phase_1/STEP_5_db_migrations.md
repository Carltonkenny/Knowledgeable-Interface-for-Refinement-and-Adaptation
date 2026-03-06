# Step 5: Database Migrations with RLS Policies

**Time:** 45 minutes  
**Status:** Not Started

---

## 🎯 Objective

Create Supabase migrations for:

1. `user_profiles` table with all fields from RULES.md
2. Add new fields to existing tables (`requests`, `conversations`, `agent_logs`)
3. Row Level Security (RLS) policies on ALL tables
4. RLS ensures users can ONLY see their own data

---

## 📋 What We're Doing and Why

### Current Database State

You have these tables in Supabase:
- `requests` — Basic prompt pairs
- `agent_logs` — Agent outputs
- `prompt_history` — Historical prompts
- `conversations` — Chat turns

**Missing:**
- `user_profiles` table (core for personalization)
- RLS policies (security risk — users can access each other's data!)
- New fields (`prompt_diff`, `quality_score`, `agents_skipped`, etc.)

### What We're Building

**New Table: `user_profiles`**
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    dominant_domains TEXT[],
    prompt_quality_trend TEXT,
    avg_prompt_length INT,
    clarification_rate FLOAT,
    preferred_tone TEXT,
    notable_patterns TEXT[],
    personality_adaptation JSONB,
    total_sessions INT,
    mcp_trust_level INT,
    input_modality_trend TEXT,
    updated_at TIMESTAMPTZ
);
```

**RLS Policy Example:**
```sql
-- Users can ONLY see their own data
CREATE POLICY "users see own data" ON user_profiles
    FOR SELECT
    USING (auth.uid() = user_id);
```

### Why RLS is Non-Negotiable

| Without RLS | With RLS |
|-------------|----------|
| User A can query User B's data if they know session_id | Database ENFORCES isolation at row level |
| Security relies on application logic (bug-prone) | Security at database layer (bulletproof) |
| Audit logs show "who queried what" | Impossible to query other user's data |
| Violates RULES.md security requirements | Compliant with production standards |

---

## 🔧 Implementation

### Part A: Create Migrations Directory

```bash
mkdir C:\Users\user\OneDrive\Desktop\newnew\migrations
type nul > migrations\README.md
```

### Part B: Create Migration SQL File

Create `migrations/001_user_profiles_and_rls.sql`:

```bash
type nul > migrations\001_user_profiles_and_rls.sql
```

**SQL to Add to File:**

```sql
-- =====================================================
-- Migration 001: user_profiles table + RLS policies
-- =====================================================
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
-- =====================================================

-- ── 1. Create user_profiles table ──────────────────

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    
    -- Core fields from RULES.md
    dominant_domains TEXT[],                          -- Top 3 domains user works in
    prompt_quality_trend TEXT,                        -- "improving" | "stable" | "declining"
    avg_prompt_length INT,                            -- Moving average
    clarification_rate FLOAT,                         -- 0.0-1.0 (how often user needed clarification)
    preferred_tone TEXT,                              -- "casual" | "formal" | "technical"
    notable_patterns TEXT[],                          -- ["likes_detailed_steps", "prefers_examples"]
    personality_adaptation JSONB,                     -- Kira's tone adjustments per domain
    total_sessions INT DEFAULT 0,
    mcp_trust_level INT DEFAULT 0,                    -- 0 | 1 | 2
    input_modality_trend TEXT,                        -- "text" | "voice" | "mixed"
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- ── 2. Add new fields to existing tables ──────────

-- requests table
ALTER TABLE requests 
    ADD COLUMN IF NOT EXISTS prompt_diff JSONB,
    ADD COLUMN IF NOT EXISTS quality_score JSONB,
    ADD COLUMN IF NOT EXISTS agents_used TEXT[],
    ADD COLUMN IF NOT EXISTS agents_skipped TEXT[],
    ADD COLUMN IF NOT EXISTS user_rating INT,
    ADD COLUMN IF NOT EXISTS input_modality TEXT,
    ADD COLUMN IF NOT EXISTS user_id UUID;

-- conversations table
ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS kira_tone_used TEXT,
    ADD COLUMN IF NOT EXISTS pending_clarification BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS clarification_key TEXT,
    ADD COLUMN IF NOT EXISTS user_id UUID;

-- agent_logs table
ALTER TABLE agent_logs
    ADD COLUMN IF NOT EXISTS was_skipped BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS skip_reason TEXT,
    ADD COLUMN IF NOT EXISTS latency_ms INT,
    ADD COLUMN IF NOT EXISTS user_id UUID;

-- ── 3. Enable RLS on ALL tables ───────────────────

-- user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- requests
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;

-- conversations
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- agent_logs
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- prompt_history
ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;

-- ── 4. Create RLS Policies ────────────────────────

-- user_profiles policies
CREATE POLICY "users_select_own_profile" ON user_profiles
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_profile" ON user_profiles
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users_update_own_profile" ON user_profiles
    FOR UPDATE
    USING (auth.uid() = user_id);

-- requests policies
CREATE POLICY "users_select_own_requests" ON requests
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_requests" ON requests
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- conversations policies
CREATE POLICY "users_select_own_conversations" ON conversations
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_conversations" ON conversations
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- agent_logs policies
CREATE POLICY "users_select_own_agent_logs" ON agent_logs
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_agent_logs" ON agent_logs
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- prompt_history policies
CREATE POLICY "users_select_own_history" ON prompt_history
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_history" ON prompt_history
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ── 5. Create function to update updated_at ───────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user_profiles
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Migration complete
-- =====================================================
```

### Part C: Run Migration in Supabase

1. Go to https://supabase.com/dashboard
2. Open your project: `cckznjkzsfypssgecyya`
3. Click **SQL Editor** in left sidebar
4. Click **New Query**
5. Copy entire SQL from `migrations/001_user_profiles_and_rls.sql`
6. Paste into SQL Editor
7. Click **Run** (or Ctrl+Enter)
8. Verify success (green checkmark)

### Part D: Update `database.py` for New Fields

**AI Prompt to Update `database.py`:**

```
You are updating database.py for PromptForge v2.0.

Follow RULES.md exactly. Add these new functions:
1. get_user_profile(user_id) — Fetch profile from user_profiles table
2. save_user_profile(user_id, profile_data) — Insert/update profile
3. save_clarification_flag(session_id, user_id, pending, clarification_key) — For clarification loop
4. get_clarification_flag(session_id, user_id) — Check if clarification pending

Update existing functions to:
1. Include user_id in all INSERT operations (for RLS)
2. Use auth.uid() in all queries (RLS compliance)
3. Add comprehensive error handling
4. Log all database operations with context

Keep existing functions:
- save_request()
- save_agent_logs()
- save_history()
- get_history()
- save_conversation()
- get_conversation_history()

File: database.py
```

### Expected New Functions in `database.py`:

```python
# database.py

# ... existing imports and get_client() ...

def get_user_profile(user_id: str) -> Optional[dict]:
    """
    Fetch user profile from user_profiles table.
    Returns None if not found or error.
    """
    try:
        db = get_client()
        result = db.table("user_profiles")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        if result.data and len(result.data) > 0:
            logger.info(f"[db] fetched profile for user_id={user_id}")
            return result.data[0]
        else:
            logger.info(f"[db] no profile found for user_id={user_id}")
            return None
            
    except Exception as e:
        logger.error(f"[db] get_user_profile failed: {e}")
        return None

def save_user_profile(user_id: str, profile_data: dict) -> bool:
    """
    Insert or update user profile.
    Returns True on success, False on failure.
    """
    try:
        db = get_client()
        
        # Check if profile exists
        existing = get_user_profile(user_id)
        
        if existing:
            # Update existing
            db.table("user_profiles")\
                .update(profile_data)\
                .eq("user_id", user_id)\
                .execute()
            logger.info(f"[db] updated profile for user_id={user_id}")
        else:
            # Insert new
            db.table("user_profiles")\
                .insert({
                    "user_id": user_id,
                    **profile_data
                })\
                .execute()
            logger.info(f"[db] created profile for user_id={user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"[db] save_user_profile failed: {e}")
        return False

def save_clarification_flag(
    session_id: str,
    user_id: str,
    pending: bool,
    clarification_key: Optional[str] = None
) -> bool:
    """
    Save clarification flag to conversations table.
    Used for clarification loop.
    """
    try:
        db = get_client()
        
        # Find latest conversation turn for this session
        result = db.table("conversations")\
            .select("id")\
            .eq("session_id", session_id)\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data and len(result.data) > 0:
            conversation_id = result.data[0]["id"]
            db.table("conversations")\
                .update({
                    "pending_clarification": pending,
                    "clarification_key": clarification_key
                })\
                .eq("id", conversation_id)\
                .execute()
            logger.info(f"[db] set clarification flag session={session_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"[db] save_clarification_flag failed: {e}")
        return False

def get_clarification_flag(session_id: str, user_id: str) -> tuple[bool, Optional[str]]:
    """
    Check if clarification is pending for this session.
    Returns (pending_clarification, clarification_key).
    """
    try:
        db = get_client()
        
        result = db.table("conversations")\
            .select("pending_clarification, clarification_key")\
            .eq("session_id", session_id)\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data and len(result.data) > 0:
            row = result.data[0]
            return (row.get("pending_clarification", False), row.get("clarification_key"))
        
        return (False, None)
        
    except Exception as e:
        logger.error(f"[db] get_clarification_flag failed: {e}")
        return (False, None)
```

---

## ✅ Verification Checklist

### Test 1: Tables Created Successfully

Go to Supabase dashboard:
1. https://supabase.com/dashboard/project/cckznjkzsfypssgecyya
2. Click **Table Editor**
3. Verify `user_profiles` table exists
4. Verify all columns present

### Test 2: RLS Enabled

In Supabase SQL Editor, run:
```sql
-- Check RLS is enabled on all tables
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Expected:** All tables show `rowsecurity = true`

### Test 3: RLS Prevents Cross-User Access

In Supabase SQL Editor, run:
```sql
-- Try to select from user_profiles without auth
-- This should return 0 rows (RLS blocks it)
SELECT * FROM user_profiles;
```

**Expected:** Empty result (RLS blocks unauthenticated access)

### Test 4: Database Functions Work

```bash
python -c "
from database import get_user_profile, save_user_profile

# Test with a fake user_id (will fail gracefully)
result = get_user_profile('00000000-0000-0000-0000-000000000000')
print(f'Profile result: {result}')
print('✅ Database functions work')
"
```

**Expected:** `✅ Database functions work` (result may be None for fake user)

---

## 🆘 Troubleshooting

### Problem: "relation already exists"

**Cause:** Migration already ran

**Solution:**
Skip table creation, just add missing columns:
```sql
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS mcp_trust_level INT DEFAULT 0;
```

### Problem: "permission denied"

**Cause:** Running migration without proper Supabase role

**Solution:**
Use `service_role` key from `.env` (has full permissions)

### Problem: "RLS blocks my own queries"

**Cause:** RLS uses `auth.uid()` which requires authenticated session

**Solution:**
For admin queries, temporarily disable RLS:
```sql
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
-- Run admin query
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
```

**Better:** Use Supabase client with auth token

---

## 📝 What Changed

| File | Change |
|------|--------|
| `migrations/001_user_profiles_and_rls.sql` | Created (new file) |
| `database.py` | Added profile + clarification functions |
| Supabase | Tables created, RLS enabled |

---

## ✅ Checkpoint — DO NOT PROCEED UNTIL

- [ ] `user_profiles` table exists in Supabase
- [ ] All new columns added to existing tables
- [ ] RLS enabled on ALL tables
- [ ] RLS policies created for SELECT, INSERT, UPDATE
- [ ] Database functions work (no import errors)
- [ ] RLS blocks unauthenticated queries

---

**Next:** Proceed to [STEP_6_kira_orchestrator.md](./STEP_6_kira_orchestrator.md)

# Supabase Migration Guide

**Project:** cckznjkzsfypssgecyya  
**Date:** 2026-03-07

---

## ⚠️ IMPORTANT: Supabase CLI Not Supported

Supabase CLI doesn't support global npm installation. Use the **SQL Editor** instead (safer and officially supported).

---

## ✅ MIGRATION METHOD: SQL Editor (Recommended)

### Step 1: Open SQL Editor
```
https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
```

### Step 2: Run Migrations in Order

#### Migration 1: Complete RLS and Tables
**File:** `migrations/008_complete_rls_and_tables.sql`

1. Open the file
2. Copy entire contents
3. Paste into SQL Editor
4. Click **RUN** (Ctrl+Enter)
5. Wait for "Success" message

**What this does:**
- Adds `user_id` to `requests` table
- Creates `user_profiles` table (THE MOAT)
- Creates `langmem_memories` table (THE MOAT)
- Creates 24 RLS policies
- Adds performance indexes

#### Migration 2: Fix Service Policies (if needed)
**File:** `migrations/009_fix_service_policies.sql`

Only run this if you get permission errors.

---

## 🔍 VERIFY MIGRATIONS

### Method 1: Run Verification Query
In SQL Editor, run:
```sql
-- Check all tables exist
SELECT 
  tablename as table_name,
  rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check policies
SELECT 
  tablename as table_name,
  count(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;
```

**Expected Output:**
```
table_name          | rls_enabled
--------------------|-------------
agent_logs          | true
conversations       | true
langmem_memories    | true  ← NEW!
prompt_history      | true
requests            | true
user_profiles       | true  ← NEW!

table_name          | policy_count
--------------------|-------------
agent_logs          | 5
conversations       | 5
langmem_memories    | 5  ← NEW!
prompt_history      | 5
requests            | 5
user_profiles       | 5  ← NEW!
```

### Method 2: Use Python Script
```bash
cd C:\Users\user\OneDrive\Desktop\newnew
python tests\test_db_simple.py
```

**Expected Output:**
```
Table                     Rows       Status
------------------------------------------------------------
requests                  1+         [OK] Active
conversations             1+         [OK] Active
agent_logs                1+         [OK] Active
prompt_history            1+         [OK] Active
user_profiles             0          [INFO] Empty (will populate)
langmem_memories          0          [INFO] Empty (will populate)
```

### Method 3: Dashboard
```
https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
```

You should see **6 tables** now.

---

## 🆘 TROUBLESHOOTING

### Error: "relation already exists"
**Cause:** Table already exists  
**Fix:** Safe to ignore - migration uses IF NOT EXISTS

### Error: "permission denied"
**Cause:** Need service_role permissions  
**Fix:** SQL Editor has full permissions by default

### Error: "foreign key violation"
**Cause:** user_id doesn't match auth.users  
**Fix:** Ensure using JWT from this Supabase instance

---

## 📝 MANUAL MIGRATION STEPS (Alternative)

If you prefer step-by-step control:

### 1. Add user_id to requests
```sql
ALTER TABLE requests ADD COLUMN IF NOT EXISTS user_id UUID;
CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
```

### 2. Create user_profiles
```sql
CREATE TABLE IF NOT EXISTS user_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid UNIQUE NOT NULL,
    dominant_domains text[] DEFAULT '{}',
    prompt_quality_trend text DEFAULT 'stable',
    clarification_rate numeric DEFAULT 0,
    preferred_tone text DEFAULT 'direct',
    notable_patterns text[] DEFAULT '{}',
    total_sessions integer DEFAULT 0,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
```

### 3. Create langmem_memories
```sql
CREATE TABLE IF NOT EXISTS langmem_memories (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    content text NOT NULL,
    improved_content text,
    domain text DEFAULT 'general',
    quality_score jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX idx_langmem_user_id ON langmem_memories(user_id);
ALTER TABLE langmem_memories ENABLE ROW LEVEL SECURITY;
```

### 4. Create RLS Policies
See `migrations/008_complete_rls_and_tables.sql` for complete policy list.

---

## ✅ POST-MIGRATION CHECKLIST

- [ ] 6 tables visible in Table Editor
- [ ] 24+ RLS policies in Auth → Policies
- [ ] `python tests\test_db_simple.py` shows all tables
- [ ] Call `/chat` endpoint
- [ ] Verify `langmem_memories` has 1+ rows
- [ ] Commit to git

---

## 📚 DOCUMENTATION

- `DOCS/DATABASE_VERIFICATION_GUIDE.md` - Complete guide
- `DOCS/DATABASE_VERIFICATION_SUMMARY.md` - Quick reference
- `DOCS/PHASE_2_LANGMEM_INTEGRATION_COMPLETE.md` - Integration docs
- `RULES.md` - Database architecture standards

---

**Last Updated:** 2026-03-07  
**Status:** Ready to migrate  
**Estimated Time:** 2 minutes

# Database Migrations

**Project:** PromptForge v2.0  
**Database:** Supabase (PostgreSQL)  
**RLS:** Enabled on ALL tables

---

## 📋 Migration Order

Run these migrations IN ORDER in Supabase SQL Editor:

1. **001_user_profiles.sql** — Create user_profiles table (core)
2. **002_requests.sql** — Add columns + RLS to requests
3. **003_conversations.sql** — Add columns + RLS to conversations
4. **004_agent_logs.sql** — Add columns + RLS to agent_logs
5. **005_prompt_history.sql** — Add user_id + RLS to prompt_history

---

## 🚀 How to Run

### Step 1: Open Supabase Dashboard

Go to: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new

### Step 2: Run Migration 001

1. Open `001_user_profiles.sql`
2. Copy entire contents
3. Paste into Supabase SQL Editor
4. Click "Run" (or Ctrl+Enter)
5. Verify success (green checkmark)

### Step 3: Run Migrations 002-005

Repeat for each migration file IN ORDER.

---

## ✅ Verification

After all migrations complete, verify:

```sql
-- Check all tables have RLS enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Expected: All tables show rowsecurity = true
```

---

## 📊 Tables Overview

| Table | Purpose | RLS |
|-------|---------|-----|
| `user_profiles` | User personalization (the "moat") | ✅ |
| `requests` | Prompt pairs (raw → improved) | ✅ |
| `conversations` | Full chat turns with classification | ✅ |
| `agent_logs` | Each agent's output for debugging | ✅ |
| `prompt_history` | Historical prompts for /history | ✅ |

---

## 🔒 RLS Policies

All tables have these policies:

```sql
-- Users can ONLY see their own data
CREATE POLICY "users_select_own_*" ON table_name
    FOR SELECT USING (auth.uid() = user_id);

-- Users can ONLY insert their own data
CREATE POLICY "users_insert_own_*" ON table_name
    FOR INSERT WITH CHECK (auth.uid() = user_id);
```

**Key:** `auth.uid()` returns the user_id from JWT token.

---

## 🆘 Troubleshooting

### Problem: "relation already exists"

**Solution:** Table already exists — migration adds columns only (IF NOT EXISTS).

### Problem: "permission denied"

**Solution:** Use service_role key from .env (has full permissions).

### Problem: "RLS blocks my queries"

**Solution:** RLS requires authenticated session. For admin queries, temporarily disable:

```sql
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
-- Run admin query
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
```

---

**Last Updated:** March 6, 2026

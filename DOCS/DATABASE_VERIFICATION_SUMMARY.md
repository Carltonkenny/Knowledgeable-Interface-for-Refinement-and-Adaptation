# Database Verification Summary

**Date:** 2026-03-07  
**Status:** ✅ Operational Tables Working, ⚠️ 2 Tables Need Migration

---

## VERIFICATION RESULTS

### ✅ Working Tables (4/6)

| Table | Category | Rows | Status |
|-------|----------|------|--------|
| `requests` | OPERATIONAL | 1+ | ✅ Active - Storing prompt pairs |
| `conversations` | CONVERSATIONAL | 1+ | ✅ Active - Storing chat history |
| `agent_logs` | OPERATIONAL | 1+ | ✅ Active - Storing agent analysis |
| `prompt_history` | OPERATIONAL | 1+ | ✅ Active - Storing historical prompts |

### ⚠️ Tables Needing Migration (2/6)

| Table | Category | Status | Action Needed |
|-------|----------|--------|---------------|
| `user_profiles` | **CORE BUSINESS** (Moat) | ⚠️ Not migrated | Run `migrations/001_user_profiles.sql` |
| `langmem_memories` | **CORE BUSINESS** (Moat) | ⚠️ Not migrated | Run `migrations/006_langmem_memories.sql` |

---

## HOW TO VERIFY (3 Methods)

### Method 1: Python Script (Quick)
```bash
cd C:\Users\user\OneDrive\Desktop\newnew
python tests\test_db_simple.py
```

**Output shows:**
- Table existence
- Row counts
- Recent activity samples

---

### Method 2: Supabase Dashboard (Visual)

1. **Table Editor**
   ```
   https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
   ```
   - Click each table to see rows
   - Verify data appearing after API calls

2. **RLS Policies**
   ```
   https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/policies
   ```
   - Each table should have 4 policies
   - All policies should be ENABLED

3. **API Logs**
   ```
   https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/logs/explorer
   ```
   - See queries in real-time
   - Verify `user_id` filtering (RLS working)

---

### Method 3: SQL Queries (Direct)

Open SQL Editor:
```
https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
```

**Run these queries:**

#### 1. Check All Tables
```sql
SELECT 
  'requests' as table_name, count(*) as row_count FROM requests
UNION ALL
SELECT 'conversations', count(*) FROM conversations
UNION ALL
SELECT 'agent_logs', count(*) FROM agent_logs
UNION ALL
SELECT 'prompt_history', count(*) FROM prompt_history;
```

#### 2. Verify RLS
```sql
-- Should return 0 (can't access other users' data)
SELECT count(*) FROM requests
WHERE user_id != auth.uid();
```

#### 3. Recent Activity
```sql
SELECT 
  raw_prompt,
  improved_prompt,
  created_at
FROM requests
ORDER BY created_at DESC
LIMIT 5;
```

---

## DATA FLOW VERIFICATION

### After `/refine` Call
Expected data flow:
```
1. requests         → New row (raw → improved pair)
2. agent_logs       → 3 rows (intent, context, domain)
3. prompt_history   → New row (for /history endpoint)
```

### After `/chat` Call
Expected data flow:
```
1. conversations    → 2 rows (user + assistant)
2. requests         → If NEW_PROMPT classification
3. agent_logs       → If swarm ran
4. prompt_history   → If swarm ran
```

### Test It:
```bash
# Call the API
curl -X POST http://localhost:8000/refine ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": \"write a story\", \"session_id\": \"test\"}"

# Then verify
python tests\test_db_simple.py
```

---

## MIGRATIONS NEEDED

### Run These 2 Migrations:

#### 1. User Profiles Table
**File:** `migrations/001_user_profiles.sql`

**What it creates:**
- `user_profiles` table
- RLS policies (SELECT, INSERT, UPDATE, DELETE)
- Indexes for performance

**How to run:**
1. Open: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
2. Copy contents of `migrations/001_user_profiles.sql`
3. Paste and run
4. Verify: Table appears in editor

#### 2. LangMem Memories Table
**File:** `migrations/006_langmem_memories.sql`

**What it creates:**
- `langmem_memories` table
- RLS policies
- Indexes on user_id, domain, created_at

**How to run:**
1. Open: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
2. Copy contents of `migrations/006_langmem_memories.sql`
3. Paste and run
4. Verify: Table appears in editor

---

## DATA CATEGORIZATION (Senior Pro Level)

### Tier 1: CORE BUSINESS (The Moat) ⭐⭐⭐⭐⭐
**Tables:** `user_profiles`, `langmem_memories`

**Why Critical:**
- User's learning history
- Personalization data
- **Switching cost** (users can't leave without losing this)
- **Competitive advantage** (gets better with usage)

**Backup Strategy:**
- Export weekly
- Store separately
- Monitor growth daily

---

### Tier 2: OPERATIONAL ⭐⭐⭐⭐
**Tables:** `requests`, `agent_logs`, `prompt_history`

**Why Important:**
- Service delivery
- Quality analysis
- Debugging
- Can be regenerated if lost

**Backup Strategy:**
- Export monthly
- Archive old data (90 days)

---

### Tier 3: CONVERSATIONAL ⭐⭐⭐
**Tables:** `conversations`

**Why Useful:**
- Multi-turn context
- Classification history
- Clarification loop state

**Retention:**
- Keep last 50 turns per session
- Auto-cleanup recommended

---

## SECURITY VERIFICATION

### RLS Policies (Non-Negotiable)

Every table MUST have:
```sql
-- SELECT
CREATE POLICY "users_select_own_TABLE" ON TABLE_NAME
  FOR SELECT
  USING (auth.uid() = user_id);

-- INSERT
CREATE POLICY "users_insert_own_TABLE" ON TABLE_NAME
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- UPDATE
CREATE POLICY "users_update_own_TABLE" ON TABLE_NAME
  FOR UPDATE
  USING (auth.uid() = user_id);

-- DELETE
CREATE POLICY "users_delete_own_TABLE" ON TABLE_NAME
  FOR DELETE
  USING (auth.uid() = user_id);
```

**Verify in Dashboard:**
```
https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/policies
```

---

## MONITORING CHECKLIST

### Daily (2 minutes)
- [ ] Open Table Editor
- [ ] Check row counts increased
- [ ] No error logs in agent_logs

### Weekly (10 minutes)
- [ ] Review slow queries (Database → Logs)
- [ ] Check langmem_memories growth
- [ ] Verify user_profiles being updated

### Monthly (30 minutes)
- [ ] Audit RLS policies
- [ ] Export langmem_memories backup
- [ ] Review prompt_quality_trend distribution

---

## FILES CREATED

| File | Purpose |
|------|---------|
| `tests/test_db_simple.py` | Quick verification script |
| `DOCS/DATABASE_VERIFICATION_GUIDE.md` | Complete guide (Senior Pro level) |
| `DOCS/DATABASE_VERIFICATION_SUMMARY.md` | This file (quick reference) |

---

## NEXT STEPS

1. **Run Migrations** (5 minutes)
   - `migrations/001_user_profiles.sql`
   - `migrations/006_langmem_memories.sql`

2. **Verify Data Flow** (2 minutes)
   - Call `/refine` or `/chat`
   - Run `python tests\test_db_simple.py`

3. **Integrate Background Writes** (Phase 2 - 5 hours)
   - Add `write_to_langmem()` to `/chat`
   - Add `update_user_profile()` to `/chat`

---

**Quick Links:**
- Table Editor: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
- SQL Editor: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
- RLS Policies: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/policies
- API Logs: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/logs/explorer

---

**Last Updated:** 2026-03-07  
**Status:** 4/6 tables operational, 2 migrations pending

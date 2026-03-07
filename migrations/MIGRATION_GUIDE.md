# Database Migration - Complete Fix

**File:** `migrations/008_complete_rls_and_tables.sql`  
**Time:** ~30 seconds  
**Safety:** Uses IF NOT EXISTS - safe to run multiple times

---

## 🚀 HOW TO RUN (3 Steps)

### Step 1: Open SQL Editor
```
https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
```

### Step 2: Copy & Paste
1. Open: `migrations/008_complete_rls_and_tables.sql`
2. Copy **entire file**
3. Paste into Supabase SQL Editor

### Step 3: Run
Click **RUN** (or Ctrl+Enter)

---

## ✅ WHAT THIS DOES

| Action | Details |
|--------|---------|
| **1. Add user_id** | Adds `user_id` column to `requests` table |
| **2. Create user_profiles** | Table for user personalization (THE MOAT) |
| **3. Create langmem_memories** | Table for pipeline memory (THE MOAT) |
| **4. Create RLS policies** | 24 user-specific policies (6 tables × 4 operations) |
| **5. Add indexes** | Performance indexes on user_id, domain, created_at |

---

## 📊 EXPECTED RESULTS

### Tables Created
- ✅ `user_profiles` (THE MOAT)
- ✅ `langmem_memories` (THE MOAT)

### Columns Added
- ✅ `requests.user_id`

### RLS Policies Created (24 total)
- ✅ `users_select_own_*` (6 policies)
- ✅ `users_insert_own_*` (6 policies)
- ✅ `users_update_own_*` (6 policies)
- ✅ `users_delete_own_*` (6 policies)

---

## 🔍 VERIFICATION

After running, you should see in SQL Editor output:

```
table_name          | rls_enabled
--------------------|-------------
agent_logs          | true
conversations       | true
langmem_memories    | true
prompt_history      | true
requests            | true
user_profiles       | true

table_name          | policy_count
--------------------|-------------
agent_logs          | 5
conversations       | 5
langmem_memories    | 5
prompt_history      | 5
requests            | 5
user_profiles       | 5
```

*(5 policies per table = 1 service_full_access + 4 user policies)*

---

## 🧪 TEST IT

### 1. Run Verification Script
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
user_profiles             0          [INFO] Empty (will populate after usage)
langmem_memories          0          [INFO] Empty (will populate after usage)
```

### 2. Check in Dashboard
```
https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
```

You should now see **6 tables**:
1. ✅ `agent_logs`
2. ✅ `conversations`
3. ✅ `langmem_memories` ← NEW!
4. ✅ `prompt_history`
5. ✅ `requests`
6. ✅ `user_profiles` ← NEW!

### 3. Check RLS Policies
```
https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/policies
```

You should see **24+ policies** (4 user policies per table).

---

## 📝 WHAT'S NEXT

After migration completes:

### 1. Test API Call
```bash
# Call /refine endpoint
curl -X POST http://localhost:8000/refine ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": \"write a story\", \"session_id\": \"test123\"}"
```

### 2. Verify Data Flow
```bash
python tests\test_db_simple.py
```

### 3. Integrate Background Writes (Phase 2)
- Add `write_to_langmem()` to `/chat` endpoint
- Add `update_user_profile()` to `/chat` endpoint

---

## 🆘 TROUBLESHOOTING

### Error: "relation already exists"
**Cause:** Table already exists  
**Fix:** Safe to ignore - migration uses IF NOT EXISTS

### Error: "permission denied"
**Cause:** Need service_role key  
**Fix:** Ensure you're using the SQL Editor (has full permissions)

### Error: "foreign key violation"
**Cause:** user_id doesn't match auth.users  
**Fix:** Ensure you're using JWT from your Supabase instance

### Policies already exist
**Cause:** Migration run before  
**Fix:** Safe to ignore - migration drops and recreates

---

## 📚 RELATED FILES

| File | Purpose |
|------|---------|
| `migrations/008_complete_rls_and_tables.sql` | This migration |
| `tests/test_db_simple.py` | Verification script |
| `DOCS/DATABASE_VERIFICATION_GUIDE.md` | Complete guide |
| `DOCS/DATABASE_VERIFICATION_SUMMARY.md` | Quick reference |
| `DOCS/RULES.md` | Database architecture standards |

---

## 🔒 SECURITY NOTES

### RLS Policy Behavior
- **SELECT:** Users can ONLY see their own data (`auth.uid() = user_id`)
- **INSERT:** Users can ONLY insert their own data
- **UPDATE:** Users can ONLY update their own data
- **DELETE:** Users can ONLY delete their own data

### Service Role Key
- The `service_full_access` policy remains for backend operations
- Your API uses service_role key for writes
- JWT authentication provides `auth.uid()` for RLS

### RULES.md Compliance
- ✅ RLS enabled on ALL tables
- ✅ user_id filtering on all queries
- ✅ No hardcoded secrets
- ✅ Type hints on all functions
- ✅ Error handling everywhere

---

**Last Updated:** 2026-03-07  
**Migration Status:** Ready to run  
**Next:** Integrate LangMem + Profile Updater background writes

# Database Verification & Categorization Guide
**Senior Pro Level - PromptForge v2.0**

**Date:** 2026-03-07  
**Per:** RULES.md Database Architecture

---

## QUICK VERIFICATION (5 minutes)

### Step 1: Open Supabase Dashboard
```
https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
```

### Step 2: Check Tables Exist
You should see these 6 tables:
1. `user_profiles` - CORE BUSINESS (The Moat)
2. `requests` - OPERATIONAL
3. `conversations` - CONVERSATIONAL
4. `agent_logs` - OPERATIONAL
5. `prompt_history` - OPERATIONAL
6. `langmem_memories` - CORE BUSINESS (The Moat)

### Step 3: Verify RLS Policies
Go to: **Authentication → Policies**

Each table should have 4 policies:
- `users_select_own_*`
- `users_insert_own_*`
- `users_update_own_*`
- `users_delete_own_*`

---

## DATA CATEGORIZATION (SENIOR PRO LEVEL)

### Category 1: CORE BUSINESS DATA (The "Moat") ⭐⭐⭐⭐⭐

**Tables:** `langmem_memories`, `user_profiles`

**Purpose:** This is your competitive advantage. The system learns from each user's usage patterns and becomes more valuable over time.

**What Gets Stored:**

#### langmem_memories
| Column | Type | Purpose |
|--------|------|---------|
| id | UUID | Primary key |
| user_id | UUID | RLS isolation |
| content | TEXT | Original prompt |
| improved_content | TEXT | Engineered prompt |
| domain | TEXT | e.g., "python", "creative writing" |
| quality_score | JSONB | {specificity: 4, clarity: 5, actionability: 3} |
| agents_used | TEXT[] | Which agents ran |
| agents_skipped | TEXT[] | Which agents skipped + why |
| created_at | TIMESTAMPTZ | When stored |

#### user_profiles
| Column | Type | Purpose |
|--------|------|---------|
| id | UUID | Primary key |
| user_id | UUID | RLS isolation |
| dominant_domains | TEXT[] | Top 3 domains user works in |
| prompt_quality_trend | TEXT | "improving" | "stable" | "declining" |
| clarification_rate | FLOAT | How often user needs clarification |
| preferred_tone | TEXT | "casual" | "formal" | "technical" |
| notable_patterns | TEXT[] | User's recurring preferences |
| total_sessions | INT | Total usage count |
| updated_at | TIMESTAMPTZ | Last profile update |

**Business Value:**
- Switching cost for users (their learning history is HERE)
- Personalization improves with usage
- Quality trends show user improvement over time

---

### Category 2: OPERATIONAL DATA (Request Processing) ⭐⭐⭐⭐

**Tables:** `requests`, `agent_logs`, `prompt_history`

**Purpose:** Needed for service delivery, debugging, and quality analysis.

#### requests
| Column | Type | Purpose |
|--------|------|---------|
| id | UUID | Primary key |
| user_id | UUID | RLS isolation |
| session_id | UUID | Conversation session |
| raw_prompt | TEXT | User's original prompt |
| improved_prompt | TEXT | Engineered prompt |
| created_at | TIMESTAMPTZ | When processed |

**Sample Query:**
```sql
-- Find all requests for a user
SELECT raw_prompt, improved_prompt, created_at
FROM requests
WHERE user_id = 'YOUR_USER_ID'
ORDER BY created_at DESC
LIMIT 10;
```

#### agent_logs
| Column | Type | Purpose |
|--------|------|---------|
| id | UUID | Primary key |
| request_id | UUID | Links to requests |
| agent_name | TEXT | "intent_agent", "context_agent", etc. |
| output | JSONB | Full agent analysis output |
| created_at | TIMESTAMPTZ | When logged |

**Sample Agent Output (JSONB):**
```json
{
  "primary_intent": "create engaging narrative",
  "goal_clarity": "low",
  "missing_info": ["target audience", "tone", "length"]
}
```

#### prompt_history
| Column | Type | Purpose |
|--------|------|---------|
| id | UUID | Primary key |
| user_id | UUID | RLS isolation |
| session_id | UUID | Conversation session |
| raw_prompt | TEXT | Original prompt |
| improved_prompt | TEXT | Engineered prompt |
| created_at | TIMESTAMPTZ | When stored |

**Difference from `requests`:**
- `requests`: One-time prompt pairs (for /refine endpoint)
- `prompt_history`: Historical prompts (for /history endpoint retrieval)

---

### Category 3: CONVERSATIONAL DATA (Context & Memory) ⭐⭐⭐

**Table:** `conversations`

**Purpose:** Enables multi-turn conversations with context awareness.

#### conversations
| Column | Type | Purpose |
|--------|------|---------|
| id | UUID | Primary key |
| user_id | UUID | RLS isolation |
| session_id | UUID | Conversation session |
| role | TEXT | "user" or "assistant" |
| message | TEXT | The message content |
| message_type | TEXT | "conversation" | "new_prompt" | "followup" |
| improved_prompt | TEXT | If applicable |
| pending_clarification | BOOL | Clarification loop flag |
| clarification_key | TEXT | Which field being clarified |
| created_at | TIMESTAMPTZ | When stored |

**Sample Query:**
```sql
-- Get last 6 turns for conversation context
SELECT role, message, message_type, improved_prompt
FROM conversations
WHERE session_id = 'SESSION_ID'
  AND user_id = 'USER_ID'
ORDER BY created_at DESC
LIMIT 6;
```

---

### Category 4: SECURITY (Access Control) ⭐⭐⭐⭐⭐

**Mechanism:** Row Level Security (RLS) on ALL tables

**Policy Pattern (applied to every table):**
```sql
-- Users can SELECT only their own data
CREATE POLICY "users_select_own_requests" ON requests
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can INSERT only their own data
CREATE POLICY "users_insert_own_requests" ON requests
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can UPDATE only their own data
CREATE POLICY "users_update_own_requests" ON requests
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Users can DELETE only their own data
CREATE POLICY "users_delete_own_requests" ON requests
  FOR DELETE
  USING (auth.uid() = user_id);
```

**Why This Matters:**
- Even if someone knows a session_id, they can't access another user's data
- JWT token provides `auth.uid()` which is checked on every query
- Non-negotiable per RULES.md

---

## DATA FLOW ARCHITECTURE

```
User Request (via /chat or /refine)
    │
    ├─→ [1] Check Cache (Redis)
    │       └─→ HIT: Return cached result (instant)
    │       └─→ MISS: Continue to swarm
    │
    ├─→ [2] Load Context (parallel)
    │       ├─→ user_profiles (preferred tone, domains)
    │       ├─→ langmem_memories (top 5 relevant memories)
    │       └─→ conversations (last 6 turns)
    │
    ├─→ [3] Run Agent Swarm
    │       ├─→ Intent Agent → intent_analysis
    │       ├─→ Context Agent → context_analysis
    │       ├─→ Domain Agent → domain_analysis
    │       └─→ Prompt Engineer → improved_prompt
    │
    ├─→ [4] Save Operational Data
    │       ├─→ requests (prompt pair)
    │       ├─→ agent_logs (each agent's output)
    │       └─→ prompt_history (for /history endpoint)
    │
    ├─→ [5] Save Conversational Data
    │       └─→ conversations (both turns: user + assistant)
    │
    └─→ [6] Background Tasks (user NEVER waits)
            ├─→ write_to_langmem() → langmem_memories
            └─→ update_user_profile() → user_profiles (every 5th interaction)
```

---

## VERIFICATION CHECKLIST

### After Running /refine Endpoint
Check these tables for new data:
- [ ] `requests` - New row with raw → improved pair
- [ ] `agent_logs` - 3 rows (intent, context, domain agents)
- [ ] `prompt_history` - New row for history retrieval

### After Running /chat Endpoint
Check these tables for new data:
- [ ] `conversations` - 2 new rows (user message + assistant reply)
- [ ] `requests` - If NEW_PROMPT classification
- [ ] `agent_logs` - If swarm ran
- [ ] `prompt_history` - If swarm ran

### After 5+ Chat Interactions
Check these tables (Profile Updater should have run):
- [ ] `user_profiles` - Profile created/updated
- [ ] `langmem_memories` - Session memories stored

---

## SQL QUERIES FOR VERIFICATION

### 1. Check All Tables Have Data
```sql
-- Run in Supabase SQL Editor
SELECT 
  'user_profiles' as table_name, count(*) as row_count FROM user_profiles
UNION ALL
SELECT 'requests', count(*) FROM requests
UNION ALL
SELECT 'conversations', count(*) FROM conversations
UNION ALL
SELECT 'agent_logs', count(*) FROM agent_logs
UNION ALL
SELECT 'prompt_history', count(*) FROM prompt_history
UNION ALL
SELECT 'langmem_memories', count(*) FROM langmem_memories;
```

### 2. Find User's Complete History
```sql
-- Replace with actual user_id
SELECT 
  r.created_at,
  r.raw_prompt,
  r.improved_prompt,
  LENGTH(r.improved_prompt) - LENGTH(r.raw_prompt) as improvement_delta
FROM requests r
WHERE r.user_id = 'YOUR_USER_ID'
ORDER BY r.created_at DESC
LIMIT 20;
```

### 3. Check Agent Performance
```sql
-- Which agents run most often?
SELECT 
  agent_name,
  count(*) as execution_count,
  avg(jsonb_array_length(output->'relevant_patterns')) as avg_patterns_found
FROM agent_logs
GROUP BY agent_name
ORDER BY execution_count DESC;
```

### 4. Verify RLS Is Working
```sql
-- This should return 0 rows (can't access other users' data)
SELECT * FROM requests
WHERE user_id != auth.uid()
LIMIT 1;
```

### 5. Check LangMem Moat
```sql
-- Show user's learning progression
SELECT 
  domain,
  quality_score->>'overall' as quality,
  created_at
FROM langmem_memories
WHERE user_id = 'YOUR_USER_ID'
ORDER BY created_at DESC
LIMIT 10;
```

---

## MONITORING DASHBOARD

### Daily Checks (2 minutes)
1. Open Supabase Dashboard → Table Editor
2. Check row counts increased (anomaly detection)
3. Verify no error logs in `agent_logs`

### Weekly Checks (10 minutes)
1. Review slow queries: Dashboard → Database → Logs
2. Check `langmem_memories` growth (the moat!)
3. Verify `user_profiles` being updated

### Monthly Checks (30 minutes)
1. Audit RLS policies: Dashboard → Auth → Policies
2. Export `langmem_memories` backup (CSV)
3. Review `prompt_quality_trend` distribution

---

## BACKUP STRATEGY

### Critical Data (Backup Weekly)
- `langmem_memories` - THE MOAT (irreplaceable)
- `user_profiles` - Learning history

### Operational Data (Backup Monthly)
- `requests` - Can be regenerated
- `prompt_history` - Can be regenerated

### Ephemeral Data (No Backup Needed)
- `conversations` - Context only, not critical
- `agent_logs` - Debugging aid

### Backup Script (Run Weekly)
```bash
# Export critical tables
curl -sS \
  -H "Authorization: Bearer YOUR_SERVICE_ROLE_KEY" \
  -H "apikey: YOUR_SERVICE_ROLE_KEY" \
  "https://cckznjkzsfypssgecyya.supabase.co/rest/v1/langmem_memories?select=*" \
  > backup_langmem_$(date +%Y%m%d).json

curl -sS \
  -H "Authorization: Bearer YOUR_SERVICE_ROLE_KEY" \
  -H "apikey: YOUR_SERVICE_ROLE_KEY" \
  "https://cckznjkzsfypssgecyya.supabase.co/rest/v1/user_profiles?select=*" \
  > backup_profiles_$(date +%Y%m%d).json
```

---

## TROUBLESHOOTING

### Problem: "Table not found"
**Solution:** Run migrations in order:
1. Open: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
2. Run migrations 001-006 in order

### Problem: "RLS blocks my query"
**Solution:** Ensure you're querying with authenticated user:
```sql
-- Wrong (no user context)
SELECT * FROM requests;

-- Correct (RLS applies)
-- Use REST API with JWT token
curl -H "Authorization: Bearer YOUR_JWT" ...
```

### Problem: "langmem_memories is empty"
**Solution:** LangMem background write not integrated yet:
- This is Phase 2 remaining work
- Add `write_to_langmem()` to `/chat` endpoint as `BackgroundTasks`

### Problem: "user_profiles is empty"
**Solution:** Profile Updater not integrated yet:
- This is Phase 2 remaining work
- Add `update_user_profile()` to `/chat` endpoint as `BackgroundTasks`

---

## SENIOR PRO TIPS

### 1. Data Isolation is Non-Negotiable
> "Never trust session_id alone. Always filter by user_id via RLS."
> - RULES.md

### 2. The Moat is Your Competitive Advantage
> "LangMem + Profiles = switching cost. Users can't leave without losing their learning history."
> - Product Strategy

### 3. Background Writes for User Experience
> "User NEVER waits for database writes. All persistence is BackgroundTasks."
> - Performance Best Practice

### 4. Monitor Data Growth
> "Set up alerts for unusual table growth. Anomalies indicate bugs or abuse."
> - Operations

### 5. Document Every Schema Change
> "Migrations are code. Treat them with same rigor as application code."
> - Engineering Standards

---

**Last Updated:** 2026-03-07  
**Next:** Integrate LangMem + Profile Updater background writes

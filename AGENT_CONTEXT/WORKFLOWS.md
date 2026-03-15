# PromptForge Workflows — Operational Playbooks

**Purpose:** Step-by-step workflows for common development and operational tasks.  
**Audience:** AI agents and human developers.  
**Scope:** What to do, in what order, with what checks.

---

## WORKFLOW 1: Adding a New API Endpoint

### When to Use

- New feature requires backend API
- Existing endpoints don't cover the use case
- Feature is within approved scope (e.g., Phase 4 features)

### Pre-Conditions

- [ ] Feature is in scope (check implementation plan)
- [ ] Database schema supports feature (or migration planned)
- [ ] RULES.md reviewed (security requirements)

### Steps

#### Step 1: Define the Contract

**Create/Update:** `lib/types.ts` (frontend)

```typescript
// Define request/response types
export interface NewFeatureRequest {
  field1: string
  field2: number
}

export interface NewFeatureResponse {
  result: string
  metadata: object
}
```

**Why:** Type safety, frontend/backend contract clarity.

#### Step 2: Database Migration (if needed)

**Create:** `migrations/021_new_feature.sql`

```sql
BEGIN;

-- 1. Add column/table
ALTER TABLE user_profiles ADD COLUMN new_field TEXT;

-- 2. Add index (if queried)
CREATE INDEX idx_user_profiles_new_field ON user_profiles(new_field);

-- 3. Add RLS policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_update_own_new_field
ON user_profiles
FOR UPDATE
USING (auth.uid() = user_id);

COMMIT;
```

**Checklist:**
- [ ] RLS policies added
- [ ] Indexes for queried fields
- [ ] Backward compatible (nullable or default)
- [ ] Migration tested locally

#### Step 3: Backend Endpoint

**Update:** `api.py`

```python
class NewFeatureRequest(BaseModel):
    field1: str = Field(..., min_length=1, max_length=100)
    field2: int = Field(..., ge=1, le=100)

class NewFeatureResponse(BaseModel):
    result: str
    metadata: dict

@app.post("/new-feature")
async def new_feature_endpoint(
    req: NewFeatureRequest,
    user: User = Depends(get_current_user)
):
    """
    Brief description of what endpoint does.

    Args:
        req: Request object with validated fields
        user: Authenticated user from JWT

    Returns:
        NewFeatureResponse with result and metadata

    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 404 if resource not found
        HTTPException: 500 if internal error
    """
    logger.info(f"[api] /new-feature requested by user={user.user_id}")

    try:
        # 1. Validate business logic
        if not some_condition:
            raise HTTPException(status_code=400, detail="Invalid request")

        # 2. Database operation
        db = get_client()
        result = db.table("some_table").insert({
            "user_id": user.user_id,
            **req.dict()
        }).execute()

        # 3. Return response
        return NewFeatureResponse(
            result="success",
            metadata={"id": result.data[0]["id"]}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[api] /new-feature failed")
        raise HTTPException(status_code=500, detail=str(e))
```

**Checklist:**
- [ ] JWT authentication (`get_current_user`)
- [ ] Input validation (Pydantic + Field constraints)
- [ ] RLS (user_id filtered in all queries)
- [ ] Type hints (parameters + return)
- [ ] Docstring (purpose, params, returns, raises)
- [ ] Structured logging (`[api]` prefix)
- [ ] Error handling (try/except with re-raise)

#### Step 4: Frontend API Function

**Update:** `lib/api.ts`

```typescript
export async function apiNewFeature(
  req: NewFeatureRequest,
  token: string
): Promise<NewFeatureResponse> {
  if (ENV.USE_MOCKS) {
    await new Promise(r => setTimeout(r, 500))
    return { result: 'mocked', metadata: {} }
  }

  const res = await fetch(`${API_BASE}/new-feature`, {
    method: 'POST',
    headers: await authHeaders(token),
    body: JSON.stringify(req),
  })

  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}
```

**Checklist:**
- [ ] Mock support (for development)
- [ ] Auth headers (Bearer token)
- [ ] Error handling (ApiError on non-OK)
- [ ] Type safety (Promise<ResponseType>)

#### Step 5: Frontend Hook

**Create:** `features/newfeature/hooks/useNewFeature.ts`

```typescript
'use client'

import { useState, useCallback } from 'react'
import { apiNewFeature } from '@/lib/api'

export function useNewFeature(token: string | null) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async (req: NewFeatureRequest) => {
    if (!token) return null

    setIsLoading(true)
    setError(null)

    try {
      const result = await apiNewFeature(req, token)
      return result
    } catch (err: any) {
      console.error('New feature failed:', err)
      setError(err.message || 'Operation failed')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [token])

  return {
    execute,
    isLoading,
    error,
    clearError: () => setError(null)
  }
}
```

**Checklist:**
- [ ] Loading state
- [ ] Error state
- [ ] Token null check
- [ ] Error logging
- [ ] Cleanup (finally block)

#### Step 6: UI Component

**Create:** `features/newfeature/components/NewFeatureForm.tsx`

```typescript
'use client'

import { useState } from 'react'
import { useNewFeature } from '../hooks/useNewFeature'

interface NewFeatureFormProps {
  token: string | null
  onSuccess?: () => void
}

export function NewFeatureForm({ token, onSuccess }: NewFeatureFormProps) {
  const [field1, setField1] = useState('')
  const [field2, setField2] = useState(1)

  const { execute, isLoading, error } = useNewFeature(token)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      await execute({ field1, field2 })
      onSuccess?.()
    } catch (err) {
      // Error already shown by hook
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Processing...' : 'Submit'}
      </button>
      {error && <div className="error">{error}</div>}
    </form>
  )
}
```

**Checklist:**
- [ ] Controlled inputs
- [ ] Loading state (disable button)
- [ ] Error display
- [ ] Success callback

#### Step 7: Tests

**Create:** `testadvance/phaseX/test_new_feature.py`

```python
class TestNewFeature:
    def test_new_feature_success(self, auth_client):
        """New feature works with valid input"""
        response = auth_client.post("/new-feature", json={
            "field1": "test",
            "field2": 42
        })
        assert response.status_code == 200
        assert "result" in response.json()

    def test_new_feature_unauthorized(self, client):
        """New feature requires authentication"""
        response = client.post("/new-feature", json={
            "field1": "test",
            "field2": 42
        })
        assert response.status_code == 403

    def test_new_feature_validation(self, auth_client):
        """New feature validates input"""
        response = auth_client.post("/new-feature", json={
            "field1": "",  # Too short
            "field2": 42
        })
        assert response.status_code == 400
```

**Checklist:**
- [ ] Success case
- [ ] Unauthorized case
- [ ] Validation case
- [ ] Edge cases (max length, boundary values)

#### Step 8: Documentation

**Update:** `AGENT_CONTEXT/PROJECT_CONTEXT.md`

- Add endpoint to API section
- Update workflow if pattern changed
- Add to troubleshooting if common issues

---

## WORKFLOW 2: Debugging a Production Issue

### When to Use

- User reports bug
- Error in logs
- Unexpected behavior

### Pre-Conditions

- [ ] Error reproduced (or logs analyzed)
- [ ] Impact assessed (how many users affected)
- [ ] Rollback plan ready (if fix might break more)

### Steps

#### Step 1: Gather Context

**Questions to Answer:**
1. What is the exact error message?
2. When did it start?
3. How often does it occur?
4. Which users are affected?
5. What action triggers it?

**Sources:**
- Backend logs (`docker-compose logs -f api`)
- Frontend console (browser DevTools)
- User report (screenshots, steps to reproduce)
- Monitoring (error tracking service)

#### Step 2: Reproduce Locally

**Backend:**
```bash
# Run same version as production
docker-compose down
docker-compose pull
docker-compose up

# Test endpoint
curl -X POST http://localhost:8000/problematic-endpoint \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
```

**Frontend:**
```bash
cd promptforge-web
npm run dev

# Open browser, reproduce steps
```

**Checklist:**
- [ ] Error reproduced locally?
- [ ] Same error message?
- [ ] Same conditions (input, user state)?

#### Step 3: Isolate the Cause

**Common Causes:**

**Database:**
- RLS policy blocking legitimate query
- Missing index causing timeout
- Migration not applied

**Authentication:**
- JWT expired
- Token format wrong
- User ID extraction failing

**Logic:**
- Edge case not handled (empty list, null value)
- Type mismatch (string vs number)
- Race condition (concurrent updates)

**External:**
- LLM API rate limited
- Redis connection lost
- Supabase downtime

**Debugging Techniques:**

1. **Add logging:**
```python
logger.info(f"[component] state={state}")
logger.debug(f"[component] variables={vars}")
```

2. **Check database:**
```sql
-- In Supabase SQL Editor
SELECT * FROM requests WHERE user_id = 'USER_ID' ORDER BY created_at DESC LIMIT 10;
```

3. **Test in isolation:**
```bash
# Test just the failing function
python -c "from module import function; print(function(test_input))"
```

#### Step 4: Implement Fix

**Rules:**
- Minimal change (fix only the bug, don't refactor)
- Add test for the bug
- Document the fix

**Example:**
```python
# BEFORE (bug: crashes if list is empty)
def calculate_average(scores: list) -> float:
    return sum(scores) / len(scores)

# AFTER (fix: handle empty list)
def calculate_average(scores: list) -> float:
    if not scores:
        return 0.0
    return sum(scores) / len(scores)
```

#### Step 5: Test Fix

**Local Testing:**
```bash
# Run affected tests
python -m pytest tests/test_module.py -v

# Run all tests
python testadvance/run_all_tests.py
```

**Checklist:**
- [ ] Bug fixed (test passes)
- [ ] No regressions (other tests pass)
- [ ] Edge cases covered

#### Step 6: Deploy

**Docker:**
```bash
# Build new image
docker-compose build

# Deploy
docker-compose up -d

# Monitor logs
docker-compose logs -f api
```

**Verify:**
- [ ] Health check passes (`curl http://localhost:8000/health`)
- [ ] Error no longer in logs
- [ ] User confirms fix

#### Step 7: Post-Mortem

**Document:**
1. What was the bug?
2. What caused it?
3. How was it fixed?
4. How to prevent it in future?

**Update:**
- Tests (add regression test)
- Documentation (add to troubleshooting)
- Code review checklist (add check for similar issues)

---

## WORKFLOW 3: Database Migration

### When to Use

- Schema change needed (new table, column, index)
- RLS policy update
- Data migration (backfill, cleanup)

### Pre-Conditions

- [ ] Change tested locally
- [ ] Backward compatible (or downtime planned)
- [ ] Rollback script ready

### Steps

#### Step 1: Create Migration File

**Name:** `migrations/021_description.sql`

**Format:**
```sql
-- ============================================================
-- PromptForge v2.0 - Migration 021: Description
-- ============================================================
-- Purpose: What this migration does
-- Date: 2026-03-15
-- Author: Your name
-- ============================================================

BEGIN;

-- Migration SQL here

COMMIT;
```

#### Step 2: Write Migration SQL

**Table Creation:**
```sql
-- 1. Create table
CREATE TABLE IF NOT EXISTS new_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Add indexes
CREATE INDEX idx_new_table_user_id ON new_table(user_id);
CREATE INDEX idx_new_table_created_at ON new_table(created_at);

-- 3. Enable RLS
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

-- 4. Add RLS policies
CREATE POLICY users_select_own_new_table
ON new_table
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY users_insert_own_new_table
ON new_table
FOR INSERT
WITH CHECK (auth.uid() = user_id);
```

**Column Addition:**
```sql
-- 1. Add column (nullable or with default)
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS new_column TEXT DEFAULT '';

-- 2. Add index (if queried)
CREATE INDEX IF NOT EXISTS idx_user_profiles_new_column
ON user_profiles(new_column);

-- 3. Update existing rows (if needed)
UPDATE user_profiles SET new_column = 'default' WHERE new_column IS NULL;
```

**Checklist:**
- [ ] RLS policies added
- [ ] Indexes for queried fields
- [ ] Backward compatible
- [ ] Transaction (BEGIN/COMMIT)

#### Step 3: Test Migration Locally

**Apply:**
```bash
# Connect to Supabase
psql $SUPABASE_URL

# Run migration
\i migrations/021_description.sql
```

**Verify:**
```sql
-- Check table exists
SELECT table_name FROM information_schema.tables
WHERE table_name = 'new_table';

-- Check RLS enabled
SELECT tablename, rowsecurity FROM pg_tables
WHERE tablename = 'new_table';

-- Check policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies
WHERE tablename = 'new_table';

-- Test RLS (as test user)
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claims" TO '{"sub": "TEST_USER_ID"}';

SELECT * FROM new_table WHERE user_id = auth.uid();
```

#### Step 4: Apply to Production

**Supabase Dashboard:**
1. Go to SQL Editor
2. Paste migration SQL
3. Run
4. Verify success

**Command Line:**
```bash
# Using Supabase CLI
supabase db push migrations/021_description.sql
```

#### Step 5: Verify Production

**Checks:**
```sql
-- Table exists
SELECT COUNT(*) FROM new_table;

-- RLS working
SELECT * FROM pg_policies WHERE tablename = 'new_table';

-- Application works
curl http://localhost:8000/health
```

#### Step 6: Update Documentation

**Update:**
- `AGENT_CONTEXT/PROJECT_CONTEXT.md` (database schema section)
- `migrations/MIGRATION_GUIDE.md` (migration log)

---

## WORKFLOW 4: Performance Optimization

### When to Use

- Endpoint slow (>target latency)
- Database query slow (>100ms)
- User reports lag

### Pre-Conditions

- [ ] Baseline measured (current latency)
- [ ] Target defined (acceptable latency)
- [ ] Load test ready (simulate traffic)

### Steps

#### Step 1: Identify Bottleneck

**Tools:**

**Backend Profiling:**
```python
import time

start = time.time()
# ... code ...
logger.info(f"[perf] operation took {time.time() - start:.3f}s")
```

**Database Query Analysis:**
```sql
-- Enable query logging in Supabase
EXPLAIN ANALYZE
SELECT * FROM requests
WHERE user_id = auth.uid()
ORDER BY created_at DESC;
```

**Frontend Performance:**
```typescript
// Chrome DevTools → Performance tab
// Record user interaction, analyze flame chart
```

**Common Bottlenecks:**

1. **LLM Calls:**
   - Sequential instead of parallel
   - Too many tokens
   - Wrong model (full instead of fast)

2. **Database:**
   - Missing indexes
   - N+1 queries
   - No pagination

3. **Network:**
   - Large payloads
   - No compression
   - Multiple round trips

4. **Frontend:**
   - Unnecessary re-renders
   - Large component tree
   - Unoptimized images

#### Step 2: Optimize LLM Calls

**Parallel Execution:**
```python
# BEFORE (sequential)
result1 = llm.invoke(prompt1)
result2 = llm.invoke(prompt2)
result3 = llm.invoke(prompt3)

# AFTER (parallel)
results = await asyncio.gather(
    llm.invoke(prompt1),
    llm.invoke(prompt2),
    llm.invoke(prompt3)
)
```

**Reduce Tokens:**
```python
# BEFORE (verbose)
prompt = f"""You are an expert assistant. Please analyze the following
text carefully and provide insights about the user's intent, context,
and any other relevant information that might be useful..."""

# AFTER (concise)
prompt = f"""Analyze: {text}. Return: {{intent, context}}."""
```

**Use Fast Model:**
```python
# Analysis agents → fast model (400 tokens)
llm = get_fast_llm()

# Prompt engineer → full model (2048 tokens)
llm = get_llm()
```

#### Step 3: Optimize Database

**Add Indexes:**
```sql
-- Slow query
SELECT * FROM requests WHERE user_id = 'UUID' ORDER BY created_at DESC;

-- Add index
CREATE INDEX idx_requests_user_created
ON requests(user_id, created_at DESC);
```

**Reduce Queries:**
```python
# BEFORE (N+1)
for request in requests:
    profile = get_user_profile(request.user_id)

# AFTER (batch)
user_ids = [r.user_id for r in requests]
profiles = get_user_profiles_batch(user_ids)
```

**Use pgvector:**
```python
# BEFORE (Python similarity)
memories = get_all_memories(user_id)
similar = cosine_similarity(query_embedding, memories)

# AFTER (database-side)
result = db.rpc("exec_sql", {
    "sql": f"""
        SELECT *, (1 - (embedding <=> '{embedding}')) AS similarity
        FROM langmem_memories
        WHERE user_id = auth.uid()
        ORDER BY embedding <=> '{embedding}'
        LIMIT 5
    """
})
```

#### Step 4: Optimize Frontend

**Memoization:**
```typescript
// BEFORE (re-calculates every render)
const filtered = items.filter(item => item.active)

// AFTER (memoized)
const filtered = useMemo(
  () => items.filter(item => item.active),
  [items]
)
```

**Debouncing:**
```typescript
// BEFORE (API call on every keystroke)
useEffect(() => {
  apiSearch(query)
}, [query])

// AFTER (debounced 300ms)
useEffect(() => {
  const timer = setTimeout(() => apiSearch(query), 300)
  return () => clearTimeout(timer)
}, [query])
```

**Lazy Loading:**
```typescript
// BEFORE (load all components)
import { HeavyComponent } from './HeavyComponent'

// AFTER (load on demand)
const HeavyComponent = lazy(() => import('./HeavyComponent'))
```

#### Step 5: Verify Improvement

**Measure:**
```bash
# Before
curl -w "@curl-format.txt" http://localhost:8000/endpoint

# After
curl -w "@curl-format.txt" http://localhost:8000/endpoint
```

**Target:**
- Cache hit: <100ms
- CONVERSATION: 2-3s
- NEW_PROMPT: 3-5s
- LangMem search: <500ms

#### Step 6: Document

**Update:**
- Performance section in `PROJECT_CONTEXT.md`
- Add to troubleshooting if common issue

---

## WORKFLOW 5: Security Review

### When to Use

- Before production deployment
- After adding new endpoint
- After security rule change

### Pre-Conditions

- [ ] RULES.md reviewed
- [ ] Security checklist ready
- [ ] Penetration test plan

### Steps

#### Step 1: Authentication Review

**Checklist:**
- [ ] All endpoints except /health require JWT
- [ ] JWT validation uses Supabase client
- [ ] Expired tokens rejected
- [ ] Invalid tokens rejected
- [ ] User ID extracted correctly from JWT

**Test:**
```bash
# Without token (should fail)
curl http://localhost:8000/endpoint
# Expected: 403 Forbidden

# With expired token (should fail)
curl -H "Authorization: Bearer EXPIRED_TOKEN" http://localhost:8000/endpoint
# Expected: 403 Forbidden

# With valid token (should succeed)
curl -H "Authorization: Bearer VALID_TOKEN" http://localhost:8000/endpoint
# Expected: 200 OK
```

#### Step 2: Authorization Review (RLS)

**Checklist:**
- [ ] All tables have RLS enabled
- [ ] Policies for SELECT, INSERT, UPDATE, DELETE
- [ ] User can only access own data
- [ ] No policies with `public` access (except /health)

**Test:**
```sql
-- Test as different user
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claims" TO '{"sub": "USER_A_ID"}';

-- Try to access User B's data
SELECT * FROM requests WHERE user_id = 'USER_B_ID';
-- Expected: Empty result (RLS blocks)
```

#### Step 3: Input Validation Review

**Checklist:**
- [ ] All inputs validated (Pydantic + Field)
- [ ] Length limits enforced (min, max)
- [ ] Type validation (string, number, boolean)
- [ ] Range validation (ge, le for numbers)
- [ ] Pattern validation (regex for email, etc.)

**Test:**
```bash
# Too short
curl -X POST http://localhost:8000/endpoint \
  -H "Content-Type: application/json" \
  -d '{"prompt": "abc"}'
# Expected: 400 Bad Request

# Too long (2001 chars)
curl -X POST http://localhost:8000/endpoint \
  -H "Content-Type: application/json" \
  -d '{"prompt": "'$(python -c "print('a'*2001)")'"}'
# Expected: 400 Bad Request
```

#### Step 4: Rate Limiting Review

**Checklist:**
- [ ] Rate limiting middleware enabled
- [ ] Per-user rate limit (100 req/hour)
- [ ] Returns 429 when exceeded
- [ ] Health endpoint exempt

**Test:**
```bash
# Send 101 requests rapidly
for i in {1..101}; do
  curl -H "Authorization: Bearer TOKEN" http://localhost:8000/endpoint
done

# 101st request should fail
# Expected: 429 Too Many Requests
```

#### Step 5: CORS Review

**Checklist:**
- [ ] No wildcard origins (`*`)
- [ ] Specific domains listed
- [ ] Credentials allowed (for cookies)
- [ ] Methods restricted (GET, POST, etc.)

**Test:**
```bash
# From allowed origin
curl -H "Origin: http://localhost:3000" http://localhost:8000/endpoint
# Expected: CORS headers present

# From disallowed origin
curl -H "Origin: http://evil.com" http://localhost:8000/endpoint
# Expected: CORS headers missing/rejected
```

#### Step 6: Data Sanitization Review

**Checklist:**
- [ ] User input sanitized (remove injection attempts)
- [ ] Output encoded (prevent XSS)
- [ ] File uploads validated (MIME type, size)
- [ ] SQL parameters bound (no string interpolation)

**Test:**
```python
# SQL injection attempt
prompt = "'; DROP TABLE requests; --"
result = process_prompt(prompt)
# Expected: Treated as string, not SQL

# XSS attempt
prompt = "<script>alert('xss')</script>"
result = process_prompt(prompt)
# Expected: Sanitized/encoded
```

#### Step 7: Secrets Management Review

**Checklist:**
- [ ] No secrets in code (all from .env)
- [ ] .env not committed to git
- [ ] .env.example committed (with placeholder values)
- [ ] Secrets rotated periodically

**Test:**
```bash
# Check for hardcoded secrets
grep -r "sk-" . --exclude-dir=node_modules
grep -r "api_key" . --exclude-dir=node_modules
# Expected: No results (or only in .env.example)
```

#### Step 8: Document

**Update:**
- Security section in `PROJECT_CONTEXT.md`
- Add failed tests to regression suite

---

## WORKFLOW 6: Code Review

### When to Use

- Before merging PR
- After implementing feature
- When reviewing AI agent output

### Pre-Conditions

- [ ] Code compiles (no syntax errors)
- [ ] Tests pass locally
- [ ] Linting passes

### Steps

#### Step 1: Architecture Review

**Questions:**
1. Does this follow existing patterns?
2. Is the component focused (single responsibility)?
3. Are dependencies minimal?
4. Is the abstraction level appropriate?

**Red Flags:**
- God class (does everything)
- Circular imports
- Tight coupling
- Premature optimization

#### Step 2: Code Quality Review

**Checklist:**
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] Error handling (try/except)
- [ ] Logging (structured, appropriate level)
- [ ] No code duplication (DRY)
- [ ] Clear variable names
- [ ] Comments explain WHY, not WHAT

**Example:**
```python
# BAD (no type hints, no docstring)
def process(data):
    result = []
    for item in data:
        if item.valid:
            result.append(transform(item))
    return result

# GOOD (type hints, docstring, clear)
def process_valid_items(data: List[Item]) -> List[TransformedItem]:
    """
    Filters and transforms valid items.

    Args:
        data: List of items to process

    Returns:
        List of transformed valid items

    Example:
        result = process_valid_items([Item(valid=True), Item(valid=False)])
        # Returns: [transformed_item]
    """
    return [transform(item) for item in data if item.valid]
```

#### Step 3: Security Review

**Checklist:**
- [ ] Authentication required
- [ ] Authorization enforced (RLS)
- [ ] Input validated
- [ ] Output sanitized
- [ ] No secrets in code
- [ ] Rate limiting applied

#### Step 4: Performance Review

**Checklist:**
- [ ] No N+1 queries
- [ ] Indexes used
- [ ] Caching applied (where appropriate)
- [ ] Parallel execution (where possible)
- [ ] Memory efficient (no leaks)

#### Step 5: Testing Review

**Checklist:**
- [ ] Unit tests for logic
- [ ] Integration tests for endpoints
- [ ] Edge cases covered
- [ ] Error cases tested
- [ ] Tests are deterministic (no flakiness)

#### Step 6: Documentation Review

**Checklist:**
- [ ] README updated (if user-facing change)
- [ ] API docs updated (new endpoints)
- [ ] Type definitions updated
- [ ] Examples provided (for complex logic)

#### Step 7: Final Approval

**Decision:**
- ✅ Approve (merge ready)
- ⚠️ Approve with comments (minor fixes, merge ok)
- ❌ Request changes (must fix before merge)

**Comment Format:**
```
[FILE:LINE] Suggestion:
"Consider using get_fast_llm() here for better performance."

[FILE:LINE] Question:
"Why is this check necessary? Can it be removed?"

[FILE:LINE] Required:
"Add error handling for database connection failure."
```

---

**Last Updated:** 2026-03-15  
**Version:** 1.0  
**Status:** Active

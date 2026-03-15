# PromptForge v2.0 — Quick Reference Guide

**Purpose:** Fast lookup for common tasks, patterns, and decisions.  
**Audience:** AI agents and developers.  
**Use:** Keep this open while working.

---

## 🚀 QUICK START

### First Time Setup

```bash
# 1. Clone and enter project
cd C:\Users\user\OneDrive\Desktop\newnew

# 2. Copy environment template
copy .env.example .env

# 3. Fill in .env with your keys
# Required: POLLINATIONS_API_KEY, SUPABASE_URL, SUPABASE_KEY, REDIS_URL, GEMINI_API_KEY

# 4. Install dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 5. Start backend
uvicorn api:app --reload --port 8000

# 6. Start frontend (new terminal)
cd promptforge-web
npm install
npm run dev

# 7. Access
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Swagger: http://localhost:8000/docs
```

### Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"2.0.0"}
```

---

## 📁 FILE LOCATIONS

### Backend

| Task | File |
|------|------|
| Add API endpoint | `api.py` |
| Add agent | `agents/*.py` |
| Change workflow | `graph/workflow.py` |
| Database operations | `database.py` |
| Authentication | `auth.py` |
| LLM configuration | `config.py` |
| Caching | `utils.py` |
| Memory (LangMem) | `memory/langmem.py` |
| Memory (Supermemory) | `memory/supermemory.py` |
| Profile updates | `memory/profile_updater.py` |
| Rate limiting | `middleware/rate_limiter.py` |
| File uploads | `multimodal/files.py` |
| Image processing | `multimodal/image.py` |
| Voice transcription | `multimodal/transcribe.py` |
| Database migrations | `migrations/*.sql` |

### Frontend

| Task | File |
|------|------|
| API calls | `lib/api.ts` |
| Types | `lib/types.ts` |
| Auth | `lib/auth.ts` |
| Error handling | `lib/errors.ts` |
| Streaming | `lib/stream.ts` |
| Chat feature | `features/chat/*` |
| History feature | `features/history/*` |
| Profile feature | `features/profile/*` |
| Onboarding | `features/onboarding/*` |
| Shared components | `components/*` |

---

## 🔑 ENVIRONMENT VARIABLES

### Required

```env
# LLM Provider (Pollinations.ai)
POLLINATIONS_API_KEY=your_api_key
POLLINATIONS_BASE_URL=https://gen.pollinations.ai/v1
POLLINATIONS_MODEL_FULL=openai
POLLINATIONS_MODEL_FAST=nova

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Redis (Caching)
REDIS_URL=redis://localhost:6379

# Embeddings (Google Gemini)
GEMINI_API_KEY=your_gemini_api_key
```

### Optional

```env
# Alternative LLM (Groq)
GROQ_API_KEY=your_groq_api_key

# Frontend URLs (CORS)
FRONTEND_URLS=http://localhost:3000,http://localhost:9000
```

---

## 📊 DATABASE SCHEMA

### Tables Overview

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `requests` | Prompt pairs | `raw_prompt`, `improved_prompt`, `version_id` |
| `conversations` | Chat history | `message`, `message_type`, `pending_clarification` |
| `agent_logs` | Agent outputs | `agent_name`, `output` |
| `chat_sessions` | Session metadata | `title`, `is_pinned`, `is_favorite` |
| `user_profiles` | User preferences | `dominant_domains`, `preferred_tone` |
| `langmem_memories` | Pipeline memory | `embedding`, `quality_score`, `domain` |
| `user_sessions` | Activity tracking | `last_activity` |
| `mcp_tokens` | MCP JWT tokens | `token_hash`, `expires_at`, `revoked` |

### RLS Pattern

All tables follow this pattern:

```sql
-- Users can SELECT their own data
CREATE POLICY users_select_own_table
ON table_name FOR SELECT
USING (auth.uid() = user_id);

-- Users can INSERT their own data
CREATE POLICY users_insert_own_table
ON table_name FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users can UPDATE their own data
CREATE POLICY users_update_own_table
ON table_name FOR UPDATE
USING (auth.uid() = user_id);

-- Users can DELETE their own data
CREATE POLICY users_delete_own_table
ON table_name FOR DELETE
USING (auth.uid() = user_id);
```

---

## 🤖 AGENT SWARM PATTERNS

### Agent Skip Conditions

| Agent | Skip When |
|-------|-----------|
| **Intent** | Simple direct command |
| **Context** | No conversation history |
| **Domain** | Profile confidence >85% |
| **Prompt Engineer** | **NEVER** (always runs) |

### Parallel Mode

```python
# In graph/workflow.py
PARALLEL_MODE = True  # Enable parallel execution

# LangGraph executes via Send() API
# [Intent + Context + Domain] run simultaneously
# Prompt Engineer waits for all to complete
```

### Agent Output Schema

```python
# Intent Agent
{
    "primary_intent": "the deep actual goal",
    "secondary_intents": ["supporting goals"],
    "goal_clarity": "low|medium|high",
    "missing_info": ["specific missing details"]
}

# Context Agent
{
    "skill_level": "beginner|intermediate|expert",
    "tone": "casual|formal|technical|creative",
    "constraints": ["real limitations"],
    "implicit_preferences": ["what user values"],
    "confidence": 0.0-1.0
}

# Domain Agent
{
    "primary_domain": "precise field name",
    "sub_domain": "specific discipline",
    "relevant_patterns": ["patterns to apply"],
    "complexity": "simple|moderate|complex",
    "confidence": 0.0-1.0
}

# Prompt Engineer
{
    "improved_prompt": "the rewritten prompt",
    "quality_score": {
        "specificity": 1-5,
        "clarity": 1-5,
        "actionability": 1-5,
        "overall": 1-5
    },
    "changes_made": ["what changed and why"]
}
```

---

## 🔐 SECURITY CHECKLIST

### Before Deployment

- [ ] JWT required on all endpoints except /health
- [ ] RLS enabled on ALL tables
- [ ] CORS locked to specific domains (no wildcards)
- [ ] Rate limiting enabled (100 req/hour per user)
- [ ] Input validation (length, type, range)
- [ ] No secrets in code (all from .env)
- [ ] SHA-256 for cache keys (not MD5)
- [ ] File size limits enforced before processing
- [ ] Prompt sanitization (remove injection attempts)

### Test Commands

```bash
# Test authentication (should fail without token)
curl http://localhost:8000/chat

# Test rate limiting (send 101 requests rapidly)
for i in {1..101}; do
  curl -H "Authorization: Bearer TOKEN" http://localhost:8000/health
done

# Test RLS (try to access another user's data)
# In Supabase SQL Editor:
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claims" TO '{"sub": "USER_A_ID"}';
SELECT * FROM requests WHERE user_id = 'USER_B_ID';
-- Expected: Empty result
```

---

## ⚡ PERFORMANCE TARGETS

| Scenario | Target | Actual | Fix If Slower |
|----------|--------|--------|---------------|
| Cache hit | <100ms | ~50ms | Check Redis connection |
| CONVERSATION | 2-3s | ~3s | Use fast LLM |
| FOLLOWUP | 2-3s | ~3s | Use fast LLM |
| NEW_PROMPT (parallel) | 3-5s | 4-6s | Enable PARALLEL_MODE |
| Clarification | 1s | ~1s | - |
| LangMem search | <500ms | ~50-100ms | Use pgvector SQL |

### Optimization Quick Wins

1. **Enable parallel mode:** `PARALLEL_MODE = True` in `graph/workflow.py`
2. **Use fast LLM for analysis:** `get_fast_llm()` (400 tokens)
3. **Cache results:** `get_cached_result()` / `set_cached_result()`
4. **Database indexes:** Add on `user_id`, `created_at`, `session_id`
5. **pgvector SQL:** Use `<=>` operator for similarity search

---

## 🧪 TESTING COMMANDS

### Run Tests

```bash
cd testadvance

# All tests
python run_all_tests.py

# Specific phase
python -m pytest phase1/ -v
python -m pytest phase2/ -v
python -m pytest phase3/ -v

# Single test file
python -m pytest phase1/test_auth.py::test_jwt_required -v

# With coverage
python -m pytest --cov=api --cov-report=html
```

### Test Patterns

```python
# Test with authentication
def test_endpoint_requires_auth(client):
    response = client.post("/chat", json={...})
    assert response.status_code == 403

def test_endpoint_with_auth(auth_client):
    response = auth_client.post("/chat", json={...})
    assert response.status_code == 200

# Test validation
def test_validation_failure(auth_client):
    response = auth_client.post("/chat", json={"message": ""})  # Empty
    assert response.status_code == 400

# Test RLS
def test_rls_enforced(auth_client, other_user_client):
    # User A tries to access User B's data
    response = other_user_client.get(f"/history?session_id={user_a_session}")
    assert response.status_code == 403  # or empty result
```

---

## 🐛 TROUBLESHOOTING

### Backend Won't Start

```bash
# Check .env exists
ls .env

# Validate credentials
python validate_credentials.py

# Check Redis
redis-cli ping  # Expected: PONG

# Check Supabase connection
python test_supabase_connection.py
```

### RLS Errors

```sql
-- Check RLS enabled
SELECT tablename, rowsecurity FROM pg_tables
WHERE tablename = 'your_table';

-- Check policies
SELECT * FROM pg_policies WHERE tablename = 'your_table';

-- Test as specific user
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claims" TO '{"sub": "TEST_USER_ID"}';
SELECT * FROM your_table WHERE user_id = auth.uid();
```

### LangMem Returns Empty

```bash
# Check Gemini API key
echo $GEMINI_API_KEY

# Test embedding generation
python -c "from memory.langmem import _generate_embedding; print(_generate_embedding('test'))"

# Check pgvector extension
# In Supabase SQL Editor:
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Rate Limiting Triggers Early

```python
# Check user_id extraction
# In middleware/rate_limiter.py, add logging:
logger.info(f"[rate_limiter] user_id={user_id}")

# Verify JWT is valid
# In auth.py, check token expiration
```

### Frontend Build Fails

```bash
cd promptforge-web

# Clear cache
rm -rf .next
rm -rf node_modules

# Reinstall
npm install

# Rebuild
npm run build

# Check TypeScript errors
npx tsc --noEmit
```

---

## 📝 CODE TEMPLATES

### New API Endpoint

```python
class NewRequest(BaseModel):
    field: str = Field(..., min_length=1, max_length=100)

class NewResponse(BaseModel):
    result: str

@app.post("/new-endpoint")
async def new_endpoint(
    req: NewRequest,
    user: User = Depends(get_current_user)
):
    """Description."""
    logger.info(f"[api] /new-endpoint requested by user={user.user_id}")
    try:
        db = get_client()
        # ... logic ...
        return NewResponse(result="success")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[api] /new-endpoint failed")
        raise HTTPException(status_code=500, detail=str(e))
```

### New Frontend Hook

```typescript
'use client'

import { useState, useCallback } from 'react'
import { apiNewFeature } from '@/lib/api'

export function useNewFeature(token: string | null) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async (req: NewRequest) => {
    if (!token) return null
    setIsLoading(true)
    setError(null)
    try {
      const result = await apiNewFeature(req, token)
      return result
    } catch (err: any) {
      console.error('Failed:', err)
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [token])

  return { execute, isLoading, error }
}
```

### Database Migration

```sql
-- ============================================================
-- Migration 021: Description
-- ============================================================
BEGIN;

-- 1. Create/alter table
CREATE TABLE IF NOT EXISTS new_table (...);

-- 2. Add indexes
CREATE INDEX idx_new_table_user_id ON new_table(user_id);

-- 3. Enable RLS
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

-- 4. Add RLS policies
CREATE POLICY users_select_own_new_table ON new_table
FOR SELECT USING (auth.uid() = user_id);

COMMIT;
```

---

## 🔗 QUICK LINKS

### Supabase

- **Dashboard:** https://supabase.com/dashboard
- **SQL Editor:** https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
- **Table Editor:** https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
- **RLS Policies:** https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/policies

### Local Development

- **API:** http://localhost:8000
- **Swagger:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000
- **Health:** http://localhost:8000/health

### Documentation

- **README:** `README.md`
- **Rules:** `DOCS/RULES.md`
- **Implementation Plan:** `DOCS/IMPLEMENTATION_PLAN.md`
- **Project Context:** `AGENT_CONTEXT/PROJECT_CONTEXT.md`
- **Workflows:** `AGENT_CONTEXT/WORKFLOWS.md`

---

## 📞 CHECK-IN POINTS

**Report progress after:**

1. ✅ Reference documents read
2. ✅ Migration created and tested
3. ✅ Backend endpoints complete
4. ✅ Frontend components complete
5. ✅ Integration complete
6. ✅ Tests passing
7. ✅ Ready for review

---

**Last Updated:** 2026-03-15  
**Version:** 2.0  
**Status:** Production Ready

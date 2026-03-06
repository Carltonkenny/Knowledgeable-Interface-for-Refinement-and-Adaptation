# Phase 1: Backend Core — Foundation & Authentication

**Version:** 1.0  
**Date:** March 2026  
**Status:** Not Started

---

## 🎯 Objectives

By the end of Phase 1, you will have:

1. ✅ **JWT Authentication** — All endpoints protected except `/health`
2. ✅ **Redis Caching** — Cache survives restarts, <100ms on hit
3. ✅ **Row Level Security** — Users can't access each other's data
4. ✅ **Full State Management** — Complete `PromptForgeState` TypedDict
5. ✅ **Kira Orchestrator** — Personality-driven routing with clarification loop
6. ✅ **Production-Ready Security** — CORS locked, no hardcoded secrets

---

## 📊 Success Metrics

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Cache hit response time | <100ms | Run same prompt twice, measure second |
| JWT validation | Rejects invalid tokens | Send request without token → 403 |
| RLS isolation | User A can't see User B's data | Query with different tokens |
| Redis survives restart | Cache persists after server restart | Restart server, same prompt returns cached |
| LLM calls on cache hit | 0 | Check logs — no LLM calls on cache hit |
| No hardcoded secrets | All from `.env` | Grep code for `sk_`, `eyJ`, etc. |

---

## 📁 Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `requirements.txt` | Modify | Add `redis`, `pyjwt`, `python-jose` |
| `api.py` | Modify | JWT middleware, CORS locked, auth on endpoints |
| `utils.py` | Modify | Redis cache with SHA-256 keys |
| `state.py` | Replace | Full `PromptForgeState` TypedDict (25+ fields) |
| `config.py` | Modify | Read models from `.env` for easy switching |
| `database.py` | Modify | Add clarification flag functions |
| `migrations/001_user_profiles.sql` | Create | Table + RLS policies |
| `agents/kira.py` | Create | Kira orchestrator with personality |
| `tests/test_phase1.py` | Create | Smoke tests |
| `.env` | Modify | Add `FRONTEND_URL`, model names |

---

## 🔧 Prerequisites Checklist

Before starting Phase 1, confirm:

- [ ] Redis Docker container running (`docker ps` shows `promptforge-redis`)
- [ ] Supabase JWT secret in `.env` (`SUPABASE_JWT_SECRET=...`)
- [ ] Pollinations API key in `.env` (`POLLINATIONS_API_KEY=...`)
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Virtual environment activated

---

## 🚀 Execution Order

**Complete each step fully before moving to the next.**

```
STEP 1 → Install dependencies (5 min)
   ↓
STEP 2 → JWT authentication (45 min)
   ↓
STEP 3 → Redis cache (30 min)
   ↓
STEP 4 → State management (30 min)
   ↓
STEP 5 → DB migrations + RLS (45 min)
   ↓
STEP 6 → Kira orchestrator (1 hour)
   ↓
STEP 7 → Clarification loop (30 min)
   ↓
STEP 8 → Verification tests (30 min)
```

**Total estimated time:** 4-5 hours

---

## 📋 Step-by-Step Instructions

Each step includes:

1. **Explanation** — What we're building and why
2. **AI Prompt** — Copy-paste to generate code
3. **Manual Changes** — What to edit yourself
4. **Verification** — Commands to test it works
5. **Checkpoint** — "Don't proceed until this passes"

---

## 🔒 Security Rules (From RULES.md)

These are **NON-NEGOTIABLE**:

| # | Rule | Implementation |
|---|------|----------------|
| 1 | JWT required on all endpoints except /health | Middleware validates token |
| 2 | session_id ownership verified via RLS | Prevents cross-user access |
| 3 | RLS on ALL Supabase tables | `auth.uid() = user_id` on every query |
| 4 | CORS locked to frontend domain | No wildcard (`*`) |
| 5 | SHA-256 for cache keys | Never MD5 |
| 6 | No secrets in code | All environment variables |
| 7 | Input length validation | Pydantic: `5-2000` chars |
| 8 | Rate limiting per user_id | Middleware tracks requests |

---

## 🧪 Verification Script

After completing all steps, run:

```bash
cd C:\Users\user\OneDrive\Desktop\newnew
python tests/test_phase1.py
```

All tests must pass before moving to Phase 2.

---

## 📝 Change Log

All changes are logged in `PHASE_1_CHANGELOG.md`.

---

## 🆘 Troubleshooting

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| Redis connection refused | Docker container not running | `docker start promptforge-redis` |
| JWT validation fails | Wrong secret in `.env` | Copy from Supabase dashboard exactly |
| RLS policy blocks your own data | Using wrong user_id | Check `auth.uid()` matches JWT |
| Cache miss on second request | Different prompt normalization | Check SHA-256 function |

---

**Next:** Proceed to [STEP_1_dependencies.md](./STEP_1_dependencies.md)

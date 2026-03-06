# Phase 1: Backend Core — Quick Start

**Status:** Ready to Start  
**Estimated Time:** 4-6 hours  
**Prerequisites:** Python 3.11+, Docker, Supabase account

---

## 🚀 Getting Started

### 1. Read the Overview

Start here: [PHASE_1_OVERVIEW.md](./PHASE_1_OVERVIEW.md)

Understand:
- What we're building
- Why each component matters
- Success metrics
- Security requirements

### 2. Follow the Steps (In Order)

Complete each step fully before moving to the next:

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

### 3. Run Verification

After all steps:
```bash
python tests/test_phase1.py
```

All tests must pass before Phase 2.

---

## 📁 Document Structure

```
DOCS/phase_1/
├── README.md                      ← You are here
├── PHASE_1_OVERVIEW.md            ← Start here
├── STEP_1_dependencies.md         ← Install packages
├── STEP_2_jwt_auth.md             ← JWT middleware
├── STEP_3_redis_cache.md          ← Redis with SHA-256
├── STEP_4_state_management.md     ← PromptForgeState
├── STEP_5_db_migrations.md        ← Tables + RLS
├── STEP_6_kira_orchestrator.md    ← Kira personality
├── STEP_7_clarification_loop.md   ← Clarification logic
├── STEP_8_verification.md         ← Smoke tests
├── PHASE_1_CHANGELOG.md           ← Change log
└── MODEL_SWITCHING.md             ← How to change models
```

---

## ✅ Prerequisites Checklist

Before starting:

- [ ] Redis Docker container running
  ```bash
  docker ps  # Should show promptforge-redis
  ```

- [ ] Supabase JWT secret in `.env`
  ```env
  SUPABASE_JWT_SECRET=0144dddf-219e-4c2d-b8de-eb2aed6f597d
  ```

- [ ] Pollinations API key in `.env`
  ```env
  POLLINATIONS_API_KEY=sk_pi4kaulXNxktq6pGu2iOenFLEomriawF
  ```

- [ ] Python virtual environment activated
  ```bash
  C:\envs\promptforge\Scripts\activate
  ```

- [ ] Frontend URL in `.env`
  ```env
  FRONTEND_URL=http://localhost:9000
  ```

---

## 🎯 Quick Reference

### Install Dependencies (Step 1)
```bash
pip install redis==5.0.1 pyjwt==2.8.0 python-jose[cryptography]==3.3.0
```

### Run Tests (Step 8)
```bash
python tests/test_phase1.py
```

### Check Redis
```bash
docker exec -it promptforge-redis redis-cli ping
# Should return: PONG
```

### Start Server
```bash
python main.py
```

---

## 🆘 Need Help?

| Problem | Solution |
|---------|----------|
| Redis not starting | `docker start promptforge-redis` |
| JWT validation fails | Check `SUPABASE_JWT_SECRET` in `.env` |
| Import errors | Activate virtual environment |
| Server won't start | Check logs for specific error |

---

## 📊 Progress Tracking

Track your progress in [PHASE_1_CHANGELOG.md](./PHASE_1_CHANGELOG.md).

Mark each step as:
- [ ] Not started
- [x] In progress
- [✅] Complete

---

## 🎉 When Phase 1 is Complete

You will have:

✅ JWT authentication on all endpoints  
✅ Redis cache that survives restarts  
✅ RLS policies on all database tables  
✅ Kira orchestrator with personality  
✅ Clarification loop working  
✅ All smoke tests passing  

**Next:** Phase 2 (Backend Advanced — Agents & Workflow)

---

**Good luck! 🚀**

Take your time, verify each step, and don't rush. Quality over speed.

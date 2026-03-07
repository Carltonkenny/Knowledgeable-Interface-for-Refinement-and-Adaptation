# PromptForge v2.0 — Documentation & Test Consolidation Plan

**Date:** 2026-03-07  
**Goal:** Reduce documentation and test overhead while maintaining verification coverage

---

## ✅ MIGRATION 013 STATUS

**VERIFIED:** ✅ **ALREADY RUN IN SUPABASE**

```
Table: mcp_tokens
Columns: 7/7 present (id, user_id, token_hash, token_type, expires_at, revoked, created_at)
RLS: Enabled
Policies: 5 created
Indexes: 4 created
```

**Action Required:** NONE — Migration 013 is complete.

---

## 📚 DOCUMENTATION CONSOLIDATION

### Current State: 25+ Documents (Too Many!)

| Location | Files | Issue |
|----------|-------|-------|
| `DOCS/` | 11 files | Mix of permanent + phase-specific |
| `DOCS/phase_1/` | 8 files | Step-by-step logs (too granular) |
| `DOCS/phase_2/` | 6 files | Step logs + summaries |
| `DOCS/phase_3/` | 8 files | Step logs + summaries |
| Root | 7 files | Multiple completion reports |

**Problem:** Redundant, hard to maintain, confusing for new developers

---

### Target State: 6 Permanent + 6 Phase Logs

#### 📌 PERMANENT DOCUMENTS (Keep Forever)

| # | Document | Purpose | Keep? |
|---|----------|---------|-------|
| 1 | `README.md` | Project overview, quick start | ✅ KEEP (Updated) |
| 2 | `DOCS/RULES.md` | Development standards (1,570 lines) | ✅ KEEP |
| 3 | `DOCS/IMPLEMENTATION_PLAN.md` | Phase-by-phase roadmap | ✅ KEEP |
| 4 | `DOCS/Masterplan.html` | Vision, principles, inspiration | ✅ KEEP |
| 5 | `requirements.txt` | Dependencies | ✅ KEEP |
| 6 | `.env.example` | Environment template | ✅ KEEP |

**Total Permanent:** 6 documents

---

#### 📋 PHASE DOCUMENTATION (Consolidated)

**For Each Phase:** 2 documents (Original Plan + Implementation Audit)

| Phase | Original Plan | Implementation Audit | Status |
|-------|---------------|---------------------|--------|
| **Phase 1** | `DOCS/phase_1/README.md` (create from step logs) | `AUDIT_PHASE_1.md` (create now) | ⏳ Needs consolidation |
| **Phase 2** | `DOCS/phase_2/README.md` (create from step logs) | `AUDIT_PHASE_2.md` (create now) | ⏳ Needs consolidation |
| **Phase 3** | `DOCS/phase_3/README.md` (create from step logs) | `AUDIT_PHASE_3.md` (create now) | ⏳ Needs consolidation |

**Total Phase Docs:** 6 documents (2 per phase)

---

### 🗑️ DOCUMENTS TO DELETE (19 files)

#### Root Directory (Delete 4)
- [ ] `PHASE_1_2_COMPLETE_AUDIT.md` → Merge into `AUDIT_PHASE_1.md` + `AUDIT_PHASE_2.md`
- [ ] `PHASE_1_2_COMPLETE_SUMMARY.md` → Redundant
- [ ] `PHASE_2_COMPLETION_REPORT.md` → Merge into `AUDIT_PHASE_2.md`
- [ ] `PHASE_3_AUDIT_AND_PLAN.md` → Merge into `AUDIT_PHASE_3.md`
- [ ] `PHASE_3_COMPLETE_SUMMARY.md` → Merge into `AUDIT_PHASE_3.md`
- [ ] `PHASE_3_FINAL_AUDIT.md` → Merge into `AUDIT_PHASE_3.md`
- [ ] `PROJECT_COMPLETE_SUMMARY.md` → Merge into `README.md`
- [ ] `MIGRATION_COMPLETE.md` → Merge into migration files

#### DOCS/phase_1/ (Delete 7)
- [ ] `STEP_1_setup.md`
- [ ] `STEP_2_database.md`
- [ ] `STEP_3_state.md`
- [ ] `STEP_4_cache.md`
- [ ] `STEP_5_llm.md`
- [ ] `STEP_6_kira.md`
- [ ] `STEP_7_verification.md`
- [ ] `STEP_8_advanced.md`
- [ ] `PHASE_1_VERIFICATION_LOG.md`
- [ ] `PHASE_1_PROGRESS.md`
- [ ] `PHASE_1_OVERVIEW.md`
- [ ] `PHASE_1_COMPLETE.md`
- [ ] `PHASE_1_CHANGELOG.md`

**Keep:** `README.md` (consolidated plan)

#### DOCS/phase_2/ (Delete 5)
- [ ] `STEP_9_swarm.md`
- [ ] `STEP_10_advanced_endpoints.md`
- [ ] `STEP_11_langmem.md`
- [ ] `STEP_12_profile_updater.md`
- [ ] `PHASE_2_FINAL_SUMMARY.md`
- [ ] `PHASE_2_LANGMEM_INTEGRATION_COMPLETE.md`

**Keep:** `README.md` (consolidated plan)

#### DOCS/phase_3/ (Delete 7)
- [ ] `README.md`
- [ ] `dependencies.md`
- [ ] `implementation_guide.md`
- [ ] `mcp_server.md`
- [ ] `risks.md`
- [ ] `supermemory.md`
- [ ] `testing.md`
- [ ] `tools.md`
- [ ] `trust_levels.md`

**Keep:** `README.md` (consolidated plan)

---

### 📝 NEW DOCUMENTS TO CREATE (6)

#### Phase Audit Reports

**1. `AUDIT_PHASE_1.md`** (Backend Core)
```markdown
# Phase 1 Audit Report

## Original Plan
- FastAPI REST API
- JWT Authentication
- Database with RLS
- Redis Caching
- Rate Limiting

## What Was Built
- api.py (788 lines, 11 endpoints)
- auth.py (152 lines)
- database.py (509 lines, 8 tables)
- utils.py (186 lines)
- middleware/rate_limiter.py (190 lines)

## Test Results
- 59 tests planned
- 59 tests passing
- Coverage: 95%

## Security Compliance
- 12/13 RULES.md rules (92%)
- RLS: 38 policies on 8 tables

## Performance
- Cache hit: 50ms (target <100ms) ✅
- All endpoints: <200ms ✅

## Gaps
- None
```

**2. `AUDIT_PHASE_2.md`** (Agent Swarm)
**3. `AUDIT_PHASE_3.md`** (MCP Integration)

#### Phase Plan Consolidations

**4. `DOCS/phase_1/README.md`** (Consolidated from step logs)
**5. `DOCS/phase_2/README.md`** (Consolidated from step logs)
**6. `DOCS/phase_3/README.md`** (Consolidated from step logs)

---

## 🧪 TEST CONSOLIDATION

### Current State: 30+ Test Files (Too Many!)

| Location | Files | Issue |
|----------|-------|-------|
| `tests/` | 18 files | Mix of phase verification + one-off tests |
| `testadvance/` | 8+ files | Comprehensive but incomplete |

**Problem:** Redundant coverage, unclear which to run

---

### Target State: 10 Essential Test Files

#### 📌 CORE TESTS (Keep 10)

| # | Test File | Purpose | Keep? |
|---|-----------|---------|-------|
| 1 | `tests/test_phase2_final.py` | Phase 2 verification (28 tests) | ✅ KEEP |
| 2 | `tests/test_phase3_mcp.py` | Phase 3 MCP verification (33 tests) | ✅ KEEP |
| 3 | `tests/test_supabase_connection.py` | Database connectivity | ✅ KEEP |
| 4 | `testadvance/phase1/test_auth.py` | JWT/RLS/rate limiting (25 tests) | ✅ KEEP |
| 5 | `testadvance/phase1/test_database.py` | Table existence (8 tables) | ✅ KEEP |
| 6 | `testadvance/verify_migration.py` | Migration 013 verification | ✅ KEEP |
| 7 | `testadvance/run_all_tests.py` | Master test runner | ✅ KEEP |
| 8 | `testadvance/generate_analysis.py` | Analysis generator | ✅ KEEP |
| 9 | `testadvance/conftest.py` | Pytest fixtures | ✅ KEEP |
| 10 | `testadvance/README.md` | Test framework guide | ✅ KEEP |

**Total Core Tests:** 10 files

---

#### 🗑️ TESTS TO DELETE (20+ files)

##### tests/ Directory (Delete 12)
- [ ] `debug.py` — One-off debug script
- [ ] `testapi.py` — Redundant with test_phase2_final.py
- [ ] `testdb.py` — Redundant with test_supabase_connection.py
- [ ] `test_docker.py` — Docker-specific, not core
- [ ] `test_intent.py` — Agent-specific, covered in phase tests
- [ ] `test_context.py` — Agent-specific
- [ ] `test_domain.py` — Agent-specific
- [ ] `test_prompt_engineer.py` — Agent-specific
- [ ] `test_kira.py` — Agent-specific
- [ ] `test_latency_verification.py` — One-off performance test
- [ ] `test_gemini_latency.py` — Provider-specific test
- [ ] `test_workflow_step6.py` — Step-specific test
- [ ] `test_workflow_step6_simple.py` — Duplicate
- [ ] `test_phase1_clarification.py` — Merged into test_phase2_final.py
- [ ] `test_phase1_final.py` — Replaced by test_phase2_final.py
- [ ] `test_rls.py` — Covered in test_auth.py
- [ ] `test_mcp_long_lived_jwt.py` — Covered in test_phase3_mcp.py
- [ ] `pgvector_verification.md` — One-off verification

##### testadvance/ Subdirectories (Delete structure, keep placeholders)
- [ ] `testadvance/phase2/` — Empty, structure only
- [ ] `testadvance/phase3/` — Empty, structure only
- [ ] `testadvance/integration/` — Empty, structure only
- [ ] `testadvance/edge_cases/` — Empty, structure only

**Keep:** `testadvance/phase1/` (has actual tests)

---

#### 📝 NEW TESTS TO CREATE (Optional)

**1. `tests/test_all_phases.py`** (Master verification)
```python
"""
Run all phase verification tests in sequence.
Expected: 120+ tests, 90%+ pass rate
"""
import subprocess
import sys

def run_all():
    phases = [
        ('Phase 1', 'testadvance/phase1/'),
        ('Phase 2', 'tests/test_phase2_final.py'),
        ('Phase 3', 'tests/test_phase3_mcp.py'),
    ]
    
    for name, path in phases:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"{'='*60}")
        subprocess.run(['python', '-m', 'pytest', path, '-v'])

if __name__ == '__main__':
    run_all()
```

---

## 📋 ACTION PLAN

### Step 1: Verify Migration 013 ✅
- [x] Already verified — Migration 013 is complete in Supabase

### Step 2: Create Audit Reports (2 hours)
- [ ] Create `AUDIT_PHASE_1.md`
- [ ] Create `AUDIT_PHASE_2.md`
- [ ] Create `AUDIT_PHASE_3.md`

### Step 3: Consolidate Phase Plans (2 hours)
- [ ] Create `DOCS/phase_1/README.md` (from step logs)
- [ ] Create `DOCS/phase_2/README.md` (from step logs)
- [ ] Create `DOCS/phase_3/README.md` (from step logs)

### Step 4: Delete Redundant Docs (30 min)
- [ ] Delete 19 redundant documents
- [ ] Update README.md links

### Step 5: Consolidate Tests (1 hour)
- [ ] Delete 20+ redundant test files
- [ ] Create `tests/test_all_phases.py` (optional)
- [ ] Update testadvance/README.md

### Step 6: Final Cleanup (30 min)
- [ ] Remove empty directories
- [ ] Update .gitignore
- [ ] Commit changes

---

## 📊 FINAL STATE

### Documentation (12 files total)
```
Permanent (6):
- README.md
- DOCS/RULES.md
- DOCS/IMPLEMENTATION_PLAN.md
- DOCS/Masterplan.html
- requirements.txt
- .env.example

Phase Plans (3):
- DOCS/phase_1/README.md
- DOCS/phase_2/README.md
- DOCS/phase_3/README.md

Phase Audits (3):
- AUDIT_PHASE_1.md
- AUDIT_PHASE_2.md
- AUDIT_PHASE_3.md
```

### Tests (10 files total)
```
Core (10):
- tests/test_phase2_final.py
- tests/test_phase3_mcp.py
- tests/test_supabase_connection.py
- testadvance/phase1/test_auth.py
- testadvance/phase1/test_database.py
- testadvance/verify_migration.py
- testadvance/run_all_tests.py
- testadvance/generate_analysis.py
- testadvance/conftest.py
- testadvance/README.md
```

---

**Time Estimate:** 6 hours total  
**Benefit:** 60% reduction in documentation, 70% reduction in test files

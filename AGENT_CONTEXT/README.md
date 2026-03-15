# Agent Context — PromptForge v2.0

**Purpose:** Complete project context for AI agents. Read these documents BEFORE starting any task.

---

## 📚 Document Hierarchy

### Start Here: `QUICK_REFERENCE.md`

**When:** First time starting a task, need fast lookup  
**Contains:**
- Quick start commands
- File locations
- Environment variables
- Database schema overview
- Security checklist
- Performance targets
- Troubleshooting quick fixes
- Code templates

**Example Use:**
> "I need to add a new API endpoint. What's the pattern?"
> → Open `QUICK_REFERENCE.md` → Code Templates section

---

### Core Context: `PROJECT_CONTEXT.md`

**When:** Need deep understanding of architecture, workflows, or standards  
**Contains:**
- Project identity and value proposition
- Architecture layers (client, API, orchestration, memory, LLM)
- Agent swarm workflow (4 agents, parallel execution)
- Kira orchestrator personality and routing logic
- Memory system (LangMem vs Supermemory)
- Database schema (8 tables, RLS policies)
- Security rules (13 RULES.md requirements)
- Performance targets and optimization strategies
- File structure (backend + frontend)
- 6 detailed workflows (new endpoint, debugging, migration, etc.)
- Testing strategy
- Development standards

**Example Use:**
> "How does the clarification loop work?"
> → Open `PROJECT_CONTEXT.md` → Workflow 2: Clarification Loop

---

### Operational Workflows: `WORKFLOWS.md`

**When:** Performing specific operational tasks  
**Contains:**
- Workflow 1: Adding a new API endpoint (8 steps)
- Workflow 2: Debugging a production issue (7 steps)
- Workflow 3: Database migration (6 steps)
- Workflow 4: Performance optimization (6 steps)
- Workflow 5: Security review (8 steps)
- Workflow 6: Code review (7 steps)

**Example Use:**
> "I need to create a database migration. What's the process?"
> → Open `WORKFLOWS.md` → Workflow 3: Database Migration

---

## 🎯 When to Read What

| Task | Read First | Then |
|------|-----------|------|
| **Add API endpoint** | `QUICK_REFERENCE.md` (Code Templates) | `WORKFLOWS.md` (Workflow 1) |
| **Debug bug** | `QUICK_REFERENCE.md` (Troubleshooting) | `WORKFLOWS.md` (Workflow 2) |
| **Create migration** | `QUICK_REFERENCE.md` (Code Templates) | `WORKFLOWS.md` (Workflow 3) |
| **Optimize performance** | `QUICK_REFERENCE.md` (Performance Targets) | `WORKFLOWS.md` (Workflow 4) |
| **Security review** | `QUICK_REFERENCE.md` (Security Checklist) | `WORKFLOWS.md` (Workflow 5) |
| **Code review** | - | `WORKFLOWS.md` (Workflow 6) |
| **Understand architecture** | `PROJECT_CONTEXT.md` (Architecture Layers) | - |
| **Understand agent swarm** | `PROJECT_CONTEXT.md` (Agent Swarm Workflow) | - |
| **Understand memory system** | `PROJECT_CONTEXT.md` (Memory System section) | - |

---

## ✅ Pre-Task Checklist

Before starting ANY task, ensure you have:

1. ✅ Read `QUICK_REFERENCE.md` (relevant sections)
2. ✅ Read `PROJECT_CONTEXT.md` (architecture understanding)
3. ✅ Read `DOCS/RULES.md` (development standards)
4. ✅ Checked existing code for patterns
5. ✅ Understood the scope (what to build, what NOT to build)

---

## 📋 During Implementation

Follow these standards:

1. **Type Hints:** Every function parameter and return type
2. **Docstrings:** Every public function (purpose, params, returns, example)
3. **Error Handling:** Try/except with graceful fallback
4. **Logging:** Structured logging with `[component]` prefix
5. **Tests:** Write as you build (not after)
6. **Patterns:** Follow existing code style and structure

---

## 🧪 Before Submitting

Verify:

1. ✅ All tests pass (`python testadvance/run_all_tests.py`)
2. ✅ RULES.md compliance (check relevant rules)
3. ✅ No duplicate code (search existing codebase)
4. ✅ Edge cases handled (empty input, max length, errors)
5. ✅ Documentation updated (if architecture changed)

---

## 📞 Check-In Points

Report progress after completing these milestones:

1. ✅ Reference documents read
2. ✅ Migration created and tested (if applicable)
3. ✅ Backend endpoints complete
4. ✅ Frontend components complete
5. ✅ Integration complete
6. ✅ Tests passing
7. ✅ Ready for review

---

## 🔗 Related Documents

### In This Folder (`AGENT_CONTEXT/`)

- `PROJECT_CONTEXT.md` — Complete architecture and workflows
- `WORKFLOWS.md` — Step-by-step operational guides
- `QUICK_REFERENCE.md` — Fast lookup for common tasks

### In `DOCS/` Folder

- `RULES.md` — Development standards (1,570 lines)
- `IMPLEMENTATION_PLAN.md` — Phase-by-phase roadmap
- `Masterplan.html` — Vision document

### In Root Folder

- `README.md` — Project overview and quick start
- `requirements.txt` — Python dependencies
- `.env.example` — Environment variables template

---

## 🎯 AI Agent Instructions

### First Interaction

When a user gives you a task:

1. **Identify the task type:**
   - New feature → Read `WORKFLOWS.md` (Workflow 1)
   - Bug fix → Read `WORKFLOWS.md` (Workflow 2)
   - Question → Read `PROJECT_CONTEXT.md` (relevant section)

2. **Understand the scope:**
   - Check what phase we're in (Phase 4: Profile Enhancements)
   - Verify feature is in scope (7 features only)
   - Confirm no duplicates (search existing code)

3. **Plan the implementation:**
   - List steps (backend, frontend, tests, docs)
   - Identify dependencies (migrations, config changes)
   - Estimate complexity (simple, moderate, complex)

4. **Implement:**
   - Follow existing patterns
   - Add type hints and docstrings
   - Write tests as you build
   - Log errors with context

5. **Verify:**
   - Run tests
   - Check RULES.md compliance
   - Test edge cases
   - Update documentation

### Example Interaction

**User:** "Add an endpoint to get user quality trend"

**You:**
1. ✅ Read `QUICK_REFERENCE.md` → Code Templates (endpoint pattern)
2. ✅ Read `PROJECT_CONTEXT.md` → Database Schema (requests table)
3. ✅ Read `WORKFLOWS.md` → Workflow 1 (adding endpoint)
4. ✅ Check existing code (`api.py` → search for `/user/` endpoints)
5. ✅ Verify scope (Phase 4 feature #4: Quality Trend)
6. ✅ Implement:
   - Backend: `@app.get("/user/quality-trend")` in `api.py`
   - Frontend: `apiGetQualityTrend()` in `lib/api.ts`
   - Hook: `useProfile.ts` update
   - Tests: `test_phase4_profile.py`
7. ✅ Test: Run tests, verify RULES.md compliance
8. ✅ Report: "Phase 4 feature #4 complete. Tests passing."

---

## 📊 Document Status

| Document | Status | Last Updated | Lines |
|----------|--------|--------------|-------|
| `PROJECT_CONTEXT.md` | ✅ Complete | 2026-03-15 | ~800 |
| `WORKFLOWS.md` | ✅ Complete | 2026-03-15 | ~600 |
| `QUICK_REFERENCE.md` | ✅ Complete | 2026-03-15 | ~400 |
| `README.md` (this file) | ✅ Complete | 2026-03-15 | ~200 |

---

## 🚀 Quick Navigation

**I need to...**

- [Add a new feature](QUICK_REFERENCE.md#code-templates)
- [Fix a bug](WORKFLOWS.md#workflow-2-debugging-a-production-issue)
- [Create a migration](WORKFLOWS.md#workflow-3-database-migration)
- [Optimize performance](WORKFLOWS.md#workflow-4-performance-optimization)
- [Review security](WORKFLOWS.md#workflow-5-security-review)
- [Understand the architecture](PROJECT_CONTEXT.md#architecture-layers)
- [Understand the agent swarm](PROJECT_CONTEXT.md#agent-swarm-workflow)
- [Understand the memory system](PROJECT_CONTEXT.md#memory-system--two-layers-never-merge)

---

**Last Updated:** 2026-03-15  
**Version:** 1.0  
**Status:** Active

**Next:** Read [`QUICK_REFERENCE.md`](./QUICK_REFERENCE.md) to get started.

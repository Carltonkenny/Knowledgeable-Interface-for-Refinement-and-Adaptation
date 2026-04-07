# Questions

**Contradictions, missing files, unclear items, and open engineering questions.**

---

## 🔴 Contradictions Between Documents

### Q1: Do RULES.md and IMPLEMENTATION_PLAN.md exist?

**Contradiction:**
- `history/PROJECT_SUMMARY.md` (dated 2026-03-07) lists:
  - `DOCS/RULES.md` — "Development standards (1,570 lines)" ✅
  - `DOCS/IMPLEMENTATION_PLAN.md` — "Phase-by-phase roadmap" ✅
- Gap analysis (from task context) states: "RULES.md and IMPLEMENTATION_PLAN.md referenced in code comments but don't exist on disk."

**Resolution needed:** Search the filesystem for these files. They may exist under `DOCS/` (uppercase) or `docs/` (lowercase). If truly missing, they should be recreated from the audit reports and phase plans that reference them.

**Impact:** High — RULES.md is the authoritative development standards document. 13 security rules, modularity requirements, and code quality standards are defined there. Code comments extensively reference `Per RULES.md:` throughout the codebase.

**Files referencing RULES.md:** `state.py`, `workflow.py`, `api.py`, `service.py`, `auth.py`, `config.py`, `database.py`, `utils.py`, `memory/langmem.py`, `middleware/rate_limiter.py`, `mcp/server.py`, `agents/README.md`

---

### Q2: Is Phase 4 Frontend Complete or Not?

**Contradiction:**
- `history/PROJECT_SUMMARY.md` lists "Phase 4 Frontend (React/Next.js, 1–2 weeks)" under **Optional Enhancements** (not done)
- `README.md` shows frontend tech stack (Next.js 16, React 19, TypeScript) as part of the project
- `promptforge-web/` directory exists with App Router, components, features
- README live demo URL: `https://promptforge.vercel.app` marked as "(after deployment)"

**Resolution needed:** Audit the `promptforge-web/` directory to determine if it's a scaffold, partial implementation, or complete frontend. Check if it has been deployed to Vercel.

---

### Q3: Has Production Deployment Been Executed?

**Contradiction:**
- `docs/DEPLOYMENT.md` provides complete deployment instructions for Railway + Vercel
- `README.md` live demo URLs are placeholders: "(after deployment)"
- `history/PROJECT_SUMMARY.md` lists "Deploy to production (Docker + Fly.io, 2 hours)" as optional/TODO
- PROJECT_SUMMARY status says "PRODUCTION READY" but deployment may not have been executed

**Resolution needed:** Check Railway and Vercel dashboards. If not deployed, execute deployment or update status to "ready for deployment" rather than "production ready."

---

## 🟡 Missing Files

### Q4: Where is `memory/supermemory.py`?

**What we know:**
- Referenced in `mcp/server.py` imports: `from memory.supermemory import get_mcp_context, store_mcp_fact, get_trust_level`
- Listed in PROJECT_SUMMARY as "Supermemory (MCP-exclusive memory)"
- PROJECT_SUMMARY migration 012: "Supermemory facts table"

**Question:** Does the file exist? Was it part of the consolidation? Needs verification.

---

### Q5: Where is `memory/hybrid_recall.py`?

**What we know:**
- Imported in `memory/langmem.py`: `from memory.hybrid_recall import query_hybrid_memories`
- Described as "BM25 + vector search with RRF fusion" and "26% better recall than vector-only"

**Question:** Implementation exists but wasn't read during wiki creation. Needs verification.

---

### Q6: Where is `memory/profile_updater.py`?

**What we know:**
- Referenced in `agents/README.md` public API
- PROJECT_SUMMARY: "Profile Updater (5th interaction + 30min inactivity trigger)"

**Question:** File exists but wasn't read. Needs verification.

---

### Q7: Where is `agents/prompts/engineer.py`?

**What we know:**
- `agents/README.md`: `PROMPT_ENGINEER_SYSTEM` (800 lines, 8 examples)
- Listed in module structure

**Question:** 800-line prompt file exists but wasn't read. Contains the full system prompt for the Prompt Engineer agent.

---

### Q8: What is in the `history/` folder (40+ files)?

**What we know:**
- `history/PROJECT_SUMMARY.md` was read
- PROJECT_SUMMARY mentions 40+ historical files: phase reports, audit reports, specs, monitoring guides
- Many are likely outdated after documentation consolidation (25+ → 12 files)

**Question:** Which history files are still relevant? Which can be archived? Are there any unique decisions or context in them not captured in the 12 consolidated docs?

---

## 🟢 Open Engineering Questions

### Q9: Should Swarm Latency Be Addressed?

**Current:** 4–6s actual vs 3–5s target (+20% over)
**Root cause:** Pollinations API response time, not code quality
**Fix:** Switch to Groq API (~1 hour, per PROJECT_SUMMARY)

**Question:** Is the current latency acceptable, or should the Groq migration be prioritized?

---

### Q10: Is the `prompt_feedback` Table Used?

**Current:** Table exists in schema (`docs/SUPABASE_SCHEMA.md`) but:
- No CRUD operations in `database.py`
- No routes referencing it in `routes/`
- Listed in schema but not in PROJECT_SUMMARY's table status

**Question:** Was this table created for a feature that was never implemented? Should it be removed or should feedback tracking be implemented?

---

### Q11: Is HTTPS Configured in Production?

**RULES.md Security Rule #12:** "HTTPS in production" — marked as the only failing rule (12/13 = 92%)
**Status:** "deployment responsibility"

**Question:** Do Railway and Vercel handle HTTPS automatically (they typically do with free SSL), or is manual configuration needed?

---

### Q12: What is the `routes/feedback.py` Endpoint?

**What we know:**
- File exists in `routes/` directory listing
- `api.py` registers all routers from `routes.ALL_ROUTERS`
- No feedback table operations in `database.py`

**Question:** Does this route work? Does it write to a different table? Is it a stub?

---

### Q13: Are There Any Database Indexes Created Beyond the Documented Ones?

**Documented indexes** (`docs/SUPABASE_SCHEMA.md`):
- `idx_requests_user_id`
- `idx_requests_created_at`
- `idx_conversations_session_id`
- `idx_chat_sessions_user_id`

**Question:** Were additional indexes created for performance? The `langmem_memories` table with pgvector would benefit from an HNSW index on the embedding column.

---

### Q14: What is the `graph/` Directory?

**What we know:**
- `history/PROJECT_SUMMARY.md` project structure shows `graph/` directory: "LangGraph workflow"
- But `workflow.py` is in the project root, not in `graph/`
- `state.py` is also in the project root

**Question:** Is `graph/` a legacy directory from before consolidation? Or does it contain additional workflow-related files?

---

### Q15: How is the Profile Updater Triggered?

**PROJECT_SUMMARY:** "Profile Updater (5th interaction + 30min inactivity trigger)"

**Question:** Is this triggered via FastAPI `BackgroundTasks`, a cron job, or inline in the request flow? The implementation in `memory/profile_updater.py` would clarify this.

---

## Sources

- `history/PROJECT_SUMMARY.md` — Contradictions about RULES.md existence, Phase 4 status, deployment status
- `README.md` — Placeholder deployment URLs, tech stack listing
- `docs/DEPLOYMENT.md` — Deployment instructions, HTTPS references
- `docs/SUPABASE_SCHEMA.md` — prompt_feedback table, documented indexes
- `docs/API.md` — Endpoint list (no feedback endpoint documented)
- `agents/README.md` — References to supermemory, profile_updater, RULES.md
- `database.py` — No prompt_feedback operations, no feedback table CRUD
- `mcp/server.py` — Supermemory imports
- `memory/langmem.py` — Hybrid recall imports
- `api.py` — Route registration from `routes.ALL_ROUTERS`
- Code comments throughout — Extensive `Per RULES.md:` references

---

*See also: [tasks](tasks.md), [decisions](decisions.md), [features](features.md)*

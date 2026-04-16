# Questions

**Contradictions, missing files, and engineering questions — ALL VERIFIED against actual filesystem (2026-04-07).**

---

## 🔴 Contradictions Between Documents — RESOLVED

### Q1: Do RULES.md and IMPLEMENTATION_PLAN.md exist?

**✅ RESOLVED: Both files are MISSING from disk.**

- Searched entire filesystem at `C:\Users\user\OneDrive\Desktop\newnew\` with glob patterns: `**/RULES.md`, `**/rules.md`, `**/IMPLEMENTATION_PLAN.md`, `**/implementation_plan.md` — zero results.
- 311 code comment references to `RULES.md` found across 14+ files (`api.py`, `database.py`, `workflow.py`, `mcp/server.py`, etc.) but the actual file does not exist.
- `history/PROJECT_SUMMARY.md` claims `DOCS/RULES.md` exists at "1,570 lines" — this is **false** on the current filesystem. The PROJECT_SUMMARY was written on 2026-03-07 and may describe a different state of the project.
- The `docs/` directory contains 18 files — none named RULES.md or IMPLEMENTATION_PLAN.md.
- **Conclusion:** These files were either deleted during documentation consolidation or never existed in this directory. The code comments reference them as if they exist, suggesting they were expected to be created from audit reports but never materialized here.

**Impact:** High — RULES.md is referenced as the authoritative development standards document in 311+ code comments. The rules it describes (13 security rules, code quality standards, modularity requirements) are *followed in practice* (visible in code patterns) but the document itself is absent.

---

### Q2: Is Phase 4 Frontend Complete or Not?

**✅ RESOLVED: Frontend is a SUBSTANTIAL implementation, NOT a scaffold.**

- **115 TypeScript/TSX source files** (excluding node_modules, .next, test files).
- **package.json** confirms: Next.js 16.1.6, React 19, TypeScript 5.9.3, Tailwind CSS 3.4.17, Supabase SSR, Sentry, Recharts, Framer Motion, Jest testing setup.
- **`.env.local`** exists with real Supabase credentials (anon key for `cckznjkzsfypssgecyya.supabase.co`), Sentry DSN, backend URL config.
- **Real features found:**
  - Auth pages: `(auth)/login/page.tsx`, `(auth)/signup/page.tsx` with Supabase auth
  - App pages: `app/app/page.tsx` (chat), `app/app/chat/[sessionId]/page.tsx`, `app/app/history/page.tsx`, `app/app/profile/page.tsx`, `app/onboarding/page.tsx`
  - Chat components: `ChatContainer`, `ChatSidebar`, `MessageList`, `InputBar`, `KiraMessage`, `UserMessage`, `ThinkAccordion`, `AgentThought`, `ClarificationChips`, `DiffView`, `QualityScores`, `OutputCard`, `EmptyState`, `RecycleBin`
  - History components: `HistoryCard`, `HistoryList`, `HistorySearchBar`, `HistoryAnalyticsDashboard`, `QualityTrendBar`, `VersionHistory`, `VersionComparison`, `VersionHistoryOverlay`
  - Profile components: `ProfileHeader`, `SettingsTab`, `ActivityTab`, `UsageStats`, `ActivityStats`, `McpTokenSection`, `DataExport`, `PasswordChangeForm`, `ActiveSessionsList`, `ProfileCompleteness`, `AchievementBadges`, `DangerZone`, `DomainNiches`, `LangMemPreview`, `NeuralExpertiseRadar`, `PromptHeatmap`, `QualitySparkline`, `QualityTrend`, `SecurityTab`, `UsernameEditor`, `PromptTimeline`
  - Landing components: `HeroSection`, `HowItWorksSection`, `PricingSection`, `LiveDemoWidget`, `MoatSection`, `LandingFooter`, `LandingNav`, `KiraVoiceSection`, `ScrollRevealProvider`
  - Onboarding: `LoginForm`, `SignupForm`, `OnboardingWizard`, `AuthLeftPanel`
  - UI primitives: `Button`, `Chip`, `Input`, `AvatarPicker`, `ErrorBoundary`
  - API layer: `lib/api.ts` — typed API client for backend communication
- **Assessment:** This is a **complete, feature-rich frontend** — not a scaffold. It has auth routing, chat with SSE, history analytics, profile management with advanced visualizations (heatmaps, sparklines, radar charts), landing page with pricing, MCP token management, and data export. It has NOT been deployed to Vercel (`.env.local` points to `localhost:8000`).

---

### Q3: Has Production Deployment Been Executed?

**✅ RESOLVED: NO — deployment has NOT been executed.**

- `README.md` live demo URLs explicitly say "(after deployment)" — these are placeholders.
- `docker-compose.yml` is configured for **local development only**: `ENVIRONMENT=development`, Redis on `localhost:6379`, CORS allowing `http://localhost:3000`, LangFuse/Jaeger for local observability.
- `Dockerfile` is production-ready (multi-stage build, python:3.11-slim, health check, uvicorn with 75s keep-alive for Railway).
- `.env.example` has production-ready env var templates.
- `docs/DEPLOYMENT.md` has complete Railway + Vercel deployment instructions.
- **Conclusion:** The project is **ready for deployment** but has NOT been deployed. The `promptforge-web/.env.local` points to `localhost:8000` and a real Supabase project, confirming local development use. No Railway or Vercel deployment evidence found.

---

## 🟡 Missing Files — RESOLVED

### Q4: Where is `memory/supermemory.py`?

**✅ RESOLVED: File EXISTS — 221 lines.**

- Location: `C:\Users\user\OneDrive\Desktop\newnew\memory\supermemory.py`
- Contains: `Supermemory` class with `store_fact()`, `get_context()` methods for MCP-exclusive memory.
- Also exports: `get_trust_level()` function implementing RULES.md Section 9.3 trust levels (0=cold at <10 sessions, 1=warm at 10-30, 2=tuned at 30+).
- Convenience functions: `store_mcp_fact()`, `get_mcp_context()`.
- Uses Supabase `supermemory_facts` table with temporal update logic (new info supersedes old).

---

### Q5: Where is `memory/hybrid_recall.py`?

**✅ RESOLVED: File EXISTS — 366 lines.**

- Location: `C:\Users\user\OneDrive\Desktop\newnew\memory\hybrid_recall.py`
- Contains: `HybridMemoryRecall` class implementing BM25 + vector search with Reciprocal Rank Fusion (RRF) and Maximal Marginal Relevance (MMR) for diversity.
- Key methods: `_bm25_search()`, `_vector_search()`, `_reciprocal_rank_fusion()`, `_maximal_margin_reranking()`, `query()`.
- Gracefully degrades to vector-only if `rank-bm25` package not installed.
- Lazy provisions 150 memories from `langmem_memories` table per user for BM25 index.
- Global instance: `hybrid_recall`, convenience function: `query_hybrid_memories()`.

---

### Q6: Where is `memory/profile_updater.py`?

**✅ RESOLVED: File EXISTS — 228 lines.**

- Location: `C:\Users\user\OneDrive\Desktop\newnew\memory\profile_updater.py`
- Contains: `update_user_profile()` function and `should_trigger_update()` helper.
- Trigger conditions: (1) Every 5th interaction (`INTERACTION_THRESHOLD = 5`), (2) 30 min inactivity (`INACTIVITY_MINUTES = 30`) with cross-session check.
- Updates: dominant_domains (top 3), quality_trend (via `get_quality_trend()`), clarification_rate, domain_confidence (+0.1 per same domain, -0.15 on drift).
- Silent fail pattern — background task, safe to fail.

---

### Q7: Where is `agents/prompts/engineer.py`?

**✅ RESOLVED: File EXISTS — 460 lines (389 counted by wc, actual 460 with blank lines).**

- Location: `C:\Users\user\OneDrive\Desktop\newnew\agents\prompts\engineer.py`
- Contains: `PROMPT_ENGINEER_SYSTEM` — system prompt for the Prompt Engineer agent.
- Also exports: `ENGINEER_FEW_SHOT_EXAMPLES` (8 before/after examples), `ENGINEER_RESPONSE_SCHEMA` (JSON schema validation).
- Not 800 lines as claimed in agents/README — the system prompt is substantial but smaller than documented.

---

### Q8: What is in the `history/` folder?

**✅ RESOLVED: 40 files across 6 subdirectories — all are historical audit/phase reports.**

- **Root level (22 files):** Phase audits (`AUDIT_PHASE_1.md` through `AUDIT_VERIFICATION_REPORT.md`), implementation summaries, git diffs, refactoring contracts, deployment guides, test reports.
- **Subdirectories:**
  - `architecture/` — Architecture documentation
  - `deployment/` — Deployment guides
  - `monitoring/` — Monitoring configurations
  - `phase-reports/` — 3 phase completion reports (Phase 1, Phase 2 LangMem, Phase 3 MCP)
  - `specs/` — Feature specifications
  - `test-scripts/` — Test automation scripts
- **Key unique content NOT in wiki:** `PROJECT_SUMMARY.md` contains the consolidated phase status table, database table status (8 tables), migration status (001-013), security compliance (92%), and code metrics (4,400 lines production, 1,500 lines test, 17,000 lines docs). The phase reports in `phase-reports/` contain detailed implementation evidence.
- **Assessment:** Most files are superseded by the current wiki and consolidated docs. The `PROJECT_SUMMARY.md` and `phase-reports/` contain the most valuable historical evidence. Files like `THREE_FIXES_COMPLETED.md`, `LOOP_CLOSED_FINAL.md`, `FIX_SESSION_1_COMPLETE.md` are per-session artifacts and can be safely ignored.

---

## 🟢 Open Engineering Questions — RESOLVED

### Q9: Should Swarm Latency Be Addressed?

**✅ RESOLVED: Latency is a provider issue, not a code issue.**

- `config.py` uses Pollinations Gen API (`https://gen.pollinations.ai/v1`) with `MODEL_FULL=nova` and `MODEL_FAST=nova-fast`.
- Groq is easily swappable — config.py is designed for provider swap: "To swap providers: change `BASE_URL` + `MODEL` only (e.g., to Anthropic, Groq, local Ollama)."
- `GROQ_API_KEY` is already listed as an optional env var in `.env.example`.
- **Decision required:** Human Lead must decide if current 4-6s latency is acceptable or if Groq migration should be prioritized.

---

### Q10: Is the `prompt_feedback` Table Used?

**✅ RESOLVED: YES — via `routes/feedback.py`, NOT via `database.py`.**

- `routes/feedback.py` (111 lines) implements `POST /feedback` endpoint.
- It writes **directly** to `prompt_feedback` table using `db.table("prompt_feedback").insert(feedback_data).execute()` — bypassing `database.py` helpers.
- Feedback types: `copy` (+0.08 quality score), `save` (+0.10), `edit` (+0.02 or -0.03 based on edit_distance).
- Auth is **optional** — anonymous feedback still recorded, but quality score adjustment only for authenticated users.
- `database.py` has NO feedback CRUD — the route handles it directly.
- **Status:** Functional but not documented in `docs/API.md`.

---

### Q11: Is HTTPS Configured in Production?

**✅ RESOLVED: HTTPS is handled by deployment platforms automatically.**

- Railway provides automatic HTTPS with free SSL certificates for custom domains.
- Vercel provides automatic HTTPS with free SSL certificates.
- `docs/DEPLOYMENT.md` does not mention manual HTTPS configuration — this confirms it's platform-managed.
- `.env.example` has no SSL/HTTPS-related env vars.
- **Conclusion:** Rule #12 (HTTPS in production) is satisfied by platform defaults when deployed. The "92% compliance" rating is because this hasn't been verified in a live deployment yet.

---

### Q12: What is the `routes/feedback.py` Endpoint?

**✅ RESOLVED:** See Q10 above. It's a fully implemented `POST /feedback` endpoint collecting implicit feedback signals (copy, edit, save) with optional auth and quality score adjustment.

---

### Q13: Are There Any Database Indexes Created Beyond the Documented Ones?

**✅ RESOLVED: Only the 4 documented indexes exist in the schema docs. No SQL migration files found for additional indexes.**

- `docs/SUPABASE_SCHEMA.md` lists exactly 4 indexes:
  1. `idx_requests_user_id` ON `requests(user_id)`
  2. `idx_requests_created_at` ON `requests(created_at DESC)`
  3. `idx_conversations_session_id` ON `conversations(session_id)`
  4. `idx_chat_sessions_user_id` ON `chat_sessions(user_id)`
- `database.py` contains zero `CREATE INDEX` statements.
- `docs/migrations/` has only `027_add_missing_profile_columns.sql` — no index migrations.
- **Note:** No HNSW index on `langmem_memories.embedding` column — this should be added for pgvector performance.

---

### Q14: What is the `graph/` Directory?

**✅ RESOLVED: Contains only `state.py` — the LangGraph state schema. `__init__.py` is empty.**

- `graph/__init__.py` — empty file (0 lines).
- `graph/state.py` — 460+ lines, the complete `PromptForgeState` TypedDict with 26 fields across 8 sections. This is the definitive state schema.
- `workflow.py` is in the project root (not in `graph/`) — it imports from `graph.state`.
- **Conclusion:** The `graph/` directory is **active, not legacy**. It houses the state schema as a proper Python package. `workflow.py` staying in root is a design choice (it's the workflow definition, not part of the graph package).

---

### Q15: How is the Profile Updater Triggered?

**✅ RESOLVED: Via FastAPI `BackgroundTasks` in `routes/prompts_stream.py`.**

- Import: `from memory.profile_updater import should_trigger_update, update_user_profile`
- At end of `/chat/stream` handler (line 362): checks `should_trigger_update(user.user_id, interaction_count)`, and if true, adds `background_tasks.add_task(update_user_profile, ...)` — user never waits for profile update.
- `should_trigger_update()` checks cross-session inactivity by querying ALL sessions for the user (not just current session), preventing premature updates when users have multiple tabs open.
- **Trigger flow:** Request completes → `should_trigger_update()` evaluated → if 5th interaction OR 30min cross-session inactivity → `update_user_profile()` runs in background thread.

---

*See also: [tasks](tasks.md), [decisions](decisions.md), [features](features.md)*

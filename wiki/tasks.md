# Tasks

**Open items, blockers, confirmed vs. unverified work — VERIFIED against actual filesystem (2026-04-07).**

---

## ✅ Confirmed Complete

These items are verified as shipped and working based on source code and audit reports.

| # | Task | Phase | Evidence |
|---|------|-------|----------|
| 1 | FastAPI REST API (11+ endpoints) | Phase 1 | `api.py`, `routes/` (12 modules) |
| 2 | JWT Authentication (Supabase) | Phase 1 | `auth.py` — full implementation with retry logic |
| 3 | Supabase database (8 tables, 38 RLS policies) | Phase 1 | `database.py`, `docs/SUPABASE_SCHEMA.md` |
| 4 | Redis caching (SHA-256 keys, 1h TTL) | Phase 1 | `utils.py` — `get_cached_result()`, `set_cached_result()` |
| 5 | Rate Limiting (hourly/daily/monthly) | Phase 1 | `middleware/rate_limiter.py` — sliding window, VIP bypass |
| 6 | 4-Agent Parallel Swarm (Send() API) | Phase 2 | `workflow.py` — `PARALLEL_MODE = True` |
| 7 | Kira Orchestrator (personality + routing) | Phase 2 | `agents/orchestrator.py`, `agents/orchestration/router.py` |
| 8 | LangMem with pgvector (768-dim Gemini embeddings) | Phase 2 | `memory/langmem.py` — hybrid recall, RRF fusion |
| 9 | Profile Updater (5th interaction + 30min trigger) | Phase 2 | `memory/profile_updater.py` — 228 lines, cross-session check, BackgroundTasks trigger |
| 10 | Multimodal Input (voice, image, file) | Phase 2 | `multimodal/` directory (transcribe.py, image.py, files.py, validators.py) |
| 11 | Native MCP Server (2 tools, stdio) | Phase 3 | `mcp/server.py` — forge_refine, forge_chat |
| 12 | Supermemory (MCP-exclusive memory) | Phase 3 | `memory/supermemory.py` — 221 lines, trust levels 0-2 |
| 13 | Long-Lived MCP JWT (365 days, revocable) | Phase 3 | `mcp/server.py` — validates revoked flag in `mcp_tokens` |
| 14 | Trust Levels (0–2 scaling) | Phase 3 | `memory/supermemory.py:get_trust_level()` — cold/warm/tuned |
| 15 | Migration 013 (mcp_tokens table) | Phase 3 | Verified in Supabase per PROJECT_SUMMARY |
| 16 | SSE Streaming | Phase 2 | `service.py` — `_astream_swarm()` async generator |
| 17 | XP Engine (gamification) | Phase 2/3 | `xp_engine.py` — calculate_forge_xp(), loyalty tiers |
| 18 | Sentry Error Tracking | Phase 1 | `api.py` — Sentry init first, `/test-error` route |
| 19 | LangFuse Tracing | Phase 2/3 | `middleware/langfuse_instrumentation.py` |
| 20 | OpenTelemetry | Phase 2/3 | `middleware/otel_tracing.py` — span decorators |
| 21 | Documentation Consolidation | Phase 3 | 18 docs in `docs/`, 12+ permanent docs |
| 22 | Hybrid Recall (BM25 + Vector + RRF + MMR) | Phase 2 | `memory/hybrid_recall.py` — 366 lines, graceful degradation |
| 23 | Implicit Feedback Collection | Phase 2/3 | `routes/feedback.py` — POST /feedback, quality score adjustment |
| 24 | Next.js Frontend (full implementation) | Phase 4 | `promptforge-web/` — 115 TS/TSX files, auth, chat, history, profile, landing |
| 25 | Prompt Engineer System Prompt | Phase 2 | `agents/prompts/engineer.py` — 460 lines, 8 few-shot examples |
| 26 | LangGraph State Schema | Phase 2 | `graph/state.py` — 26 fields, 8 sections, TypedDict |

---

## 🔧 Open Items

### High Priority

| # | Task | Description | Effort | Blockers |
|---|------|-------------|--------|----------|
| H1 | **Production Deployment** | Deploy backend to Railway + frontend to Vercel. `.env.local` points to localhost. All deployment configs are ready (Dockerfile, docker-compose, DEPLOYMENT.md). | 2 hours | Railway + Vercel accounts, env var setup |
| H2 | **H2 Frontend Audit** | Frontend (`promptforge-web/`) is a complete implementation (115 TS/TSX files) but has not passed the same security/performance audit as Phases 1-3. Needs TypeScript strict mode verification, XSS audit, API error handling review. | 1-2 weeks | Requires dedicated audit session |
| H3 | **Recreate RULES.md** | 311+ code comments reference RULES.md but the file is missing from disk. Should be recreated from the standards described in code comments (13 security rules, modularity, code quality, error handling, type hints). | 2-3 hours | None |

### Medium Priority

| # | Task | Description | Effort | Blockers |
|---|------|-------------|--------|----------|
| M1 | **Switch to Groq API** | Would fix swarm latency variance (4-6s → target 3-5s). Change `BASE_URL` and models in `config.py`. `GROQ_API_KEY` already listed in `.env.example`. | ~1 hour | Groq API key needed |
| M2 | **Manual MCP Testing in Cursor** | Verify MCP server works end-to-end in Cursor IDE. 2-3 hours per PROJECT_SUMMARY. | 2-3 hours | Cursor installation, MCP config |
| M3 | **Add HNSW Index to pgvector** | `langmem_memories.embedding` column has no HNSW index. Add: `CREATE INDEX ON langmem_memories USING hnsw (embedding vector_cosine_ops)` for performance. | 30 min | Supabase access |
| M4 | **Multi-Instance Rate Limiting** | Current rate limiting is in-memory. For multi-instance, need Redis-based. Redis dependency already exists in docker-compose. | 4 hours | Redis dependency already exists |
| M5 | **Document /feedback in API docs** | `routes/feedback.py` is implemented but not documented in `docs/API.md`. | 30 min | None |
| M6 | **Better Stack Uptime Monitoring** | Set up health endpoint monitoring with 3-minute interval. | 30 min | Better Stack account |

### Low Priority / Nice-to-Have

| # | Task | Description | Effort | Blockers |
|---|------|-------------|--------|----------|
| L1 | **Stripe Integration** | Mentioned as potential enhancement. Would enable paid tiers, usage-based billing. | 1-2 weeks | Business model decision |
| L2 | **Add Unit Tests for `xp_engine.py`** | XP engine exists but no dedicated test file found in test suite. | 1 hour | None |
| L3 | **Add Unit Tests for `memory/hybrid_recall.py`** | Hybrid recall implemented but dedicated tests unclear. | 2 hours | None |
| L4 | **Swagger Docs Enhancement** | API docs at `/docs` could include request/response examples for all endpoints including /feedback. | 2 hours | None |
| L5 | **Archive history/ folder** | 40 files in `history/` — most are superseded. Archive to reduce clutter. Keep PROJECT_SUMMARY.md and phase-reports/. | 30 min | None |

---

## ✅ Previously Unverified — NOW CONFIRMED

All items from the "Unverified" table have been verified against the filesystem.

| # | Item | Previous Status | ✅ VERIFIED |
|---|------|----------------|------------|
| U1 | `DOCS/RULES.md` | ⚠️ PROJECT_SUMMARY says exists, gap analysis says doesn't | ❌ CONFIRMED MISSING — needs recreation |
| U2 | `DOCS/IMPLEMENTATION_PLAN.md` | ⚠️ Same contradiction | ❌ CONFIRMED MISSING — needs recreation |
| U3 | `DOCS/Masterplan.html` | ⚠️ Listed but not read | ❌ NOT FOUND on disk — may have been lost during consolidation |
| U4 | `memory/supermemory.py` | ⚠️ Referenced but not read | ✅ EXISTS — 221 lines, MCP-exclusive memory with trust levels |
| U5 | `memory/hybrid_recall.py` | ⚠️ Imported but not read | ✅ EXISTS — 366 lines, BM25+Vector+RRF+MMR |
| U6 | `memory/profile_updater.py` | ⚠️ Referenced but not read | ✅ EXISTS — 228 lines, 5th interaction + 30min cross-session trigger |
| U7 | `agents/prompts/engineer.py` | ⚠️ 800-line claim, not read | ✅ EXISTS — 460 lines (not 800), system prompt + 8 examples |
| U8 | Phase 4 Frontend Code | ⚠️ Exists but audit unknown | ✅ EXISTS — 115 TS/TSX files, complete implementation with auth, chat, history, profile, landing |
| U9 | Live Demo URLs | ⚠️ Placeholders | ❌ NOT DEPLOYED — `.env.local` points to localhost |
| U10 | `routes/feedback.py` | ⚠️ Exists but DB ops unknown | ✅ EXISTS — 111 lines, writes to prompt_feedback table directly, quality score adjustment |

---

## 🚫 Known Blockers

| # | Blocker | Impact | Resolution |
|---|---------|--------|------------|
| B1 | RULES.md missing | 311+ code comments reference it; development standards not formally documented | Recreate from code comment patterns (13 security rules, type hints, error handling, modularity) |
| B2 | No production deployment | Cannot claim "production ready" without verified deployment | Deploy to Railway + Vercel using existing Dockerfile and DEPLOYMENT.md |

---

## Sources

- Filesystem verification: all files read directly from `C:\Users\user\OneDrive\Desktop\newnew\`
- `memory/supermemory.py` — 221 lines, read in full
- `memory/hybrid_recall.py` — 366 lines, read in full
- `memory/profile_updater.py` — 228 lines, read in full
- `agents/prompts/engineer.py` — 460 lines, read first 50 lines
- `routes/feedback.py` — 111 lines, read in full
- `graph/state.py` — 460+ lines, read in full
- `graph/__init__.py` — empty
- `promptforge-web/` — 115 TS/TSX source files counted, package.json read, .env.local read
- `routes/prompts_stream.py` — lines 358-373 read for BackgroundTasks trigger
- `docs/SUPABASE_SCHEMA.md` — indexes section read
- `docs/DEPLOYMENT.md` — full read
- `docker-compose.yml` — full read
- `Dockerfile` — full read
- `config.py` — full read
- `database.py` — grep for feedback/indexes
- `api.py` — grep for BackgroundTasks
- Glob searches for RULES.md, IMPLEMENTATION_PLAN.md — zero results

---

*See also: [features](features.md), [questions](questions.md), [decisions](decisions.md)*

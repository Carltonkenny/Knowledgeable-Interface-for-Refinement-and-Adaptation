# Tasks

**Open items, blockers, confirmed vs. unverified work.**

---

## ✅ Confirmed Complete

These items are verified as shipped and working based on source code and audit reports.

| # | Task | Phase | Evidence |
|---|------|-------|----------|
| 1 | FastAPI REST API (11 endpoints) | Phase 1 | `api.py`, `routes/` (12 modules) |
| 2 | JWT Authentication (Supabase) | Phase 1 | `auth.py` — full implementation with retry logic |
| 3 | Supabase database (8 tables, 38 RLS policies) | Phase 1 | `database.py` (897 lines), `docs/SUPABASE_SCHEMA.md` |
| 4 | Redis caching (SHA-256 keys, 1h TTL) | Phase 1 | `utils.py` — `get_cached_result()`, `set_cached_result()` |
| 5 | Rate Limiting (100 req/hour) | Phase 1 | `middleware/rate_limiter.py` — hourly/daily/monthly |
| 6 | 4-Agent Parallel Swarm (Send() API) | Phase 2 | `workflow.py` — `PARALLEL_MODE = True` |
| 7 | Kira Orchestrator (personality + routing) | Phase 2 | `agents/orchestrator.py`, `agents/orchestration/router.py` |
| 8 | LangMem with pgvector (768-dim Gemini embeddings) | Phase 2 | `memory/langmem.py` — hybrid recall, RRF fusion |
| 9 | Profile Updater (5th interaction + 30min trigger) | Phase 2 | `memory/profile_updater.py` (referenced in agents/README) |
| 10 | Multimodal Input (voice, image, file) | Phase 2 | `multimodal/` directory (transcribe.py, image.py, files.py, validators.py) |
| 11 | Native MCP Server (685 lines, 2 tools) | Phase 3 | `mcp/server.py` — forge_refine, forge_chat |
| 12 | Supermemory (MCP-exclusive memory) | Phase 3 | Referenced in `mcp/server.py`, `memory/supermemory.py` |
| 13 | Long-Lived MCP JWT (365 days, revocable) | Phase 3 | `mcp/server.py` — `validate_mcp_jwt()` checks revoked flag |
| 14 | Trust Levels (0–2 scaling) | Phase 3 | `mcp/server.py` — `_get_trust_message()` |
| 15 | Migration 013 (mcp_tokens table) | Phase 3 | Verified in Supabase per PROJECT_SUMMARY |
| 16 | SSE Streaming | Phase 2 | `service.py` — `_astream_swarm()` async generator |
| 17 | XP Engine (gamification) | Phase 2/3 | `xp_engine.py` — calculate_forge_xp(), loyalty tiers |
| 18 | Sentry Error Tracking | Phase 1 | `api.py` — Sentry init first, `/test-error` route |
| 19 | LangFuse Tracing | Phase 2/3 | `middleware/langfuse_instrumentation.py` — `trace_swarm_run()` |
| 20 | OpenTelemetry | Phase 2/3 | `middleware/otel_tracing.py` — span decorators on db/cache |
| 21 | Documentation Consolidation | Phase 3 | 12 permanent docs (from 25+), git commit `6336c6b` |
| 22 | Test Consolidation | Phase 3 | 10 test files (from 30+), 179 total tests passing |

---

## 🔧 Open Items

### High Priority

| # | Task | Description | Effort | Blockers |
|---|------|-------------|--------|----------|
| H1 | **Resolve RULES.md/IMPLEMENTATION_PLAN.md existence** | These files are referenced extensively in code comments and PROJECT_SUMMARY but gap analysis says they don't exist on disk. Need to verify actual location or recreate from audit reports. | 30 min | None |
| H2 | **Phase 4 Frontend Audit** | Frontend exists (`promptforge-web/`) but has not been audited to the same standard as Phases 1–3. Needs security review, performance audit, TypeScript strict mode check. | 1–2 weeks | Requires dedicated audit session |
| H3 | **Production Deployment Verification** | Deployment docs reference Railway + Vercel but live URLs are placeholders. Need to verify if production was ever deployed or if it's still pending. | 1 hour | Access to Railway/Vercel dashboards |

### Medium Priority

| # | Task | Description | Effort | Blockers |
|---|------|-------------|--------|----------|
| M1 | **Switch to Groq API** | Would fix swarm latency variance (4–6s → target 3–5s). Change `BASE_URL` and models in `config.py`. ~1 hour effort per PROJECT_SUMMARY. | 1 hour | Groq API key needed |
| M2 | **Manual MCP Testing in Cursor** | Verify MCP server works end-to-end in Cursor IDE. 2–3 hours per PROJECT_SUMMARY. | 2–3 hours | Cursor installation, MCP config |
| M3 | **Implement `prompt_feedback` Table Operations** | Table exists in schema but no CRUD operations found in `database.py` or routes. Either implement or remove unused table. | 2 hours | Decision on whether to keep |
| M4 | **Multi-Instance Rate Limiting** | Current rate limiting is in-memory. For multi-instance deployments, need Redis-based rate limiting. | 4 hours | Redis dependency already exists |
| M5 | **Better Stack Uptime Monitoring** | Referenced in deployment docs but unclear if configured. Set up health endpoint monitoring with 3-minute interval. | 30 min | Better Stack account |

### Low Priority / Nice-to-Have

| # | Task | Description | Effort | Blockers |
|---|------|-------------|--------|----------|
| L1 | **Stripe Integration** | Mentioned as potential enhancement. Would enable paid tiers, usage-based billing. | 1–2 weeks | Business model decision |
| L2 | **Add Unit Tests for `xp_engine.py`** | XP engine exists but no dedicated test file found in test suite. | 1 hour | None |
| L3 | **Add Unit Tests for `memory/hybrid_recall.py`** | Hybrid recall referenced in langmem.py but dedicated tests unclear. | 2 hours | None |
| L4 | **Swagger Docs Enhancement** | API docs at `/docs` exist but could include request/response examples for all 11 endpoints. | 2 hours | None |
| L5 | **Docker Compose for Full Stack** | Current compose file may only include backend. Could add frontend, Redis, Jaeger for local dev. | 4 hours | None |

---

## ⚠️ Unverified / Referenced but Not Confirmed

These items are mentioned in documentation or code comments but their actual existence/status could not be confirmed from source files.

| # | Item | Referenced In | Status | Action Needed |
|---|------|---------------|--------|---------------|
| U1 | `DOCS/RULES.md` | Code comments, agents/README, PROJECT_SUMMARY | ⚠️ PROJECT_SUMMARY says exists (1,570 lines). Gap analysis says doesn't exist on disk. | Search filesystem or recreate |
| U2 | `DOCS/IMPLEMENTATION_PLAN.md` | PROJECT_SUMMARY | ⚠️ Same contradiction as RULES.md | Search filesystem or recreate |
| U3 | `DOCS/Masterplan.html` | PROJECT_SUMMARY | ⚠️ Listed as core documentation but not read | Verify existence |
| U4 | `memory/supermemory.py` | mcp/server.py, PROJECT_SUMMARY | ⚠️ Referenced but not read during wiki creation | Read and verify implementation |
| U5 | `memory/hybrid_recall.py` | memory/langmem.py | ⚠️ Imported in langmem.py but not read | Read and verify implementation |
| U6 | `memory/profile_updater.py` | agents/README.md, PROJECT_SUMMARY | ⚠️ Referenced but not read | Read and verify implementation |
| U7 | `agents/prompts/engineer.py` | agents/README.md | ⚠️ 800-line system prompt referenced but not read | Verify content |
| U8 | Phase 4 Frontend Code | PROJECT_SUMMARY "Optional Enhancements" | ⚠️ Frontend exists but audit status unknown | Audit `promptforge-web/` |
| U9 | Live Demo URLs | README.md | ⚠️ URLs are placeholders ("after deployment") | Deploy or update docs |
| U10 | `routes/feedback.py` | routes directory listing | ⚠️ File exists but no schema implementation in database.py | Verify feedback table operations |

---

## 🚫 Known Blockers

| # | Blocker | Impact | Resolution |
|---|---------|--------|------------|
| B1 | RULES.md missing | Cannot enforce development standards without the authoritative rules document | Locate or recreate from audit reports |
| B2 | Production deployment uncertain | Cannot claim "production ready" without verified production deployment | Deploy to Railway + Vercel or update status |

---

## Sources

- `history/PROJECT_SUMMARY.md` — Phase completion status, optional enhancements, metrics, optional next steps
- `README.md` — Live demo URLs (placeholders), deployment references
- `docs/DEPLOYMENT.md` — Deployment steps, monitoring setup (Better Stack referenced)
- `docs/API.md` — Endpoint list, rate limits
- `docs/SUPABASE_SCHEMA.md` — Database tables (prompt_feedback listed but not implemented)
- `api.py` — Registered route modules (routes/ has 12 files)
- `database.py` — Database operations (no prompt_feedback CRUD found)
- `middleware/rate_limiter.py` — In-memory rate limiting, multi-instance note
- `agents/README.md` — Agent system references to RULES.md, supermemory, profile_updater
- `mcp/server.py` — Supermemory references
- `memory/langmem.py` — Hybrid recall references

---

*See also: [features](features.md), [questions](questions.md), [decisions](decisions.md)*

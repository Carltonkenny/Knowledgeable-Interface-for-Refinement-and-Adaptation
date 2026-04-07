# Wiki Creation Log

**Initial wiki structure creation for PromptForge v2.0**

---

## Entry 1 — 2026-04-07

### What Was Done

Created the production-ready wiki structure using the `raw/` + `wiki/` pattern. This is the **initial creation** — no existing files were modified, moved, or deleted.

### Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `raw/.gitkeep` | Empty marker for raw sources folder | 0 |
| `wiki/index.md` | Table of contents, project metadata, quick links | ~70 |
| `wiki/overview.md` | What PromptForge is, who it's for, v2.0 status, key metrics | ~120 |
| `wiki/architecture.md` | Full system architecture: Kira, swarm, LangGraph, Supabase, Redis, middleware, MCP, Next.js, Docker | ~280 |
| `wiki/features.md` | Shipped features (22 confirmed), planned features (6), uncertainties (9) | ~130 |
| `wiki/decisions.md` | 15 key architectural/design decisions with rationale and evidence | ~200 |
| `wiki/tasks.md` | 22 confirmed complete, 14 open items (3H/5M/6L), 10 unverified, 2 blockers | ~130 |
| `wiki/questions.md` | 15 open questions: 3 contradictions, 5 missing files, 7 engineering questions | ~180 |
| `wiki/log.md` | This file — creation log | — |

### Sources Read

The following source files were read to populate the wiki with real, detailed content:

| Source | Lines Read | Key Information Extracted |
|--------|-----------|--------------------------|
| `README.md` | Full | Project overview, features, tech stack, performance metrics, architecture diagram, placeholder URLs |
| `docs/API.md` | Full | 11 endpoints, rate limits, error codes, auth requirements |
| `docs/DEPLOYMENT.md` | Full | Railway + Vercel deployment steps, env vars, monitoring setup |
| `docs/SUPABASE_SCHEMA.md` | Full | 8 tables, RLS policies, indexes, required extensions |
| `agents/README.md` | Full | Agent public API, module structure, quality metrics, temperature/token constants |
| `history/PROJECT_SUMMARY.md` | Full | Phase completion status, database tables, security compliance, metrics, optional enhancements |
| `state.py` | Full | 27-field PromptForgeState schema, 5 sections, merge_dict reducer |
| `workflow.py` | Full | LangGraph StateGraph with Send() parallel execution, node registration |
| `api.py` | Full | App factory, middleware stack, Sentry init, route registration |
| `service.py` | Full | _run_swarm, _astream_swarm, _run_swarm_with_clarification, compute_diff, sse_format |
| `auth.py` | Full | JWT auth with Supabase, retry logic, User model |
| `config.py` | Full | LLM factory, Pollinations Gen API, model configuration, lru_cache |
| `database.py` | 762 of 897 | All Supabase operations, auto-versioning, session management, user profiles, clarification flags |
| `utils.py` | Full | Redis caching (SHA-256), JSON parsing, format_history, calculate_overall_quality |
| `xp_engine.py` | Full | XP calculation, loyalty tiers, streak multipliers, polymath/teaching bonuses |
| `mcp/server.py` | Full | MCP server with 2 tools, trust levels, JWT validation, surface isolation |
| `memory/langmem.py` | Full | Gemini embeddings (768 dims), hybrid recall, quality trends, image description |
| `middleware/rate_limiter.py` | Full | Sliding window rate limiting, hourly/daily/monthly, VIP bypass, master toggle |
| `routes/` directory | Listing | 12 route modules identified |

### Conventions Established

- **Filenames:** kebab-case for all wiki pages
- **Uncertainties:** Marked with `⚠️ UNCERTAIN:` prefix
- **Sources section:** Every page ends with `## Sources` listing raw files used
- **Backlinks:** Pages include "See also:" links to related pages
- **Relative links:** All inter-wiki links use relative paths (e.g., `[architecture](architecture.md)`)
- **Tables:** Used extensively for structured data presentation
- **Code references:** File paths and function names in backticks

### Notes

- The `raw/` folder is a **conceptual label** — existing raw source files in `docs/` and `history/` were NOT moved. The `raw/.gitkeep` simply marks the conceptual boundary.
- Some source files were truncated during reading (e.g., `database.py` at line 762 of 897). Content from the truncated portion may be incomplete.
- Files NOT read but referenced in wiki pages: `memory/supermemory.py`, `memory/hybrid_recall.py`, `memory/profile_updater.py`, `agents/prompts/engineer.py`, individual route modules, `routes/feedback.py`

---

*Wiki created by PromptForge Development Orchestrator. All content derived from actual source files.*

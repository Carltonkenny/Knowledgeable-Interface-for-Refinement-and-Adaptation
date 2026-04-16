# PromptForge Wiki

**Multi-agent AI prompt engineering platform — v2.0.0**

| | |
|---|---|
| **Version** | 2.0.0 |
| **Status** | Production Ready (Phases 1-3 complete). Phase 4 Frontend: Complete implementation (not deployed) |
| **Last Updated** | 2026-04-07 |
| **Last Verified** | 2026-04-07 — Deep verification pass: all 15 questions resolved against filesystem |
| **Backend** | FastAPI, Python 3.11, LangGraph 0.2.39, LangChain 0.3.7 |
| **LLM** | Pollinations Gen API (OpenAI-compatible) |
| **Embeddings** | Google Gemini (gemini-embedding-001, 768 dims) |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **Cache** | Redis (Upstash) |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS — 115 source files |
| **Auth** | Supabase JWT (ES256/HS256) |
| **Monitoring** | Sentry, LangFuse, OpenTelemetry |
| **Deployment** | Railway (backend), Vercel (frontend) — configs ready, NOT deployed |
| **Containerization** | Docker multi-stage, Docker Compose |
| **MCP** | 2 tools (forge_refine, forge_chat) for Cursor/Claude Desktop |

---

## Table of Contents

### Core Documentation
- [Overview](overview.md) — What PromptForge is, who it's for, v2.0 status and scope
- [Architecture](architecture.md) — Full system architecture: Kira, swarm, LangGraph, Supabase, Redis, MCP, Next.js, Docker
- [Features](features.md) — Shipped features, planned features, and uncertainties

### Project Management
- [Decisions](decisions.md) — Key architectural and design decisions, when and why they were made
- [Tasks](tasks.md) — Open items, blockers, confirmed vs. unverified work
- [Questions](questions.md) — Contradictions, missing files, open engineering questions

### Raw Sources
- [Creation Log](log.md) — When this wiki was created, what sources were used

---

## Note on Raw Sources

This wiki is derived from the project's **raw sources** located in:
- `docs/` — Permanent documentation (API, deployment, schema, rules, plans)
- `history/` — Historical audit reports, phase summaries, specs (40+ files)

The `raw/` folder is a conceptual label documented in this wiki. Raw source files have **not** been moved or modified. All wiki pages include a `## Sources` section listing the specific raw files used.

---

## Quick Links to Raw Documentation

| Doc | Path | Description |
|-----|------|-------------|
| README | `README.md` | Project overview, quick start |
| API Reference | `docs/API.md` | All 11 endpoint docs |
| Deployment | `docs/DEPLOYMENT.md` | Railway + Vercel deployment |
| Database Schema | `docs/SUPABASE_SCHEMA.md` | Supabase tables and RLS |
| Agent System | `agents/README.md` | Agent public API, usage examples |
| Project Summary | `history/PROJECT_SUMMARY.md` | Phase completion status, metrics |

---

*Wiki created following the raw/ + wiki/ pattern. No existing files were modified, moved, or deleted.*

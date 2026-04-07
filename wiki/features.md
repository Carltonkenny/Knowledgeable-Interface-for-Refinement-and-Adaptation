# Features

**Shipped features, planned features, and known uncertainties.**

---

## ✅ Shipped Features

### Core Prompt Engineering
| Feature | Description | Status |
|---------|-------------|--------|
| **Multi-Agent Swarm** | 4 specialized agents (Intent, Context, Domain, Prompt Engineer) running in parallel via LangGraph `Send()` API | ✅ Shipped |
| **Kira Orchestrator** | Personality-driven routing agent that analyzes intent, checks memory, and decides routing | ✅ Shipped |
| **Quality Scoring** | Every engineered prompt includes quality metrics: specificity, clarity, actionability (1–5 scale) | ✅ Shipped |
| **Word-Level Diff** | `difflib.SequenceMatcher` computes add/remove/keep diff for frontend DiffView component | ✅ Shipped |
| **Clarification Loop** | Kira can ask clarifying questions before proceeding with swarm; `_run_swarm_with_clarification()` skips orchestrator | ✅ Shipped |

### Memory & Personalization
| Feature | Description | Status |
|---------|-------------|--------|
| **LangMem** | Long-term persistent memory with pgvector semantic search. Google Gemini embeddings (768 dims). Hybrid recall (BM25 + vector) with RRF fusion | ✅ Shipped |
| **Supermemory** | MCP-exclusive memory layer. Surface isolation: LangMem NEVER on MCP, Supermemory NEVER on web app | ✅ Shipped |
| **Profile Updater** | Updates user preferences every 5th interaction + 30min inactivity trigger. Tracks dominant_domains, preferred_tone, clarification_rate | ✅ Shipped |
| **Conversational Memory** | Session history loaded from Supabase `conversations` table, last 6 turns (3 exchanges) | ✅ Shipped |
| **Quality Trend Tracking** | Analyzes last N sessions, compares first-half vs second-half avg quality. Returns 'improving' | ✅ Shipped |

### Multimodal Input
| Feature | Description | Status |
|---------|-------------|--------|
| **Voice Processing** | Voice input transcribed to text before swarm processing | ✅ Shipped |
| **Image Processing** | Image attachments described via Gemini Vision, embedded for semantic search | ✅ Shipped |
| **File Processing** | File upload with text extraction, base64 handling, size limits enforced first | ✅ Shipped |

### API & Integration
| Feature | Description | Status |
|---------|-------------|--------|
| **SSE Streaming** | Server-Sent Events for real-time streaming responses. `_astream_swarm()` yields chunks incrementally | ✅ Shipped |
| **REST API** | 11 endpoints: health, chat/stream, refine, history, analytics, user profile, sessions, feedback, usage, MCP | ✅ Shipped |
| **MCP Server** | Native MCP server with 2 tools (forge_refine, forge_chat) for Cursor/Claude Desktop. stdio transport | ✅ Shipped |
| **MCP Trust Levels** | Progressive trust: 0 (cold) → 1 (warm) → 2 (tuned). Long-lived JWT (365 days), revocable | ✅ Shipped |
| **Redis Caching** | SHA-256 cache keys, 1-hour TTL, per-user personalization, schema versioning | ✅ Shipped |

### Auth & Security
| Feature | Description | Status |
|---------|-------------|--------|
| **JWT Authentication** | Supabase JWT (ES256/HS256), retry logic for transient errors | ✅ Shipped |
| **Row Level Security** | 38 RLS policies across 8 tables. User isolation enforced at database level | ✅ Shipped |
| **Rate Limiting** | Per-user: hourly (10), daily (50), monthly (1500). Sliding window algorithm. Master toggle + VIP bypass | ✅ Shipped |
| **CORS** | Locked to `FRONTEND_URLS` env var (no wildcard). Credentials enabled | ✅ Shipped |
| **Input Validation** | 5–2000 char prompt validation, file size limits, JSON parsing with 3 failure modes + exponential backoff | ✅ Shipped |

### Monitoring & Analytics
| Feature | Description | Status |
|---------|-------------|--------|
| **Sentry** | Error tracking with FastAPI integration. 10% transaction sampling. Test endpoint `/test-error` (dev only) | ✅ Shipped |
| **LangFuse** | Swarm execution tracking: agents run/skipped, latencies, quality scores, domain, session_id | ✅ Shipped |
| **OpenTelemetry** | Distributed tracing with Jaeger. Span decorators on database operations, cache operations | ✅ Shipped |
| **LangSmith** | LangChain native tracing. Every LLM call traced automatically when `LANGCHAIN_TRACING_V2=true` | ✅ Shipped |
| **Analytics API** | `/history/analytics` endpoint: total prompts, avg quality, unique domains, hours saved, quality trends, domain distribution | ✅ Shipped |

### Gamification
| Feature | Description | Status |
|---------|-------------|--------|
| **XP Engine** | `xp_engine.py` — calculates XP based on quality score, polymath bonus (+25 for new domains), teaching bonus (+15 for clarification), streak multiplier (1.2x at 3 days, 1.5x at 7 days) | ✅ Shipped |
| **Loyalty Tiers** | Bronze (Analyst) 0 XP → Silver (Practitioner) 500 XP → Gold (Architect) 2000 XP → Kira-Class (Forge-Master) 5000 XP | ✅ Shipped |
| **Session Management** | Create, pin, favorite, soft-delete, restore, purge sessions. Auto-versioning with parent_version_id | ✅ Shipped |

### Database
| Feature | Description | Status |
|---------|-------------|--------|
| **8 Tables** | requests, conversations, chat_sessions, user_profiles, agent_logs, langmem_memories, prompt_feedback, mcp_tokens | ✅ Shipped |
| **13 Migrations** | 001–009 (Phase 1–2 tables + RLS), 010 (LangMem embedding), 011 (user sessions), 012 (Supermemory), 013 (MCP tokens — verified) | ✅ Shipped |
| **Auto-Versioning** | requests table: version_id, version_number, parent_version_id, is_production, change_summary | ✅ Shipped |

---

## 📋 Planned Features

### Optional Enhancements (from `history/PROJECT_SUMMARY.md`)

| Feature | Description | Effort | Status |
|---------|-------------|--------|--------|
| **Switch to Groq API** | Would fix swarm latency variance (currently 4–6s vs target 3–5s). Pollinations API is the bottleneck, not code quality | ~1 hour | ⚠️ Not started |
| **Manual MCP Testing in Cursor** | Verify MCP server works end-to-end in Cursor IDE | 2–3 hours | ⚠️ Not started |
| **Phase 4 Frontend** | Full React/Next.js frontend implementation and audit | 1–2 weeks | ⚠️ Status unclear — frontend exists but audit status unknown |
| **Deploy to Production** | Docker + Fly.io deployment | 2 hours | ⚠️ Referenced as "TODO" in docs, may not have been executed |

### Referenced but Unverified

| Feature | Description | Status |
|---------|-------------|--------|
| **Stripe Integration** | Mentioned in gap analysis as a potential enhancement | ⚠️ Referenced but no implementation found |
| **Better Stack Monitoring** | Mentioned in deployment docs for uptime monitoring | ⚠️ Referenced but unclear if configured |

---

## ⚠️ Uncertainties

| Uncertainty | Details |
|-------------|---------|
| **Phase 4 Frontend Status** | Frontend (`promptforge-web/`) exists with Next.js 16, App Router, components, features. But it's unclear whether it has passed the same rigorous audit as Phases 1–3. The PROJECT_SUMMARY only lists Phases 1–3 as complete. |
| **RULES.md Location** | Referenced extensively in code comments as `DOCS/RULES.md` and `RULES.md`. PROJECT_SUMMARY says it exists at `DOCS/RULES.md` (1,570 lines). But the gap analysis says "RULES.md and IMPLEMENTATION_PLAN.md referenced in code comments but don't exist on disk." ⚠️ Contradiction needs resolution. |
| **IMPLEMENTATION_PLAN.md Location** | Same issue — referenced as `DOCS/IMPLEMENTATION_PLAN.md` in PROJECT_SUMMARY, but gap analysis says it doesn't exist on disk. |
| **Deployment Status** | Deployment docs reference Railway + Vercel as targets, but live demo URLs are placeholders ("after deployment"). Unclear if production deployment was ever completed. |
| **Swarm Latency** | Actual 4–6s vs target 3–5s (+20% over). Attributed to Pollinations API, not code quality. Groq swap would fix this. |
| **HTTPS in Production** | RULES.md Security Rule #12 is the only failing rule (out of 13). Marked as "deployment responsibility" — unclear if Railway/Vercel handle this automatically. |
| **Prompt Feedback Table** | `prompt_feedback` table listed in schema but no implementation found in `database.py` or routes. |
| **Supermemory Implementation** | Referenced in MCP server and PROJECT_SUMMARY, but `memory/supermemory.py` was not among the files read. |
| **Hybrid Recall Implementation** | `memory/hybrid_recall.py` referenced in `langmem.py` but not read directly. |

---

## Sources

- `README.md` — Features list, performance metrics, architecture diagram
- `history/PROJECT_SUMMARY.md` — Phase completion, optional enhancements, metrics
- `docs/API.md` — Endpoint documentation, rate limits
- `docs/DEPLOYMENT.md` — Monitoring tools (Sentry, Better Stack), deployment targets
- `docs/SUPABASE_SCHEMA.md` — Database tables, RLS policies
- `agents/README.md` — Agent system features, quality metrics
- `state.py` — State schema fields
- `workflow.py` — Parallel execution via Send()
- `service.py` — Swarm execution, diff computation, SSE formatting
- `config.py` — LLM models and configuration
- `database.py` — Database operations, auto-versioning, session management
- `utils.py` — Redis caching, quality scoring
- `xp_engine.py` — XP engine, loyalty tiers
- `mcp/server.py` — MCP tools, trust levels, surface isolation
- `memory/langmem.py` — LangMem, Gemini embeddings, hybrid recall, quality trends
- `middleware/rate_limiter.py` — Rate limiting (hourly/daily/monthly), VIP bypass
- `auth.py` — JWT authentication, retry logic
- `api.py` — Middleware stack, monitoring integrations

---

*See also: [overview](overview.md), [architecture](architecture.md), [tasks](tasks.md)*

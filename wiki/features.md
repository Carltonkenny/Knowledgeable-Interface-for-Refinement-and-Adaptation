# Features

**Shipped features, planned features, and uncertainties — VERIFIED against actual filesystem (2026-04-07).**

---

## ✅ Shipped Features

### Core Prompt Engineering
| Feature | Description | Status |
|---------|-------------|--------|
| **Multi-Agent Swarm** | 4 specialized agents (Intent, Context, Domain, Prompt Engineer) running in parallel via LangGraph `Send()` API | ✅ Shipped |
| **Kira Orchestrator** | Personality-driven routing agent that analyzes intent, checks memory, and decides routing | ✅ Shipped |
| **Quality Scoring** | Every engineered prompt includes quality metrics: specificity, clarity, actionability (1-5 scale) | ✅ Shipped |
| **Word-Level Diff** | `difflib.SequenceMatcher` computes add/remove/keep diff for frontend DiffView component | ✅ Shipped |
| **Clarification Loop** | Kira can ask clarifying questions before proceeding with swarm; `_run_swarm_with_clarification()` skips orchestrator | ✅ Shipped |
| **Prompt Engineer System Prompt** | `agents/prompts/engineer.py` — 460 lines with 8 few-shot examples and JSON response schema | ✅ Shipped |

### Memory & Personalization
| Feature | Description | Status |
|---------|-------------|--------|
| **LangMem** | Long-term persistent memory with pgvector semantic search. Google Gemini embeddings (768 dims). Hybrid recall (BM25 + vector) with RRF fusion | ✅ Shipped |
| **Hybrid Recall** | `memory/hybrid_recall.py` — 366 lines. BM25 keyword + vector semantic search with Reciprocal Rank Fusion and Maximal Marginal Relevance for diversity. Graceful degradation to vector-only if rank-bm25 unavailable | ✅ Shipped |
| **Supermemory** | `memory/supermemory.py` — 221 lines. MCP-exclusive memory layer. Surface isolation: LangMem NEVER on MCP, Supermemory NEVER on web app. Trust levels: 0 (cold, <10 sessions), 1 (warm, 10-30), 2 (tuned, 30+) | ✅ Shipped |
| **Profile Updater** | `memory/profile_updater.py` — 228 lines. Updates user preferences every 5th interaction OR 30min cross-session inactivity. Triggered via FastAPI BackgroundTasks in `routes/prompts_stream.py`. Tracks dominant_domains, quality_trend, clarification_rate, domain_confidence | ✅ Shipped |
| **Conversational Memory** | Session history loaded from Supabase `conversations` table, last 6 turns (3 exchanges) | ✅ Shipped |
| **Quality Trend Tracking** | Analyzes last N sessions, compares first-half vs second-half avg quality. Returns 'improving'/'declining'/'stable' via `get_quality_trend()` in langmem.py | ✅ Shipped |

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
| **REST API** | 12+ endpoints: health, chat/stream, refine, history, analytics, user profile, sessions, feedback, usage, MCP | ✅ Shipped |
| **MCP Server** | Native MCP server with 2 tools (forge_refine, forge_chat) for Cursor/Claude Desktop. stdio transport | ✅ Shipped |
| **MCP Trust Levels** | Progressive trust: 0 (cold) → 1 (warm) → 2 (tuned). Long-lived JWT (365 days), revocable | ✅ Shipped |
| **Redis Caching** | SHA-256 cache keys, 1-hour TTL, per-user personalization, schema versioning | ✅ Shipped |
| **Implicit Feedback** | `routes/feedback.py` — POST /feedback collects copy/edit/save signals. Adjusts user quality score (+0.08 copy, +0.10 save, +/-0.02-0.03 edit). Auth optional, direct DB insert | ✅ Shipped |

### Auth & Security
| Feature | Description | Status |
|---------|-------------|--------|
| **JWT Authentication** | Supabase JWT (ES256/HS256), retry logic for transient errors | ✅ Shipped |
| **Row Level Security** | 38 RLS policies across 8 tables. User isolation enforced at database level | ✅ Shipped |
| **Rate Limiting** | Per-user: hourly (10), daily (50), monthly (1500). Sliding window algorithm. Master toggle + VIP bypass | ✅ Shipped |
| **CORS** | Locked to `FRONTEND_URLS` env var (no wildcard). Credentials enabled | ✅ Shipped |
| **Input Validation** | 5-2000 char prompt validation, file size limits, JSON parsing with 3 failure modes + exponential backoff | ✅ Shipped |

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
| **13 Migrations** | 001-009 (Phase 1-2 tables + RLS), 010 (LangMem embedding), 011 (user sessions), 012 (Supermemory), 013 (MCP tokens — verified) | ✅ Shipped |
| **Auto-Versioning** | requests table: version_id, version_number, parent_version_id, is_production, change_summary | ✅ Shipped |
| **4 Performance Indexes** | idx_requests_user_id, idx_requests_created_at, idx_conversations_session_id, idx_chat_sessions_user_id | ✅ Shipped |

### Next.js Frontend (Phase 4)
| Feature | Description | Status |
|---------|-------------|--------|
| **Framework** | Next.js 16.1.6 (App Router), React 19, TypeScript 5.9.3, Tailwind CSS 3.4.17 | ✅ Shipped |
| **Source Size** | 115 TypeScript/TSX source files (excluding node_modules, .next, test files) | ✅ Shipped |
| **Authentication** | Supabase SSR auth with login, signup pages, session management | ✅ Shipped |
| **Chat Interface** | ChatContainer, MessageList, InputBar, KiraMessage, UserMessage, ThinkAccordion, AgentThought, ClarificationChips, DiffView, QualityScores, OutputCard | ✅ Shipped |
| **History** | HistoryList, HistorySearchBar, HistoryAnalyticsDashboard, QualityTrendBar, VersionHistory, VersionComparison | ✅ Shipped |
| **Profile** | ProfileHeader, SettingsTab, ActivityTab, UsageStats, MCP Token Management, Data Export, Password Change, Achievement Badges, Neural Expertise Radar, Prompt Heatmap, Quality Sparkline | ✅ Shipped |
| **Landing Page** | HeroSection, HowItWorks, Pricing, LiveDemo, MoatSection, Navigation | ✅ Shipped |
| **Onboarding** | LoginForm, SignupForm, OnboardingWizard | ✅ Shipped |
| **Error Handling** | ErrorBoundary component, Sentry integration | ✅ Shipped |
| **API Layer** | `lib/api.ts` — typed API client for backend communication | ✅ Shipped |
| **Testing** | Jest + Testing Library setup with coverage configuration | ✅ Shipped |
| **Deployment** | `.env.local` configured for local dev (localhost:8000). NOT deployed to Vercel. | ⚠️ Ready, not deployed |

---

## 📋 Planned Features

### Optional Enhancements

| Feature | Description | Effort | Status |
|---------|-------------|--------|--------|
| **Switch to Groq API** | Would fix swarm latency variance (currently 4-6s vs target 3-5s). Pollinations API is the bottleneck. `GROQ_API_KEY` already in `.env.example`. Config swap in `config.py`. | ~1 hour | ⚠️ Not started |
| **Manual MCP Testing in Cursor** | Verify MCP server works end-to-end in Cursor IDE | 2-3 hours | ⚠️ Not started |
| **Production Deployment** | Deploy backend to Railway + frontend to Vercel. All configs ready (Dockerfile, docker-compose, DEPLOYMENT.md). | 2 hours | ⚠️ Not started |
| **HNSW Index for pgvector** | Add `CREATE INDEX ON langmem_memories USING hnsw (embedding vector_cosine_ops)` for vector search performance | 30 min | ⚠️ Not started |
| **Better Stack Uptime Monitoring** | Set up health endpoint monitoring with 3-minute interval | 30 min | ⚠️ Not started |
| **Document /feedback endpoint** | Add feedback endpoint to `docs/API.md` | 30 min | ⚠️ Not started |

### Referenced but Not Implemented

| Feature | Description | Status |
|---------|-------------|--------|
| **Stripe Integration** | Mentioned in gap analysis as potential enhancement | ❌ No implementation |
| **Multi-Instance Rate Limiting** | Current rate limiting is in-memory; need Redis-based for horizontal scaling | ❌ Not started |

---

## ✅ Previously Uncertain — NOW RESOLVED

| Uncertainty | Resolution |
|-------------|------------|
| **Phase 4 Frontend Status** | ✅ RESOLVED: Complete implementation — 115 TS/TSX files with auth, chat, history, profile, landing pages. Not deployed to Vercel. |
| **RULES.md Location** | ✅ RESOLVED: CONFIRMED MISSING from disk. 311+ code comments reference it. Needs recreation from standards described in code. |
| **IMPLEMENTATION_PLAN.md Location** | ✅ RESOLVED: CONFIRMED MISSING from disk. Same status as RULES.md. |
| **Deployment Status** | ✅ RESOLVED: NOT DEPLOYED. All configs ready. `.env.local` points to localhost. Placeholder URLs in README confirm. |
| **Swarm Latency** | ✅ RESOLVED: Pollinations API bottleneck. Groq swap is ~1 hour via config.py BASE_URL change. |
| **HTTPS in Production** | ✅ RESOLVED: Handled automatically by Railway/Vercel with free SSL. No manual configuration needed. |
| **Prompt Feedback Table** | ✅ RESOLVED: Active via `routes/feedback.py` — direct DB insert with quality score adjustment. |
| **Supermemory Implementation** | ✅ RESOLVED: `memory/supermemory.py` exists — 221 lines with trust levels, temporal updates. |
| **Hybrid Recall Implementation** | ✅ RESOLVED: `memory/hybrid_recall.py` exists — 366 lines, BM25+Vector+RRF+MMR. |

---

## Sources

- `README.md` — Features list, performance metrics, architecture diagram
- `history/PROJECT_SUMMARY.md` — Phase completion, optional enhancements, metrics
- `docs/API.md` — Endpoint documentation, rate limits
- `docs/DEPLOYMENT.md` — Monitoring tools (Sentry, Better Stack), deployment targets
- `docs/SUPABASE_SCHEMA.md` — Database tables, RLS policies, indexes
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
- `memory/supermemory.py` — 221 lines, MCP-exclusive memory, trust levels (READ)
- `memory/hybrid_recall.py` — 366 lines, BM25+Vector+RRF+MMR (READ)
- `memory/profile_updater.py` — 228 lines, 5th interaction + 30min trigger (READ)
- `agents/prompts/engineer.py` — 460 lines, system prompt + 8 examples (READ)
- `routes/feedback.py` — 111 lines, POST /feedback endpoint (READ)
- `routes/prompts_stream.py` — BackgroundTasks trigger for profile updater (READ)
- `graph/state.py` — 26-field PromptForgeState TypedDict (READ)
- `middleware/rate_limiter.py` — Rate limiting (hourly/daily/monthly), VIP bypass
- `auth.py` — JWT authentication, retry logic
- `api.py` — Middleware stack, monitoring integrations
- `promptforge-web/package.json` — 115 TS/TSX files confirmed (READ)
- `promptforge-web/.env.local` — Local dev config confirmed (READ)

---

*See also: [overview](overview.md), [architecture](architecture.md), [tasks](tasks.md)*

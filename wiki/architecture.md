# Architecture

**Full system architecture of PromptForge v2.0 — backend, frontend, infrastructure.**

---

## 1. Kira Orchestrator (`agents/orchestrator.py`)

Kira is the personality-driven routing agent that sits at the entry point of every request. It:

1. **Analyzes** the user's message for intent, complexity, and tone
2. **Checks memory** — loads user profile from `user_profiles` table and LangMem semantic memories
3. **Decides routing** — determines whether to:
   - **CONVERSATION** — reply with casual personality-driven response
   - **SWARM** — proceed with full 4-agent parallel swarm
   - **FOLLOWUP** — refine existing prompt based on modification request
   - **CLARIFICATION** — ask user a clarifying question before proceeding
4. **Adapts personality** — adjusts tone based on user's profile (technical vs. casual, power user vs. beginner)

**Routing logic** (`agents/orchestration/router.py`):
- Intent agent: Always runs unless simple direct command
- Context agent: Skipped if no session history
- Domain agent: Skipped if profile confidence > 85%
- Prompt Engineer: ALWAYS runs (never skipped)

Kira outputs a `user_facing_message` shown immediately via SSE, and a `proceed_with_swarm` boolean that gates swarm execution.

---

## 2. 4-Agent Swarm (LangGraph `Send()` API)

The swarm runs 3 analysis agents **in parallel** using LangGraph's `Send()` API, followed by the Prompt Engineer as a join node:

| Agent | File | Model | Temp | Tokens | Purpose |
|-------|------|-------|------|--------|---------|
| **Intent Agent** | `agents/intent.py` | Fast (nova-fast) | 0.2 | 400 | Analyzes user's true goal, goal clarity, missing info |
| **Context Agent** | `agents/context.py` | Fast (nova-fast) | 0.2 | 400 | Builds user context from profile, memories, session history |
| **Domain Agent** | `agents/domain.py` | Fast (nova-fast) | 0.15 | 300 | Identifies primary domain, sub-domain, complexity, relevant patterns |
| **Prompt Engineer** | `agents/prompt_engineer.py` | Full (nova) | 0.3 | 2048 | Synthesizes all agent outputs into final engineered prompt |

**Parallel execution flow** (from `workflow.py`):

```
1. kira_orchestrator (entry point) → routing decision
2. route_to_agents() → returns Send() objects for parallel execution
3. intent/context/domain → run in PARALLEL via Send() API
4. prompt_engineer → join node, waits for all, synthesizes
5. END → return final state
```

Expected latency: Kira ~500ms + parallel agents ~500–1000ms + prompt engineer ~1–2s = **2–5s total** (with Pollinations paid tier).

---

## 3. LangGraph State Schema (`graph/state.py`)

`PromptForgeState` is a TypedDict with **26 fields** organized in 8 sections. Located in `graph/state.py` (not in root — the `graph/` directory is an active Python package with empty `__init__.py`). This is the "baton" passed between all agents:

### Section 1: INPUT (6 fields)
- `message` — User's actual message (5-2000 chars)
- `session_id` — Conversation session identifier
- `user_id` — From JWT, extracted via `auth.uid()`
- `attachments` — Multimodal: `[{type, content/base64, filename}]`
- `input_modality` — `'text' | 'file' | 'image' | 'voice'`
- `conversation_history` — Last N turns from Supabase

### Section 2: MEMORY (6 fields)
- `user_profile` — From `user_profiles` table (dominant_domains, preferred_tone, etc.)
- `langmem_context` — Top 5 memories from LangMem semantic search
- `mcp_trust_level` — 0 (cold) | 1 (warm) | 2 (tuned), always 0 for web app
- `session_count` — Total sessions for experience level formatting
- `user_facts` — Verified facts from fact_extractor.py background job (v2.5)
- `quality_trend` — Last 5 quality scores for trend detection (v2.5)

### Section 3: ROUTING (5 fields)
- `mode` — `"REFINE" | "ARCHITECT" | "ERROR_DIAGNOSIS"` (v3)
- `route` — `"CONVERSATION" | "SWARM" | "FOLLOWUP" | "CLARIFICATION"`
- `input_quality` — From `score_input_quality()` — structural quality assessment
- `agents_to_run` — Which agents to execute (subset of intent, context, domain)
- `orchestrator_decision` — Full Kira response JSON

### Section 4: AGENT OUTPUTS (5 fields)
- `intent_analysis` — From intent agent (None if skipped)
- `context_analysis` — From context agent (None if skipped)
- `domain_analysis` — From domain agent (None if skipped)
- `agents_skipped` — Which agents didn't run and why
- `agent_latencies` — Execution time per agent in ms

### Section 5: FINAL OUTPUT (8 fields)
- `improved_prompt` — Final engineered prompt
- `original_prompt` — User's original input
- `prompt_diff` — Changes with annotations `[{type, before, after, reason}]`
- `quality_score` — Scores (1-5): specificity, clarity, actionability, overall
- `changes_made` — Human-readable change explanations
- `breakdown` — Agent-specific insights for API response
- `user_facing_message` — Message user sees via SSE stream

### Section 6: CLARIFICATION (4 fields)
- `clarification_needed` — True if Kira needs user answer
- `clarification_question` — The actual question asked
- `clarification_key` — Which field is being clarified
- `pending_clarification` — True if waiting for user's answer

### Section 7: V3 ERROR DIAGNOSIS (4 fields) — Future-proofing
- `error_text`, `original_tool`, `error_category`, `error_fix_suggestion`

### Section 8: V3 PROJECT CONTEXT (2 fields) — Future-proofing
- `project_context`, `session_level_context`

**Helper:** `create_initial_state()` function initializes all INPUT fields with defaults.

---

## 4. Supabase Database Schema

**8 tables**, all with Row Level Security (RLS) enabled. 38 total RLS policies.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `requests` | Prompt history (raw → improved pairs) | id, user_id, raw_prompt, improved_prompt, quality_score, version_id, version_number |
| `conversations` | Chat session turns | id, user_id, session_id, role, message, message_type |
| `chat_sessions` | Session metadata | id, user_id, title, is_pinned, is_favorite, deleted_at |
| `user_profiles` | User preferences (THE MOAT) | user_id (unique), primary_use, audience, preferred_tone, xp_total, loyalty_tier |
| `agent_logs` | Agent execution logs | request_id, agent_name, output |
| `langmem_memories` | Long-term memory with embeddings | user_id, content, improved_content, domain, embedding (pgvector, 768 dims) |
| `prompt_feedback` | Implicit feedback tracking | — |
| `mcp_tokens` | MCP auth tokens (365-day JWT) | user_id, token_hash, revoked |

**Required PostgreSQL extensions:** `pgvector` (for embeddings), `uuid-ossp`

**4 Performance Indexes:**
```sql
CREATE INDEX idx_requests_user_id ON requests(user_id);
CREATE INDEX idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
```

**⚠️ Missing:** No HNSW index on `langmem_memories.embedding` — should be added for pgvector performance.

**13 migrations:** 001-009 (Phase 1-2 tables + RLS), 010 (LangMem embedding column), 011 (user sessions), 012 (Supermemory facts), 013 (MCP tokens — verified in Supabase). Additional migration `docs/migrations/027_add_missing_profile_columns.sql` found.

**Note on `prompt_feedback` table:** No CRUD operations in `database.py`. The `routes/feedback.py` endpoint writes directly to this table via `db.table("prompt_feedback").insert()`, bypassing database.py helpers.

---

## 5. Redis Caching (`utils.py`)

- **Client:** Connection-pooled, created once via `lru_cache(maxsize=1)`
- **Cache key:** SHA-256 hash (never MD5) with version prefix `v2` and optional user personalization hash
- **TTL:** 1 hour (3600 seconds)
- **Capacity:** Auto-managed by Redis LRU; warning logged at 100+ entries
- **Schema versioning:** `CACHE_VERSION` constant — increment when state schema changes to orphan old keys
- **Personalization:** Cache key includes first 16 chars of SHA-256(user_id) for per-user results

---

## 6. Middleware Stack (`api.py`)

Order of middleware registration (top to bottom = first to last executed):

1. **Sentry** — Error tracking (must be first, initialized before any other imports)
2. **CORS** — Locked to `FRONTEND_URLS` env var (no wildcard), credentials enabled
3. **Rate Limiter** — Per-user: 100 req/hour, 1000 req/day (configurable via env). Skips `/health` and `OPTIONS`
4. **Metrics** — Structured logging + latency tracking

**Additional instrumentation:**
- **LangSmith** — LangChain native tracing (enabled via `LANGCHAIN_TRACING_V2=true`)
- **OpenTelemetry** — Distributed tracing with Jaeger (enabled via `OTEL_ENABLED=true`)
- **LangFuse** — Swarm execution tracking (agents run, latencies, quality scores)

---

## 7. MCP Server (`mcp/server.py`)

Native MCP server for Cursor/Claude Desktop integration:

**2 Tools:**
- `forge_refine` — Prompt improvement via 4-agent swarm (maps to `POST /refine`)
- `forge_chat` — Conversational improvement with classification (maps to `POST /chat`)

**Authentication:** Long-lived JWT (365 days), revocable via `mcp_tokens` table. Token type must be `mcp_access`.

**Trust Levels:**
- **0 (cold):** "Use me via web app more — I'll get sharper."
- **1 (warm):** "I'm learning your style. Domain skip and tone adaptation active."
- **2 (tuned):** "Full profile active. I know your preferences and patterns."

**Memory surface isolation (RULES.md):**
- LangMem is **NEVER** called from MCP (always `langmem_context=[]`)
- Supermemory is **NEVER** called from web app
- Two memory layers, never merged

---

## 8. Next.js Frontend (`promptforge-web/`) — VERIFIED COMPLETE

| Aspect | Details |
|--------|---------|
| **Framework** | Next.js 16.1.6 (App Router), React 19, TypeScript 5.9.3 |
| **Source Size** | 115 TypeScript/TSX source files (excluding node_modules, .next) |
| **Styling** | Tailwind CSS 3.4.17, Framer Motion, Lucide React icons, Sonner toasts |
| **Auth** | Supabase SSR (`@supabase/ssr`) with login/signup pages, session management |
| **State** | Redux Toolkit (RTK) — confirmed from package.json dependencies |
| **Charts** | Recharts 3.8.0 for analytics visualizations |
| **API Layer** | `lib/api.ts` — typed API client communicating with `NEXT_PUBLIC_API_URL` |
| **Testing** | Jest + Testing Library with coverage configuration |
| **Error Tracking** | `@sentry/nextjs` configured with DSN in `.env.local` |
| **Env Config** | `.env.local` — real Supabase credentials, localhost:8000 backend |
| **Features** | Auth (login/signup), Chat with SSE, History with analytics, Profile management, Landing page, Onboarding wizard, MCP token management, Data export |

**Key pages:**
- `app/(auth)/login/page.tsx`, `app/(auth)/signup/page.tsx` — Authentication
- `app/app/page.tsx` — Main chat interface
- `app/app/chat/[sessionId]/page.tsx` — Session-specific chat
- `app/app/history/page.tsx` — Prompt history with search/filter
- `app/app/profile/page.tsx` — User profile with multiple tabs
- `app/onboarding/page.tsx` — Onboarding wizard
- `app/(marketing)/page.tsx` — Landing page

**Assessment:** This is a **complete, feature-rich frontend** — not a scaffold or placeholder. It has NOT been deployed to Vercel (`.env.local` points to `localhost:8000`).

---

## 9. Docker Stack

**Multi-stage Dockerfile** with:
- No hot-reload in production (per RULES.md Security Rule #5)
- Health checks configured
- Railway auto-builds from `Dockerfile` in repo root

**Docker Compose:**
- `docker-compose up -d` for local testing
- Health endpoint: `curl http://localhost:8000/health`
- Logs: `docker-compose logs -f api`

---

## 10. Business Logic Layer (`service.py`)

Three core functions, all framework-agnostic (no FastAPI dependency — callable from CLI, cron, WebSocket):

| Function | Purpose |
|----------|---------|
| `_run_swarm()` | Full LangGraph workflow executor with Redis caching. 180s timeout via ThreadPoolExecutor. |
| `_astream_swarm()` | Async native streaming via `workflow.astream()`. Yields chunks incrementally as nodes execute. |
| `_run_swarm_with_clarification()` | Skips orchestrator, fires swarm directly with clarified context already resolved. |
| `compute_diff()` | Word-level diff using `difflib.SequenceMatcher` for frontend DiffView component. |
| `sse_format()` | Server-Sent Event formatter: `data: {"type": "event", "data": {...}}\n\n` |

---

## 11. Authentication (`auth.py`)

- **Provider:** Supabase JWT (ES256/HS256)
- **Validation:** Uses `supabase.auth.get_user(token)` — handles both algorithms automatically
- **Retry logic:** Retries once on transient network errors (WinError 10035 on Windows)
- **User extraction:** Returns `User(user_id, email, role="authenticated")`
- **Optional auth:** `get_optional_user()` for public endpoints that optionally personalize

**Security rules (per RULES.md Section 11):**
1. ✅ JWT on all endpoints except `/health`
2. ✅ session_id ownership via RLS
3. ✅ RLS on ALL tables
4. ✅ CORS locked to frontend domain (no wildcard)
5. ✅ No hot-reload in Dockerfile
6. ✅ SHA-256 for cache keys
7. ✅ Prompt sanitization
8. ✅ Rate limiting per user_id (100 req/hour)
9. ✅ Input length validation (5–2000 chars)
10. ✅ File size limits enforced first
11. ✅ No secrets in code (all from .env)
12. ⚠️ HTTPS in production (deployment responsibility)
13. ✅ Session timeout (24 hours via JWT)

---

## 12. LLM Configuration (`config.py`)

**Provider:** Pollinations Gen API (`https://gen.pollinations.ai/v1`)

| Model | Purpose | Temperature | Max Tokens |
|-------|---------|-------------|------------|
| `MODEL_FULL` (nova) | Prompt Engineer (full) | 0.3 | 2048 |
| `MODEL_FAST` (nova-fast) | Analysis agents | 0.1 | 400 |

Both models cached via `lru_cache(maxsize=1)` — created once, reused everywhere. To swap providers (e.g., Groq, Anthropic, Ollama), change `BASE_URL` and `MODEL` only.

---

## Sources

- `state.py` — Full 27-field PromptForgeState schema
- `graph/state.py` — 26-field PromptForgeState TypedDict, 8 sections, create_initial_state() helper (READ)
- `workflow.py` — LangGraph StateGraph with Send() parallel execution
- `api.py` — App factory, middleware stack, Sentry init
- `service.py` — Business logic (_run_swarm, _astream_swarm, compute_diff, sse_format)
- `auth.py` — JWT authentication with Supabase
- `config.py` — LLM factory (Pollinations Gen API)
- `database.py` — All Supabase operations (897 lines)
- `utils.py` — Redis caching, JSON parsing, quality scoring
- `xp_engine.py` — XP/gamification system
- `mcp/server.py` — MCP server with 2 tools, trust levels
- `memory/langmem.py` — LangMem with Gemini embeddings, hybrid recall
- `memory/supermemory.py` — 221 lines, MCP-exclusive memory, trust levels (READ)
- `memory/hybrid_recall.py` — 366 lines, BM25+Vector+RRF+MMR (READ)
- `memory/profile_updater.py` — 228 lines, 5th interaction + 30min trigger (READ)
- `routes/feedback.py` — 111 lines, POST /feedback endpoint (READ)
- `routes/prompts_stream.py` — BackgroundTasks trigger for profile updater (READ lines 358-373)
- `middleware/rate_limiter.py` — Rate limiting (hourly/daily/monthly)
- `docs/SUPABASE_SCHEMA.md` — Database schema documentation, 4 indexes
- `agents/README.md` — Agent system public API
- `history/PROJECT_SUMMARY.md` — Phase completion, metrics, security
- `README.md` — Project overview, architecture diagram
- `promptforge-web/package.json` — Dependencies, scripts (READ)
- `promptforge-web/.env.local` — Local dev config with real Supabase credentials (READ)

---

*See also: [overview](overview.md), [features](features.md), [decisions](decisions.md)*

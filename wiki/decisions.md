# Decisions

**Key architectural and design decisions extracted from source files, phase reports, and audit documents.**

---

## Core Architecture Decisions

### 1. Multi-Agent Swarm Over Single LLM Call
**Decision:** Use 4 specialized agents (Intent, Context, Domain, Prompt Engineer) instead of a single LLM call for prompt engineering.

**Why:** Each agent has a single responsibility — intent analysis, context building, domain identification, and synthesis. This produces higher-quality outputs with measurable quality scores (specificity, clarity, actionability).

**Evidence:** `workflow.py`, `agents/README.md`, `history/PROJECT_SUMMARY.md`

**When:** Phase 2 (Agent Swarm)

---

### 2. LangGraph `Send()` API for True Parallel Execution
**Decision:** Use LangGraph's `Send()` API for TRUE parallel execution of analysis agents, not sequential chaining.

**Why:** Reduces total latency from sum-of-all-agents to max-of-parallel-agents. With Pollinations paid tier: parallel agents run in ~500–1000ms vs sequential ~1.5–3s.

**Evidence:** `workflow.py` — `PARALLEL_MODE = True`, `route_to_agents()` returns `Send()` objects

**When:** Phase 2

---

### 3. Kira as Personality-Driven Router
**Decision:** Create "Kira" as a distinct orchestrator agent with personality adaptation, not just a dumb router.

**Why:** Kira adapts tone based on user profile (technical vs. casual), recognizes power users vs. beginners, and provides personality-driven user-facing messages via SSE before the swarm completes.

**Evidence:** `agents/orchestrator.py`, `agents/orchestration/router.py`, `agents/orchestration/personality.py`, `agents/prompts/orchestrator.py` (400-line system prompt with 8 examples)

**When:** Phase 2

---

### 4. Pollinations Gen API as LLM Provider
**Decision:** Use Pollinations.ai (`https://gen.pollinations.ai/v1`) as the LLM provider via OpenAI-compatible interface.

**Why:** Cost-effective, OpenAI-compatible (uses `ChatOpenAI` from `langchain_openai`), supports parallel access with paid tier. Configurable via `BASE_URL` and `MODEL` — easy to swap to Groq, Anthropic, or Ollama.

**Trade-off:** Swarm latency variance (4–6s vs target 3–5s) attributed to Pollinations API response times. Groq swap would fix this (~1 hour effort).

**Evidence:** `config.py` — `BASE_URL = "https://gen.pollinations.ai/v1"`, `MODEL_FULL = "nova"`, `MODEL_FAST = "nova-fast"`

**When:** Phase 2

---

### 5. Gemini Embeddings at 768 Dimensions (Not 3072)
**Decision:** Use `gemini-embedding-001` with `output_dimensionality=768` instead of default 3072.

**Why:** Supabase free tier HNSW index limit is 2000 dimensions. 768 dims fits comfortably while maintaining good embedding quality. Migration 024 (`024_fix_embedding_dimensions.sql`) handled the column resize.

**Evidence:** `memory/langmem.py` — `EMBEDDING_DIM = 768`, comment explaining Supabase HNSW limit

**When:** Phase 2 (after migration 024)

---

### 6. Redis SHA-256 Cache Keys (Never MD5)
**Decision:** Use SHA-256 for cache keys with version prefix and optional user personalization hash.

**Why:** Per RULES.md security requirements — MD5 is a known vulnerability. SHA-256 provides collision resistance. Version prefix (`v2`) allows cache invalidation on schema changes.

**Evidence:** `utils.py` — `get_cache_key()` uses `hashlib.sha256()`, `CACHE_VERSION = "v2"`

**When:** Phase 1

---

### 7. Memory Surface Isolation
**Decision:** LangMem is NEVER called from MCP requests. Supermemory is NEVER called from web app requests. Two memory layers, never merged.

**Why:** Security and data isolation. MCP clients (Cursor, Claude Desktop) should not have access to the user's full web app memory history. Each surface gets its own memory store.

**Evidence:** `mcp/server.py` — `langmem_context=[]` always set for MCP swarm calls. `memory/langmem.py` — raises `ValueError` if `surface="mcp"` passed to `query_langmem()`.

**When:** Phase 3 (MCP Integration)

---

### 8. Supabase Over Self-Hosted PostgreSQL
**Decision:** Use Supabase (managed PostgreSQL + pgvector + auth) instead of self-hosted database.

**Why:** Built-in JWT auth integration, RLS policies, pgvector extension, managed backups, free tier generous for early stage. Eliminates need for separate auth service.

**Evidence:** `auth.py`, `database.py`, `docs/SUPABASE_SCHEMA.md`

**When:** Phase 1

---

### 9. In-Memory Rate Limiting (Not Redis-Based)
**Decision:** Use in-memory rate limiting with sliding window algorithm instead of Redis-based rate limiting.

**Why:** Simpler implementation, no additional Redis dependency for rate limiting. Acceptable for single-instance deployments.

**Trade-off:** Not thread-safe for multi-instance deployments. `middleware/rate_limiter.py` notes: "For multi-instance, use Redis-based rate limiting."

**Evidence:** `middleware/rate_limiter.py` — `RateLimiter` class with `defaultdict` tracking

**When:** Phase 1

---

### 10. Service Layer Decoupled from FastAPI
**Decision:** `service.py` contains all business logic with NO FastAPI dependency. Callable from CLI, cron, WebSocket, or HTTP.

**Why:** Per RULES.md modularity requirements. Enables testing without HTTP layer, supports multiple entry points (REST API, MCP server, future WebSocket).

**Evidence:** `service.py` — imports only from `workflow`, `state`, `utils`, `middleware.langfuse_instrumentation`

**When:** Phase 1

---

### 11. Prompt Engineer ALWAYS Runs (Never Skipped)
**Decision:** The Prompt Engineer agent is a mandatory join node — it always runs regardless of which analysis agents were skipped.

**Why:** Even if intent, context, and domain agents are all skipped (e.g., simple direct command), the Prompt Engineer still needs to produce an engineered prompt. It's the only agent that produces the final output.

**Evidence:** `workflow.py` — `graph.add_edge("intent_agent", "prompt_engineer")` and similar for context/domain. Prompt engineer node has no conditional skip path.

**When:** Phase 2

---

### 12. Auto-Versioning on Requests
**Decision:** Automatically version prompts within sessions. New prompts in an existing session increment `version_number` and share the same `version_id`. Previous versions are marked `is_production=False`.

**Why:** Enables prompt iteration tracking. Users can see how their prompts evolved and revert to previous versions.

**Evidence:** `database.py` — `save_request()` with Phase 3 Auto-Versioning logic

**When:** Phase 3

---

### 13. Long-Lived MCP JWT (365 Days, Revocable)
**Decision:** MCP tokens are long-lived (365 days) but revocable via database flag.

**Why:** MCP clients (Cursor, Claude Desktop) shouldn't require frequent re-authentication. Revocability provides security control — tokens can be invalidated without waiting for expiry.

**Evidence:** `mcp/server.py` — `validate_mcp_jwt()` checks `mcp_tokens` table for `revoked=False`

**When:** Phase 3

---

### 14. Gamification via XP Engine
**Decision:** Implement XP system with quality-based scoring, polymath bonus, teaching bonus, and streak multiplier.

**Why:** Encourages high-quality prompt engineering, cross-domain exploration, and consistent usage. Loyalty tiers (Bronze → Silver → Gold → Kira-Class) provide long-term engagement hooks.

**Evidence:** `xp_engine.py` — `calculate_forge_xp()`, `get_tier_from_xp()`

**When:** ⚠️ Uncertain when this was implemented — not explicitly listed in phase completion summary

---

### 15. Sentry First in Middleware Stack
**Decision:** Sentry SDK initialization MUST be the very first import/execution in `api.py`, before any other imports.

**Why:** Ensures all errors — including import-time errors — are captured. If Sentry initializes after other imports, errors during those imports are lost.

**Evidence:** `api.py` — `# ═══ SENTRY INITIALIZATION — MUST BE FIRST ═══` comment, Sentry init before all other imports

**When:** Phase 1

---

## Sources

- `workflow.py` — Parallel mode, Send() API, prompt engineer always runs
- `state.py` — State schema design, field organization
- `service.py` — Service layer decoupled from FastAPI
- `config.py` — Pollinations Gen API selection, model configuration
- `database.py` — Auto-versioning logic, Supabase usage
- `utils.py` — SHA-256 cache keys, version prefixing
- `auth.py` — Supabase JWT authentication
- `mcp/server.py` — Memory surface isolation, long-lived JWT, trust levels
- `memory/langmem.py` — Gemini 768-dim embeddings, hybrid recall
- `middleware/rate_limiter.py` — In-memory rate limiting, sliding window
- `xp_engine.py` — XP engine design, loyalty tiers
- `api.py` — Sentry first, middleware stack
- `agents/README.md` — Agent system design, temperature/token constants
- `history/PROJECT_SUMMARY.md` — Phase decisions, trade-offs
- `docs/SUPABASE_SCHEMA.md` — Database design decisions
- `docs/DEPLOYMENT.md` — Deployment target decisions (Railway, Vercel)

---

*See also: [architecture](architecture.md), [questions](questions.md), [tasks](tasks.md)*

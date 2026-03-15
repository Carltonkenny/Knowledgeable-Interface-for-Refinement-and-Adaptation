# PromptForge v2.0 — Complete AI Agent Context

**Generated:** 2026-03-15  
**Purpose:** Complete project context for AI agents. Read this FIRST before any task.  
**Scope:** Architecture, workflows, standards, and operational patterns. NO CODE.

---

## 🎯 PROJECT IDENTITY

### What Is PromptForge?

A **multi-agent AI prompt engineering system** that transforms vague, rough prompts into precise, high-performance instructions using a swarm of 4 specialized AI agents with MCP integration.

### Core Value Proposition

**Input (vague):** "write a story about a robot"

**Output (engineered):** "You are a seasoned science-fiction author. Write a 1,200-word short story set in a near-future city, told from the first-person perspective of a maintenance robot named Aria. Blend humor with subtle social commentary, exploring the theme of identity versus programming..."

**Improvement:** ~2000% more detailed, with role, audience, tone, structure, and constraints.

### The Moat (Competitive Advantage)

The system **learns each user over time**. More usage = richer profile = better results. Switching away means starting over. This is created by:

1. **LangMem** — Stores prompt quality history, domain confidence, stylistic preferences
2. **User Profiles** — Tracks dominant domains, preferred tone, clarification patterns
3. **Semantic Search** — Retrieves user's best past work as stylistic reference

---

## 🏗️ ARCHITECTURE LAYERS

### Layer 1: Client Surface

**Technologies:** Next.js 16, React 19, TypeScript, Tailwind CSS

**Entry Points:**
- Web App (`promptforge-web/`) — Primary user interface
- MCP Clients (Cursor, Claude Desktop) — External integrations

**Key Rule:** Web and MCP surfaces use **different memory layers** (never merge).

### Layer 2: API Gateway

**Technology:** FastAPI (Python)

**Responsibilities:**
- JWT authentication (Supabase)
- Rate limiting (100 requests/hour per user)
- CORS enforcement
- Input validation
- Request routing

**Endpoints:** 11 total (health, refine, chat, stream, history, sessions, user profile)

### Layer 3: Orchestration

**Technology:** LangGraph StateGraph

**Pattern:** Sequential pipeline with conditional parallel execution

**Flow:**
1. Kira Orchestrator (routing decision)
2. Conditional parallel agents (intent, context, domain)
3. Join node (prompt engineer)
4. Output + background writes

### Layer 4: Memory & Storage

**Databases:**
- Supabase PostgreSQL (primary DB with pgvector)
- Redis (caching layer)

**Memory Layers:**
- LangMem (web app only) — Operational intelligence
- Supermemory (MCP only) — Conversational facts

### Layer 5: LLM Providers

**Primary:** Pollinations.ai (OpenAI-compatible API)
- Full model: `openai` (GPT-5 Mini) — for prompt engineering
- Fast model: `nova` (Amazon Nova Micro) — for analysis agents

**Alternative:** Groq API (faster inference, free tier)

**Embeddings:** Google Gemini (`gemini-embedding-001`, 3072 dimensions)

---

## 🤖 AGENT SWARM WORKFLOW

### The 4 Agents (No More, No Less)

| Agent | Purpose | Model | Skip Condition |
|-------|---------|-------|----------------|
| **Intent** | Analyzes WHAT user wants | Fast | Simple direct command |
| **Context** | Analyzes WHO is asking | Fast | No session history |
| **Domain** | Identifies field/patterns | Fast | Profile confidence >85% |
| **Prompt Engineer** | Synthesizes final prompt | Full | **NEVER skipped** |

### Execution Modes

**Sequential (Default):**
```
Kira → Intent → Context → Domain → Prompt Engineer
Total: 4 LLM calls, ~4-6 seconds
```

**Parallel (Enabled):**
```
Kira → [Intent + Context + Domain] → Prompt Engineer
Total: 2 LLM stages, ~2-5 seconds
```

### Parallel Implementation

Uses LangGraph `Send()` API for TRUE parallel execution:

1. `kira_orchestrator` returns `agents_to_run: ["intent", "domain"]`
2. `route_to_agents()` returns `Send("intent_agent", state), Send("domain_agent", state)`
3. LangGraph executes both simultaneously
4. `prompt_engineer` waits for all to complete (automatic join)

---

## 🧠 KIRA ORCHESTRATOR — THE PERSONALITY

### Character Profile

**Name:** Kira  
**Role:** Prompt engineering orchestrator  
**Personality:** Direct, warm, slightly opinionated — like a senior collaborator

### Forbidden Phrases (Never Use)

"Certainly", "Great question", "Of course", "I'd be happy to", "Let me help you", "No problem", "Sure!", "Absolutely", "Happy to help"

### Behavioral Rules

1. **NEVER** asks more than ONE question per response
2. **NEVER** explains process in detail — just does it
3. **Speed is a personality trait** — every interaction feels deliberate
4. **Reads user profile before every response** — adapts tone

### Routing Logic (In Order)

1. **message.length < 10** → CONVERSATION handler (user is being brief)
2. **pending_clarification** → Inject answer, fire swarm directly
3. **Modification phrases** → FOLLOWUP handler (1 LLM call)
4. **ambiguity_score > 0.7** → CLARIFICATION (ask 1 question)
5. **Otherwise** → SWARM mode (select agents based on confidence)

### Response Schema

```json
{
  "user_facing_message": "What user sees immediately",
  "proceed_with_swarm": true/false,
  "agents_to_run": ["intent", "domain"],
  "clarification_needed": true/false,
  "clarification_question": "Your one question or null",
  "skip_reasons": {"context": "reason or null"},
  "tone_used": "direct" | "casual" | "technical",
  "profile_applied": true/false
}
```

---

## 📊 MEMORY SYSTEM — TWO LAYERS, NEVER MERGE

### Layer 1: LangMem (Web App Only)

**Purpose:** Internal pipeline memory for web app requests

**What It Stores:**
- Prompt quality history and trends
- Domain confidence per user
- Past improved prompts (stylistic reference)
- Clarification patterns and user responsiveness
- Agent skip decision accuracy
- Session-level project context

**Query Pattern:**
1. User message arrives
2. Generate Gemini embedding (3072 dimensions)
3. pgvector SQL cosine similarity search (`<=>` operator)
4. Return top 5 relevant memories
5. Inject into Kira orchestrator context

**Write Pattern:**
1. Session completes
2. FastAPI BackgroundTask extracts facts
3. Writes to `langmem_memories` table
4. User never waits

**Critical Rule:** DO NOT call LangMem during MCP requests. LangMem is app-exclusive.

### Layer 2: Supermemory (MCP Only)

**Purpose:** Conversational memory for MCP clients (Cursor, Claude Desktop)

**What It Stores:**
- Conversational facts ("user prefers Python")
- Project context ("working on FastAPI project")
- Client-specific preferences

**Critical Rule:** MCP clients NEVER access LangMem. Use Supermemory only.

### Why Two Layers?

| Aspect | LangMem | Supermemory |
|--------|---------|-------------|
| **Surface** | Web app | MCP clients |
| **Purpose** | Operational intelligence | Conversational context |
| **Query** | Semantic search (pgvector) | Keyword + recency |
| **Write** | Background task | Real-time |
| **Access** | Web app pipeline | MCP server only |

---

## 🗄️ DATABASE SCHEMA

### Tables (8 Total)

**Core Tables:**
1. `requests` — Prompt pairs (raw → improved) with version control
2. `conversations` — Full chat turns with classification
3. `agent_logs` — Each agent's analysis output
4. `chat_sessions` — Session metadata (title, pins, favorites)

**Moat Tables:**
5. `user_profiles` — User personalization (dominant domains, preferred tone)
6. `langmem_memories` — Pipeline memory with pgvector embeddings

**Infrastructure Tables:**
7. `user_sessions` — Session activity tracking
8. `mcp_tokens` — Long-lived MCP JWT tokens (365 days, revocable)

### RLS Policies (38 Total)

**Pattern:** `users_select_own_*`, `users_insert_own_*`, `users_update_own_*`, `users_delete_own_*`

**Key Principle:** Users can ONLY see/modify their own data. Enforced at database level.

### Version Control (Migration 019)

**Auto-Versioning Logic:**
- If session_id exists, find latest version in that session
- If found, increment `version_number` and link to same `version_id`
- If new session, start version 1 with new `version_id`
- Previous versions marked `is_production: false`

**Columns:**
- `version_id` — Groups related versions
- `version_number` — Incrementing counter
- `parent_version_id` — Links to previous version
- `change_summary` — Human-readable change description
- `is_production` — Marks current active version

---

## 🔐 SECURITY RULES (NON-NEGOTIABLE)

### RULES.md Compliance: 92% (12/13 rules)

| # | Rule | Status | Implementation |
|---|------|--------|----------------|
| 1 | JWT on all endpoints except /health | ✅ | `get_current_user` dependency |
| 2 | session_id ownership via RLS | ✅ | `user_id = auth.uid()` |
| 3 | RLS on ALL tables | ✅ | 38 policies |
| 4 | CORS locked to frontend domain | ✅ | No wildcards |
| 5 | No hot-reload in Dockerfile | ✅ | Production build |
| 6 | SHA-256 for cache keys | ✅ | `hashlib.sha256()` |
| 7 | Prompt sanitization | ✅ | `sanitize_text()` |
| 8 | Rate limiting per user_id | ✅ | 100 req/hour |
| 9 | Input length validation | ✅ | 5-2000 chars |
| 10 | File size limits enforced first | ✅ | Validate before process |
| 11 | No secrets in code | ✅ | All from .env |
| 12 | HTTPS in production | ⚠️ | Deployment responsibility |
| 13 | Session timeout | ✅ | 24 hours via JWT |

### Authentication Flow

1. User logs in via Supabase Auth
2. Supabase returns JWT
3. Frontend stores JWT in memory (not localStorage)
4. Every API call includes `Authorization: Bearer <token>`
5. Backend validates JWT via `get_current_user`
6. `user_id` extracted and used for RLS queries

### Rate Limiting Algorithm

**Sliding Window:**
- Window: 1 hour (3600 seconds)
- Limit: 100 requests per user_id
- Storage: In-memory dict (per-process)
- Cleanup: Old timestamps removed on each check

**Response on Exceed:**
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "limit": "100 requests per hour",
  "remaining": 0
}
```

---

## ⚡ PERFORMANCE TARGETS

| Scenario | Target | Actual | Status |
|----------|--------|--------|--------|
| Cache hit | <100ms | ~50ms | ✅ Exceeds |
| CONVERSATION | 2-3s | ~3s | ✅ |
| FOLLOWUP | 2-3s | ~3s | ✅ |
| NEW_PROMPT (parallel) | 3-5s | 4-6s | ⚠️ Close |
| Clarification question | 1s | ~1s | ✅ |
| LangMem search | <500ms | ~50-100ms | ✅ Exceeds (5-10x) |

**Note:** Swarm latency variance is due to Pollinations API, not code quality. Switch to Groq for consistent 3-5s.

### Optimization Strategies

**Implemented:**
- Parallel agent execution (Send() API)
- Redis caching (SHA-256 keys, 1-hour expiry)
- pgvector SQL operators (database-side similarity)
- Background writes (FastAPI BackgroundTasks)
- Fast LLM for analysis agents (400 tokens max)

**Not Implemented:**
- Streaming responses (SSE from agents)
- Speculative execution (run all agents, discard skipped)
- Batch embeddings (multiple queries in one API call)

---

## 📁 FILE STRUCTURE

### Backend (`newnew/`)

```
newnew/
├── agents/                     # AI agent implementations
│   ├── autonomous.py           # Kira orchestrator + conversation handlers
│   ├── intent.py               # Intent analysis agent
│   ├── context.py              # Context analysis agent
│   ├── domain.py               # Domain identification agent
│   └── prompt_engineer.py      # Final prompt synthesis agent
│
├── graph/                      # LangGraph orchestration
│   └── workflow.py             # Agent pipeline (PARALLEL_MODE=True)
│
├── mcp/                        # MCP Integration
│   ├── server.py               # Native MCP server (6 tools)
│   └── __main__.py             # stdio transport for Cursor
│
├── memory/                     # Memory systems
│   ├── langmem.py              # Web app pipeline memory (pgvector)
│   ├── profile_updater.py      # User profile evolution
│   └── supermemory.py          # MCP-exclusive memory
│
├── middleware/                 # FastAPI middleware
│   └── rate_limiter.py         # 100 req/hour per user
│
├── multimodal/                 # Input processing
│   ├── files.py                # PDF/DOCX/TXT extraction
│   ├── image.py                # Base64 encoding
│   ├── transcribe.py           # Whisper transcription
│   └── validators.py           # Security validation
│
├── migrations/                 # Database migrations
│   └── 001-020.sql             # 20 migrations total
│
├── api.py                      # FastAPI REST endpoints
├── auth.py                     # JWT authentication
├── config.py                   # LLM factory (Pollinations/Groq)
├── database.py                 # Supabase client
├── state.py                    # LangGraph TypedDict (26 fields)
├── utils.py                    # Redis cache + utilities
└── workflow.py                 # Compiled StateGraph
```

### Frontend (`promptforge-web/`)

```
promptforge-web/
├── app/                        # Next.js app router
│   ├── (auth)/                 # Auth pages (login, signup)
│   ├── (marketing)/            # Landing pages
│   ├── app/                    # Main chat interface
│   └── onboarding/             # 3-step wizard
│
├── features/                   # Feature modules
│   ├── auth/                   # Auth components
│   ├── chat/                   # Chat interface + hooks
│   ├── history/                # History search + analytics
│   ├── landing/                # Landing page components
│   ├── onboarding/             # Onboarding wizard
│   └── profile/                # Profile settings (Phase 4)
│
├── lib/                        # Core utilities
│   ├── api.ts                  # All backend calls
│   ├── auth.ts                 # Auth helpers
│   ├── errors.ts               # Error mapping
│   ├── logger.ts               # Structured logging
│   ├── stream.ts               # SSE parser
│   └── types.ts                # Shared types
│
└── components/                 # Shared components
```

---

## 🔄 WORKFLOWS

### Workflow 1: New Prompt Request (Web App)

**Trigger:** User types message in chat, presses Enter

**Steps:**
1. Frontend validates input (5-2000 chars)
2. `useKiraStream` hook initiates SSE connection
3. Backend: `/chat` endpoint receives request
4. JWT validation → extract `user_id`
5. Rate limit check (100 req/hour)
6. Parallel context loads:
   - User profile from `user_profiles`
   - LangMem memories (semantic search)
   - Conversation history (last 6 turns)
7. Kira orchestrator analyzes (1 fast LLM call)
8. Kira returns routing decision via SSE
9. Conditional parallel agents run:
   - Intent analysis (if not simple command)
   - Context analysis (if history exists)
   - Domain analysis (if profile confidence <85%)
10. Prompt engineer synthesizes (1 full LLM call)
11. Final result streamed via SSE:
    - `improved_prompt`
    - `diff` (add/remove/keep)
    - `quality_score` (specificity, clarity, actionability)
    - `breakdown` (agent insights)
12. Background tasks (user doesn't wait):
    - Save to `requests` table
    - Save agent logs
    - Write to LangMem
    - Update profile (if 5th interaction)
    - Cache result (Redis, 1 hour)

**Total Time:** 2-6 seconds (depends on parallel mode)

---

### Workflow 2: Clarification Loop

**Trigger:** Kira detects ambiguity (ambiguity_score > 0.7)

**Steps:**
1. Kira returns `clarification_needed: true`
2. Kira returns 1 question (e.g., "What's the target audience?")
3. Backend saves to `conversations`:
   - `pending_clarification: true`
   - `clarification_key: "target_audience"`
4. Frontend displays question, waits for answer
5. User responds with clarification
6. Next request: Backend checks `pending_clarification` FIRST
7. If true: Inject answer into state, skip orchestrator, fire swarm directly
8. After swarm completes: Clear `pending_clarification` flag

**Critical:** Do NOT re-run orchestrator on clarification answer.

---

### Workflow 3: Followup Request

**Trigger:** User wants to modify last prompt ("make it longer", "add detail")

**Detection:** Kira identifies modification phrases:
- "make it"
- "change the"
- "add more"
- "less"
- "shorter"
- "longer"

**Steps:**
1. Kira returns `proceed_with_swarm: false`
2. Kira returns `followup_mode: true`
3. Backend calls `handle_followup()` (1 LLM call)
4. Followup handler:
   - Fetches last improved prompt
   - Applies modification
   - Returns new version
5. Frontend displays result

**Total Time:** ~3 seconds (1 LLM call vs 4)

---

### Workflow 4: MCP Request (Cursor/Claude Desktop)

**Trigger:** User invokes PromptForge via MCP tool

**Steps:**
1. MCP client sends request via stdio
2. MCP server validates long-lived JWT token
3. Trust level check:
   - Level 0 (cold): Basic refinement only
   - Level 1 (warm): + memory access
   - Level 2 (tuned): + profile personalization
4. If trust level < 2: Return basic refinement
5. If trust level = 2: Call Supermemory for context
6. Run swarm (same as web app)
7. Return result via MCP protocol

**Critical:** MCP uses Supermemory, NOT LangMem.

---

### Workflow 5: Profile Update (Background)

**Trigger:** Every 5th interaction OR 30min inactivity

**Steps:**
1. `profile_updater.py` runs as BackgroundTask
2. Fetches last 5 sessions from `conversations`
3. Analyzes patterns:
   - Dominant domains
   - Preferred tone
   - Clarification responsiveness
   - Quality trends
4. Updates `user_profiles`:
   - `dominant_domains` (array)
   - `preferred_tone` (string)
   - `clarification_rate` (numeric)
   - `prompt_quality_trend` (string)
   - `notable_patterns` (array)
5. Writes insights to LangMem:
   - "User excels at creative writing"
   - "Prefers technical tone"
   - "Often clarifies target audience"

**User Impact:** Next request gets personalized treatment.

---

### Workflow 6: History Search (RAG)

**Trigger:** User types in history search bar

**Steps:**
1. Frontend: `useHistorySearch` hook
2. Debounced (300ms) to avoid excessive calls
3. Backend: `/history/search` endpoint
4. RAG toggle check:
   - **RAG ON:** Query LangMem (semantic search)
   - **RAG OFF:** Query database (keyword search)
5. Apply filters:
   - Domain (e.g., "coding", "writing")
   - Quality score (min 1-5)
   - Date range (from/to)
6. Return results with highlights

**RAG Query:**
```sql
SELECT *, (1 - (embedding <=> query_embedding)) AS similarity
FROM langmem_memories
WHERE user_id = auth.uid()
ORDER BY embedding <=> query_embedding
LIMIT 10
```

---

## 🧪 TESTING STRATEGY

### Test Categories

**Unit Tests:**
- Individual functions (e.g., `parse_json_response`)
- Edge cases (empty input, max length, special chars)
- Error handling (invalid JWT, DB connection failure)

**Integration Tests:**
- Full API endpoints (e.g., `/chat` with real LLM)
- Database operations (RLS enforcement)
- Caching (Redis hit/miss)

**E2E Tests:**
- Complete user flows (signup → onboarding → chat)
- Multi-turn conversations
- Clarification loops

**Performance Tests:**
- Latency targets (see Performance section)
- Concurrent request handling
- Memory usage under load

### Test Structure

```
testadvance/
├── phase1/                     # Backend Core tests
│   ├── test_auth.py            # JWT, RLS, rate limiting
│   └── test_database.py        # Table existence, RLS policies
├── phase2/                     # Agent Swarm tests
├── phase3/                     # MCP Integration tests
├── integration/                # End-to-end tests
└── edge_cases/                 # Edge case tests
```

### Running Tests

```bash
cd testadvance

# Run all tests
python run_all_tests.py

# Run specific phase
python -m pytest phase1/ -v

# Generate analysis
python generate_analysis.py
```

---

## 📖 DEVELOPMENT STANDARDS

### Code Quality Rules

1. **Type Hints:** Every function parameter and return type
2. **Docstrings:** Every public function (purpose, params, returns, example)
3. **Error Handling:** Try/except with graceful fallback
4. **Logging:** Structured logging with `[component]` prefix
5. **No AI Slop:** Senior-level code quality, no shortcuts

### Naming Conventions

**Python:**
- Files: `snake_case.py`
- Functions: `snake_case()`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private: `_leading_underscore`

**TypeScript:**
- Files: `PascalCase.tsx` (components), `camelCase.ts` (utils)
- Functions: `camelCase()`
- Components: `PascalCase()`
- Types: `PascalCase`
- Hooks: `usePascalCase()`

### File Organization

**One Module = One Responsibility**

Bad: `utils.py` with 50 unrelated functions  
Good: `cache.py`, `embedding.py`, `validation.py` (each focused)

**Import Order:**
1. Standard library
2. Third-party
3. Project modules
4. Local imports

---

## 🚀 DEPLOYMENT

### Docker (Production)

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Configuration:**
- No hot-reload (`--reload` flag removed)
- Production workers (uvicorn workers)
- Redis included in compose
- Health check endpoint

### Local Development

```bash
# Backend
cd newnew
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn api:app --reload --port 8000

# Frontend
cd promptforge-web
npm install
npm run dev
```

### Environment Variables

**Required:**
- `POLLINATIONS_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_JWT_SECRET`
- `REDIS_URL`
- `GEMINI_API_KEY`

**Optional:**
- `GROQ_API_KEY` (alternative LLM provider)
- `FRONTEND_URLS` (CORS origins, comma-separated)

---

## 🎯 CURRENT STATUS

### Phase Completion

| Phase | Status | Tests | Compliance |
|-------|--------|-------|------------|
| **Phase 1: Backend Core** | ✅ COMPLETE | 59/59 | 100% |
| **Phase 2: Agent Swarm** | ✅ COMPLETE | 28/28 | 100% |
| **Phase 3: MCP Integration** | ✅ COMPLETE | 33/33 | 100% |
| **Phase 4: Profile Enhancements** | 🚧 IN PROGRESS | TBD | TBD |

### Phase 4 Scope (7 Features Only)

1. **Username Update** — `PATCH /user/username`
2. **Domain Stats** — `GET /user/domains`
3. **Memory Preview** — `GET /user/memories`
4. **Quality Trend** — `GET /user/quality-trend`
5. **Usage Stats** — `GET /user/stats`
6. **Account Deletion** — `DELETE /user/account` (GDPR)
7. **Data Export** — `GET /user/export-data` (GDPR)

**Explicitly NOT in Phase 4:**
- Email notifications
- Avatar uploads
- Additional profile fields

---

## 🔧 TROUBLESHOOTING

### Common Issues

**Backend won't start:**
- Check `.env` file exists with all required variables
- Verify Supabase credentials are valid
- Check Redis is running (`redis-cli ping`)

**RLS errors:**
- Ensure `user_id` is included in all queries
- Verify JWT is valid and not expired
- Check RLS policies are enabled in Supabase dashboard

**LangMem search returns empty:**
- Verify `GEMINI_API_KEY` is set
- Check `pgvector` extension is enabled
- Ensure embeddings are being generated (check logs)

**Rate limiting triggers too early:**
- Check `user_id` extraction from JWT
- Verify sliding window algorithm is correct
- Consider increasing limit for testing (not production)

**MCP connection fails:**
- Verify long-lived token is valid (not revoked)
- Check trust level is sufficient for requested operation
- Ensure stdio transport is configured correctly

---

## 📞 CHECK-IN POINTS

**Report progress after:**

1. ✅ Reference documents read (this file + RULES.md)
2. ✅ Migration created and tested
3. ✅ Backend endpoints complete
4. ✅ Frontend components complete
5. ✅ Integration complete
6. ✅ Tests passing
7. ✅ Ready for review

---

## 🎯 AI AGENT INSTRUCTIONS

### Before Starting Any Task

1. **Read this document** completely
2. **Read RULES.md** for detailed standards
3. **Check existing code** for patterns to follow
4. **Understand the scope** (what to build, what NOT to build)

### During Implementation

1. **Follow existing patterns** (style, structure, naming)
2. **Write tests as you build** (not after)
3. **Add type hints and docstrings** (mandatory)
4. **Log errors with context** (`[component] action failed: error`)
5. **Handle errors gracefully** (fallback, don't crash)

### Before Submitting

1. **Run tests** (all must pass)
2. **Check compliance** (RULES.md checklist)
3. **Verify no duplicates** (search for existing code)
4. **Test edge cases** (empty input, max length, errors)
5. **Document changes** (update this file if architecture changes)

---

**Last Updated:** 2026-03-15  
**Version:** 2.0  
**Status:** Production Ready (Phases 1-3 Complete, Phase 4 In Progress)

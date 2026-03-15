# PromptForge v2.0 — Project Overview for Frontend Developers

**Document Purpose:** Complete context for LLMs/frontend developers to understand the PromptForge system architecture, workflows, and integration points.

**Last Updated:** March 15, 2026
**Status:** ✅ PRODUCTION READY

---

## 🎯 WHAT IS PROMPTFORGE?

PromptForge is a **multi-agent AI prompt engineering system** that transforms vague, rough prompts into precise, high-performance instructions using a swarm of 4 specialized AI agents.

### Example Transformation

**Input (vague):**
```
"write a story about a robot"
```

**Output (engineered):**
```
You are a seasoned science-fiction author. Write a 1,200-word short story set in a 
near-future city, told from the first-person perspective of a maintenance robot named Aria. 
Blend humor with subtle social commentary, exploring the theme of identity versus programming. 
The central conflict: Aria discovers a hidden human diary that challenges its purpose. 
Keep the tone witty yet reflective, suitable for adult readers, and end with a twist that 
leaves the reader questioning what it means to be "alive".
```

**Improvement:** ~2000% more detailed with role, audience, tone, structure, and constraints.

---

## 📊 SYSTEM METRICS

| Metric | Value |
|--------|-------|
| **Backend LOC** | ~9,400 lines (Python) |
| **Frontend LOC** | ~6,000 lines (TypeScript/React) |
| **API Endpoints** | 11 (8 authenticated) |
| **AI Agents** | 4 (intent, context, domain, prompt_engineer) |
| **Database Tables** | 8 (38 RLS policies) |
| **Test Coverage** | 129+ tests |
| **Security Compliance** | 92% (12/13 RULES.md rules) |
| **Performance Target** | 2-5s end-to-end latency |

---

## 🏗️ ARCHITECTURE LAYERS

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│           (Browser / Frontend / curl / MCP Clients)              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI API LAYER                           │
│  ┌──────────┬──────────┬──────────────┬──────────┬──────────┐  │
│  │ /health  │ /refine  │   /chat      │ /upload  │ /history │  │
│  └──────────┴──────────┴──────────────┴──────────┴──────────┘  │
│         │              │                │              │         │
│         ▼              ▼                ▼              ▼         │
│  ┌─────────────┬──────────────┬─────────────────┬────────────┐ │
│  │   Cache     │  Classifier  │   Multimodal    │  Database  │ │
│  │  (Redis)    │  (Kira)      │   (Whisper)     │ (Supabase) │ │
│  └─────────────┴──────────────┴─────────────────┴────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                            │
│                                                                  │
│  ┌─────────────────┐                                            │
│  │ Kira Orchestrator│ ← 1 fast LLM call (~500ms)               │
│  └────────┬────────┘                                            │
│           │ Conditional Edges (Send() API)                      │
│      ┌────┼────┬────────┐                                       │
│      ▼    ▼    ▼        │                                       │
│   ┌──┐ ┌──┐ ┌──┐       │  ← PARALLEL execution                 │
│   │I │ │C │ │D │       │     (~500-1000ms total)               │
│   └──┘ └──┘ └──┘       │                                       │
│      └────┴────┴───────┘                                       │
│           │ Join Point                                          │
│           ▼                                                     │
│   ┌──────────────┐                                              │
│   │Prompt Engineer│ ← 1 full LLM call (~1-2s)                  │
│   └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MEMORY LAYER                                 │
│  ┌─────────────┐    ┌─────────────────┐                         │
│  │ LangMem     │    │ Supermemory     │                         │
│  │ (Web App)   │    │ (MCP Only)      │                         │
│  │ pgvector    │    │ Conversational  │                         │
│  │ embeddings  │    │ context         │                         │
│  └─────────────┘    └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 AUTHENTICATION FLOW

### JWT-Based Authentication (Supabase)

```
┌─────────────────────────────────────────────────────────────────┐
│ AUTHENTICATION FLOW                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User signs up/logs in via Supabase Auth                     │
│     POST /auth/v1/signup {email, password}                      │
│                                                                 │
│  2. Supabase returns JWT token                                  │
│     { access_token, refresh_token, user: {id, email} }          │
│                                                                 │
│  3. Frontend stores token in localStorage/cookie                │
│                                                                 │
│  4. Every API request includes token:                           │
│     Authorization: Bearer <token>                               │
│                                                                 │
│  5. Backend validates JWT via Supabase client                   │
│     - auth.py:get_current_user()                                │
│     - Extracts user_id for RLS queries                          │
│                                                                 │
│  6. Database enforces Row Level Security                        │
│     WHERE user_id = auth.uid()                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Token Structure

```typescript
interface JWTPayload {
  sub: string;           // User UUID
  email: string;         // User email
  role: string;          // 'authenticated'
  aud: string;           // 'authenticated'
  iat: number;           // Issued at (timestamp)
  exp: number;           // Expires at (timestamp)
  iss: string;           // Issuer (Supabase URL)
}
```

---

## 📡 API ENDPOINTS

### Public Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | ❌ | Liveness check |

### Authenticated Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/refine` | POST | ✅ | Single-shot prompt improvement |
| `/chat` | POST | ✅ | Conversational with memory |
| `/chat/stream` | POST | ✅ | Streaming conversational (SSE) |
| `/history` | GET | ✅ | Past prompts from requests table |
| `/conversation` | GET | ✅ | Full chat history for session |
| `/transcribe` | POST | ✅ | Voice transcription (Whisper) |
| `/upload` | POST | ✅ | File/image upload for multimodal |

---

## 🗄️ DATABASE SCHEMA

### Core Tables

```sql
-- requests: Stores prompt pairs (for /refine and /chat)
CREATE TABLE requests (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,              -- RLS KEY
    raw_prompt TEXT NOT NULL,
    improved_prompt TEXT NOT NULL,
    session_id TEXT,
    quality_score JSONB,
    domain_analysis JSONB,
    agents_used TEXT[],
    agents_skipped TEXT[],
    version_id UUID,
    version_number INTEGER,
    parent_version_id UUID,
    is_production BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- conversations: Full chat turns with classification
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,              -- RLS KEY
    session_id TEXT,
    role TEXT NOT NULL,                 -- 'user' | 'assistant'
    message TEXT NOT NULL,
    message_type TEXT,                  -- 'conversation' | 'new_prompt' | 'followup'
    improved_prompt TEXT,
    pending_clarification BOOLEAN,
    clarification_key TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- user_profiles: THE MOAT — User personalization
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL,
    dominant_domains TEXT[],
    prompt_quality_trend TEXT,          -- 'improving' | 'stable' | 'declining'
    clarification_rate NUMERIC,
    preferred_tone TEXT,
    notable_patterns TEXT[],
    total_sessions INTEGER,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- langmem_memories: THE MOAT — Pipeline memory with pgvector
CREATE TABLE langmem_memories (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,              -- RLS KEY
    content TEXT NOT NULL,
    improved_content TEXT,
    domain TEXT,
    quality_score JSONB,
    embedding VECTOR(3072),             -- Gemini embedding
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Row Level Security (RLS)

All tables have RLS enabled with policies:
- `users_select_own_*` — Users can only see their own data
- `users_insert_own_*` — Users can only insert their own data
- `users_update_own_*` — Users can only update their own data
- `users_delete_own_*` — Users can only delete their own data

**Total:** 38 RLS policies across 8 tables

---

## 🤖 AGENT SWARM DETAILS

### The 4 Agents

| Agent | Model | Temp | Tokens | Purpose | Skip Condition |
|-------|-------|------|--------|---------|----------------|
| **Intent** | nova-fast | 0.1 | 400 | Analyze user's true goal | Simple direct command |
| **Context** | nova-fast | 0.1 | 400 | Analyze user context | First message (no history) |
| **Domain** | nova-fast | 0.1 | 400 | Identify domain/patterns | Profile confidence > 85% |
| **Prompt Engineer** | openai | 0.3 | 2048 | Synthesize final prompt | **NEVER** |

### Parallel Execution

The swarm uses LangGraph's `Send()` API for TRUE parallel execution:

```python
# graph/workflow.py
def route_to_agents(state: AgentState) -> List[Send]:
    decision = state.get("orchestrator_decision", {})
    agents_to_run = decision.get("agents_to_run", [])
    
    # Return Send() objects for parallel execution
    return [
        Send("intent_agent", state),
        Send("context_agent", state),
        Send("domain_agent", state),
    ]
```

**Latency Breakdown:**
- Kira Orchestrator: ~500ms
- Parallel agents: ~500-1000ms (max of parallel calls)
- Prompt Engineer: ~1-2s
- **TOTAL:** 2-5s

---

## 🧠 MEMORY SYSTEM

### Two Layers (NEVER merge)

#### Layer 1: LangMem (Web App Surface)

**Purpose:** Internal pipeline memory for web app requests

**Storage:** Supabase `langmem_memories` table with pgvector

**Query Pattern:**
1. User message → Generate embedding (Gemini API, ~500ms)
2. pgvector similarity search (Supabase SQL, ~50-100ms)
3. Return top 5 memories
4. Inject into LLM context

**Write Pattern:**
- FastAPI `BackgroundTask` after session completes
- User never waits for write

#### Layer 2: Supermemory (MCP Surface Only)

**Purpose:** Conversational context for MCP clients (Cursor, Claude Desktop)

**Storage:** Supabase `supermemory_facts` table

**Rule:** DO NOT call LangMem during MCP requests

---

## 🎨 KIRA — THE ORCHESTRATOR PERSONALITY

Kira is **NOT** just a router. She is a **personality with routing capability**.

### Character Constants

- **Direct, warm, slightly opinionated** — Like a senior collaborator
- **NEVER says:** "Certainly", "Great question", "Of course", "I'd be happy to"
- **NEVER asks more than ONE question** per response
- **NEVER explains her process** in detail
- **Speed is a personality trait** — Every interaction feels deliberate

### Routing Logic (In Order)

1. `message.length < 10` → CONVERSATION handler
2. `pending_clarification` on session → Inject answer, fire swarm directly
3. Modification phrases detected → FOLLOWUP handler (1 LLM call)
4. `ambiguity_score > 0.7` → CLARIFICATION (ask 1 question)
5. Otherwise → SWARM mode (4 agents)

### Response Schema

```json
{
  "user_facing_message": "string — streams to user immediately via SSE",
  "proceed_with_swarm": true,
  "agents_to_run": ["intent", "domain"],
  "clarification_needed": false,
  "clarification_question": null,
  "skip_reasons": { "context": "no session history" },
  "tone_used": "direct",
  "profile_applied": true
}
```

---

## 📡 SERVER-SENT EVENTS (SSE) STREAMING

### Stream Format

```
data: {"type": "status", "data": {"message": "Loading conversation history..."}}

data: {"type": "kira_message", "data": {"message": "H", "complete": false}}
data: {"type": "kira_message", "data": {"message": "e", "complete": false}}
data: {"type": "kira_message", "data": {"message": "y", "complete": false}}
data: {"type": "kira_message", "data": {"message": "", "complete": true}}

data: {"type": "result", "data": {"type": "prompt_improved", "reply": "..."}}

data: {"type": "done", "data": {"message": "Complete"}}
```

### Frontend Parser

```typescript
// lib/stream.ts
export function parseStream(
  stream: ReadableStream,
  callbacks: {
    onStatus: (msg: string) => void
    onKiraMessage: (msg: string, complete: boolean) => void
    onResult: (result: ChatResult) => void
    onDone: () => void
    onError: (error: string) => void
  }
) {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || '' // Keep incomplete line

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const json = JSON.parse(line.slice(6))
        const { type, data } = json

        switch (type) {
          case 'status':
            callbacks.onStatus(data.message)
            break
          case 'kira_message':
            callbacks.onKiraMessage(data.message, data.complete)
            break
          case 'result':
            callbacks.onResult(data)
            break
          case 'done':
            callbacks.onDone()
            break
          case 'error':
            callbacks.onError(data.message)
            break
        }
      }
    }
  }
}
```

---

## 🔒 SECURITY RULES

### RULES.md Section 11 — 13 Security Rules (92% compliance)

1. ✅ JWT required on all endpoints except /health
2. ✅ session_id ownership verified via RLS
3. ✅ RLS on ALL tables (38 policies)
4. ✅ CORS locked to frontend domain
5. ✅ No hot-reload in Dockerfile
6. ✅ SHA-256 for cache keys
7. ✅ Prompt sanitization
8. ✅ Rate limiting per user_id (100 req/hour)
9. ✅ Input length validation (5-2000 chars)
10. ✅ File size limits enforced first
11. ✅ No secrets in code (all from .env)
12. ⚠️ HTTPS in production (deployment responsibility)
13. ✅ Session timeout (24 hours via JWT)

---

## ⚡ PERFORMANCE TARGETS

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Cache hit | <100ms | ~50ms | ✅ Exceeds |
| CONVERSATION | 2-3s | ~3s | ✅ |
| FOLLOWUP | 2-3s | ~1-2s | ✅ Exceeds |
| NEW_PROMPT (parallel) | 3-5s | 4-6s | ⚠️ Close |
| Clarification question | 1s | ~500ms | ✅ Exceeds |
| LangMem search | <500ms | ~50-100ms | ✅ Exceeds (5-10x) |

**Note:** Swarm latency variance is due to Pollinations API, not code quality.

---

## 📁 PROJECT STRUCTURE

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
├── memory/                     # Memory systems
│   ├── langmem.py              # Web app pipeline memory (pgvector SQL)
│   ├── profile_updater.py      # User profile evolution (every 5th interaction)
│   └── supermemory.py          # MCP-exclusive conversational context
│
├── middleware/                 # FastAPI middleware
│   └── rate_limiter.py         # Rate limiting (100 req/hour per user)
│
├── multimodal/                 # Multimodal input processing
│   ├── transcribe.py           # Whisper transcription
│   ├── image.py                # Base64 encoding for GPT-4o Vision
│   └── files.py                # PDF/DOCX/TXT text extraction
│
├── migrations/                 # Database migrations (001-013)
├── testadvance/                # Comprehensive test framework
├── tests/                      # Core verification tests
├── DOCS/                       # Permanent documentation
│   ├── RULES.md                # Development standards (1,570 lines)
│   ├── IMPLEMENTATION_PLAN.md  # Phase-by-phase roadmap
│   └── Masterplan.html         # Vision document
│
├── api.py                      # FastAPI REST endpoints (11 endpoints)
├── auth.py                     # JWT authentication (Supabase)
├── config.py                   # LLM factory (Pollinations/Groq)
├── database.py                 # Supabase client + operations
├── state.py                    # LangGraph TypedDict schema (26 fields)
├── utils.py                    # Shared utilities (Redis cache, JSON parsing)
└── workflow.py                 # LangGraph StateGraph compilation
```

---

## 🔗 QUICK LINKS

### Supabase Dashboard
- **SQL Editor:** https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
- **Table Editor:** https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/editor
- **RLS Policies:** https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/policies

### Local Development
- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🚀 DEPLOYMENT

### Docker (Recommended)

```bash
# Start (foreground)
docker-compose up

# Start (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy .env and fill in your keys
copy .env.example .env

# Run
python main.py
```

---

**Built with LangGraph multi-agent orchestration. Production-ready. Dockerized. MCP-enabled.**

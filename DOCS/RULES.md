# PromptForge v2.0 — Complete Development Rules & Engineering Standards

**Version:** 1.0  
**Last Updated:** March 2026  
**Document Purpose:** Comprehensive rules, principles, and engineering standards for building PromptForge v2.0. Feed this to your AI coding agent before any implementation work.

---

## TABLE OF CONTENTS

1. [Project Identity](#project-identity)
2. [Architecture Overview](#architecture-overview)
3. [Kira Orchestrator](#kira--the-orchestrator-personality)
4. [Agent Swarm](#agent-swarm)
5. [Memory System](#memory-system--two-layers-never-merge-them)
6. [Database Rules](#database--supabase)
7. [API Endpoints](#api-endpoints)
8. [Multimodal Input](#multimodal-input)
9. [MCP Integration](#mcp-integration)
10. [Tech Stack](#tech-stack)
11. [Security Rules](#security--non-negotiable)
12. [Performance Targets](#performance-targets)
13. [Code Quality Standards](#code-quality-standards)
14. [DRY Principles](#dry-principles)
15. [Modularity Rules](#modularity--component-design)
16. [Testing Standards](#testing-standards)
17. [Documentation Standards](#documentation-standards)
18. [Naming Conventions](#naming-conventions)
19. [Error Handling](#error-handling--logging)
20. [Performance Optimization](#performance-optimization)
21. [Dependency Management](#dependency-management)
22. [Do Not Do These Things](#do-not-do-these-things)
23. [File Structure](#file-structure)

---

## PROJECT IDENTITY

**Product:** PromptForge v2.0

**Orchestrator Name:** Kira

**Purpose:** Multi-agent AI prompt engineering system that transforms vague prompts into precise, high-performance instructions through a 4-agent swarm pipeline with dynamic personalization.

**Core Differentiator:** The system learns each user over time. More usage = richer profile = better results. Switching away means starting over. This is the moat.

**Development Philosophy:** Senior-level code quality, maintainable architecture, no AI slop. Everything written should be indistinguishable from code written by experienced developers.

---

## ARCHITECTURE OVERVIEW

```
User Input 
  ↓
[Auth/JWT Validation] + [Input Validation]
  ↓
[Parallel Context Load] ← Supabase Profile + LangMem Context + Conversation History
  ↓
[Kira Orchestrator] ← 1 fast LLM call, returns routing decision
  ↓
[SSE Stream] → User-facing message from Kira
  ↓
[Conditional Agent Swarm] ← Intent || Context || Domain (parallel via LangGraph Send())
  ↓
[Join Node] ← Wait for all selected agents
  ↓
[Prompt Engineer Agent] ← Full model, synthesizes all context
  ↓
[SSE Stream] → improved_prompt + diff + quality_score
  ↓
[BACKGROUND TASKS] → Redis cache + Supabase writes + LangMem write + Profile Updater
```

**Key Principle:** Users never wait for background operations. All writes are async.

---

## KIRA — THE ORCHESTRATOR PERSONALITY

Kira is **NOT** a router. She is a **personality with routing capability**. She is the face of the product.

### Character Constants — Never Change These

- **Direct, warm, slightly opinionated** — Speaks like a senior collaborator who respects your time
- **Never says:** "Certainly", "Great question", "Of course", "I'd be happy to", "Let me help you", "No problem"
- **Never asks more than ONE question per response** — Multi-question requests overwhelm users
- **Never explains her process in detail** — She just does it. Users don't need the play-by-play
- **Speed is a personality trait** — She moves fast. Every interaction feels deliberate and snappy
- **She reads the user profile before every response** — Adapts expression based on history and domain

### What Kira Returns (Structured JSON)

**Specifications:**
- Max tokens: 150
- Model: Fast LLM (GPT-4o-mini)
- Temperature: 0.1
- Response time target: 300-500ms

**Response Schema:**
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

### Kira Routing Logic (In Order)

1. **message.length < 10** → CONVERSATION handler (user is being brief)
2. **pending_clarification on session** → Inject answer into state, skip orchestrator, fire swarm directly
3. **Modification phrases detected** → FOLLOWUP handler (1 LLM call only, skip full swarm)
4. **ambiguity_score > 0.7** → Set `clarification_needed: true`, return 1 question, stop
5. **Otherwise** → SWARM mode, select which agents based on profile confidence

### Clarification Loop — Critical Implementation Detail

When `clarification_needed` is true:

1. Save `pending_clarification: true` and `clarification_key: "field_name"` to session in Supabase
2. Return Kira's question via SSE event, end request
3. User responds with clarification
4. On next request: Check session for `pending_clarification` flag **FIRST**
5. If set: Treat message as answer, inject into state, fire swarm directly, clear flag
6. **Do NOT re-run orchestrator** — Avoid re-classifying the answer

---

## AGENT SWARM

### Core Rule: Four Agents. No More. Do Not Add Without Explicit Instruction.

| Agent | Model | Tokens | Temp | Skip Condition |
|-------|-------|--------|------|---|
| **Intent** | GPT-4o-mini | 400 | 0.1 | Simple direct command, no ambiguity detected |
| **Context** | GPT-4o-mini | 400 | 0.1 | First message in session (zero history) |
| **Domain** | GPT-4o-mini | 400 | 0.1 | User profile has domain at >85% confidence |
| **Prompt Engineer** | GPT-4o | 2048 | 0.3 | **Never skipped — always runs** |

### Execution Strategy

**Parallel Execution:**
- Use LangGraph `add_conditional_edges()` from orchestrator node
- Define `route_to_agents()` function that reads `orchestrator_decision["agents_to_run"]`
- Return list of agent node names to fire
- LangGraph handles parallel execution via `Send()` — no manual threading code

**Join Node:**
- Prompt engineer waits for ALL selected agents to complete
- Collects their outputs into state
- Synthesizes final improved prompt

**Prompt Engineer Additional Context:**
- Before execution, query LangMem for user's 3-5 best past prompts in identified domain
- Use as stylistic reference for the rewrite
- This ensures output matches user's established quality bar and writing style

---

## MEMORY SYSTEM — TWO LAYERS, NEVER MERGE THEM

### Layer 1: LangMem — Owns the App Surface

**Purpose:** Internal pipeline memory for web app requests

**Integration:**
- Lives inside LangGraph pipeline natively
- No adapter layer or translation code
- Transparent to agents

**What It Stores:**
- Prompt quality history and trends
- Domain confidence per user
- Past improved prompts (stylistic reference)
- Clarification patterns and user responsiveness
- Agent skip decision accuracy
- Session-level project context

**Query Pattern:**
- Incoming message → semantic search in LangMem
- Returns top 5 relevant memories
- Injected into Kira orchestrator context

**Write Pattern:**
- FastAPI `BackgroundTask` after each session completes
- Extracts facts and patterns from session
- Writes to persistent LangMem store
- User never waits

**Strict Rule:**
- DO NOT call LangMem during MCP requests
- LangMem is app-exclusive

### Layer 2: Supermemory — Owns the MCP Surface Only

**Purpose:** Context memory for Claude Desktop, Cursor, and MCP clients

**Integration:**
- Called **ONLY** on MCP requests
- Never called during normal web app flow

**What It Stores:**
- Conversational facts mentioned in passing
- Project context and client names
- Soft preferences stated naturally
- Temporal updates ("I moved to SF" supersedes "I live in NYC")
- Brief session summaries

**Usage:**
- MCP server queries Supermemory before conversation
- Context injected at conversation start
- User sees relevant history in their MCP client

**Write Pattern:**
- Lighter, conversational summary
- Post-session write (async)

**Strict Rule:**
- DO NOT call Supermemory during web app requests
- Completely separate from LangMem
- No content duplication between layers

### The Golden Rule

> **LangMem runs on web app requests. Supermemory runs on MCP requests. They never compete because they never run on the same request.**

Your core moat (LangMem operational intelligence) lives in your infrastructure. Your MCP presence (Supermemory conversational context) lives in third-party systems. Separation prevents conflicts and protects strategic data.

---

## PROFILE UPDATER AGENT

**Purpose:** Maintain and evolve user profiles without blocking user requests

**Trigger Conditions (Any One):**
- Every 5th interaction in a session
- 30 minutes of inactivity
- Explicit session end

**Input Data:**
- Last 5 sessions of interactions
- Existing Supabase `user_profiles` row
- Quality scores from all prompts
- Clarification outcomes (how many questions needed, how well user responded)

**LLM Call:**
- Model: Fast (GPT-4o-mini)
- Tokens: 500
- Temperature: 0.1
- Returns: Updated profile JSON with new values

**Output:**
- Updated `user_profiles` row in Supabase
- New dominant_domains
- Updated prompt_quality_trend
- Revised clarification_rate
- personality_adaptation adjustments

**Execution:**
- FastAPI `BackgroundTask` — **User NEVER waits**
- Safe to fail silently if backend is busy

---

## LANGGRAPH STATE — COMPLETE TYPEDDICT

This is the "baton" passed between all agents. Every field must be initialized before use.

```python
class PromptForgeState(TypedDict):
    # ═══ INPUT ═══
    message: str                     # User's actual message
    session_id: str                  # From JWT, uniquely identifies conversation
    user_id: str                     # From JWT, extracted via auth.uid()
    attachments: list[dict]          # [{type, content/base64, filename}]
    input_modality: str              # text | file | image | voice
    conversation_history: list[dict] # Last N turns from Supabase

    # ═══ MEMORY ═══
    user_profile: dict               # Loaded from Supabase user_profiles table
    langmem_context: list[dict]      # Top 5 memories from LangMem
    mcp_trust_level: int             # 0 (cold) | 1 (warm) | 2 (tuned)

    # ═══ ORCHESTRATOR ═══
    orchestrator_decision: dict      # Full Kira response JSON
    user_facing_message: str         # User sees this via SSE
    pending_clarification: bool      # True if waiting for answer
    clarification_key: str | None    # Which field is being clarified
    proceed_with_swarm: bool         # Kira's go/no-go decision

    # ═══ AGENT OUTPUTS ═══
    intent_analysis: dict            # From intent agent
    context_analysis: dict           # From context agent
    domain_analysis: dict            # From domain agent
    agents_skipped: list[str]        # Which agents didn't run and why
    agent_latencies: dict[str, int]  # {agent_name: ms}

    # ═══ OUTPUT ═══
    improved_prompt: str             # Final engineered prompt
    original_prompt: str             # User's original input
    prompt_diff: list[dict]          # Changes with annotations
    quality_score: dict              # {specificity: 1-5, clarity: 1-5, actionability: 1-5}
    changes_made: list[str]          # Human-readable change explanations
    breakdown: dict                  # Agent-specific insights
```

---

## DATABASE — SUPABASE

### Tables and Key Fields

#### user_profiles (NEW — CORE)

```
id: uuid (PK)
user_id: uuid (FK → auth.users) — RLS KEY
dominant_domains: text[] — Top 3 domains user works in
prompt_quality_trend: text — "improving" | "stable" | "declining"
avg_prompt_length: int — Moving average
clarification_rate: float — 0.0-1.0 (how often user needed clarification)
preferred_tone: text — "casual" | "formal" | "technical"
notable_patterns: text[] — ["likes_detailed_steps", "prefers_examples"]
personality_adaptation: jsonb — Kira's tone adjustments per domain
total_sessions: int
mcp_trust_level: int — 0 | 1 | 2
input_modality_trend: text — "text" | "voice" | "mixed"
updated_at: timestamptz — Last profile update
```

#### requests (EXISTING + NEW FIELDS)

```
id: uuid (PK)
user_id: uuid (FK) — RLS KEY
session_id: uuid
raw_prompt: text
improved_prompt: text
ADD: prompt_diff (jsonb) — Change annotations
ADD: quality_score (jsonb) — Scores dict
ADD: agents_used (text[]) — Which agents ran
ADD: agents_skipped (text[]) — Which agents skipped + reasons
ADD: user_rating (int 1-5) — Feedback on output
ADD: input_modality: text — text | file | image | voice
created_at: timestamptz
```

#### conversations (EXISTING + NEW FIELDS)

```
id: uuid (PK)
user_id: uuid (FK) — RLS KEY (not session_id!)
session_id: uuid
role: text — "user" | "assistant"
content: text — The message body
message_type: text — Metadata on message purpose
ADD: kira_tone_used (text) — Which tone variant Kira used
ADD: pending_clarification (bool) — Flag for clarification loop
ADD: clarification_key (text) — Which field is being clarified
created_at: timestamptz
```

#### agent_logs (EXISTING + NEW FIELDS)

```
id: uuid (PK)
request_id: uuid (FK)
agent_name: text
output: jsonb — Full agent response
ADD: was_skipped (bool) — True if agent didn't run
ADD: skip_reason (text) — Why it was skipped
ADD: latency_ms (int) — Execution time
created_at: timestamptz
```

### Row Level Security — Apply to ALL Tables

**Rule:** Every table must have RLS enabled. Non-negotiable.

```sql
-- Conversations table example
CREATE POLICY "users see own data" ON conversations
  FOR SELECT 
  USING (auth.uid() = user_id);

-- Repeat for: requests, user_profiles, agent_logs
-- Key principle: auth.uid() = user_id, never trust session_id alone
```

**Why:** Prevents users from accessing each other's data even if they know session IDs. Eliminates session ID data exposure vulnerability.

### Connection Pooling

**Rule:** Always use Supavisor pooler URL in production, never direct DB URL.

- Required for multi-instance deployments
- Handles connection reuse across instances
- Configure in environment variables

---

## CACHING

**Provider:** Redis (Upstash free tier for MVP)

**Key Strategy:**
- Function: SHA-256 hash of lowercased, stripped prompt
- Algorithm: `hashlib.sha256(prompt.strip().lower().encode()).hexdigest()`
- **Never use MD5** — Collision vulnerabilities

**Capacity & Eviction:**
- Max 100 entries
- LRU eviction when full
- Survives app restarts (unlike in-memory dict)

**Shared Access:**
- Accessible across all app instances
- Single source of truth for cached results

**Cache Behavior:**
- **Cache HIT:** Instant return, 0 LLM calls, <100ms response
- **Cache MISS:** Full swarm pipeline (4 LLM calls max)

**Implementation Rule:**
- Check cache FIRST in `_run_swarm()` function
- Store result to cache AFTER swarm completes
- Never bypass cache, never skip cache checks

---

## API ENDPOINTS

### Endpoint Specifications

```
GET  /health              → Liveness check, no auth required
POST /refine              → Single-shot improvement, no memory
POST /chat                → Conversational, with memory
POST /chat/stream         → SSE version of /chat
POST /transcribe          → Voice → Whisper → text
GET  /history             → Prompt history (optional session filter)
GET  /conversation        → Full chat history for authenticated user
```

### Authentication & Authorization

**Rule:** JWT required on ALL endpoints except `/health`

- Extract `user_id` from JWT
- Verify `session_id` ownership via Supabase RLS
- Return 403 if mismatch

**Header:** `Authorization: Bearer {jwt_token}`

### Response Headers

- `Content-Type: application/json`
- `Cache-Control: no-cache` (for conversational endpoints)
- `X-Response-Time: {ms}` (for monitoring)

### SSE Event Types (for `/chat/stream`)

Clients listen for these events in order:

| Event | Data | Purpose |
|-------|------|---------|
| `status` | `{message: "Analyzing intent..."}` | Real-time progress updates |
| `kira_message` | `{message: "From Kira"}` | Orchestrator response |
| `classification` | `{type: "NEW_PROMPT"}` | Routing decision |
| `result` | Full result object | Final output |
| `done` | `{message: "Complete"}` | Stream finished |
| `error` | `{message: "Error details"}` | Something failed |

---

## MULTIMODAL INPUT

### Voice Processing

**Flow:**
1. Frontend: `MediaRecorder API` → collect audio blob
2. Frontend: `POST /transcribe` with audio file
3. Backend: Forward to OpenAI Whisper API
4. Backend: Return transcript text
5. Frontend: Populate input field with transcript
6. User: Edit if needed, send normally
7. Backend: Process as regular text input
8. State: Set `input_modality: "voice"`

**Specifications:**
- Max file size: 25MB
- Supported formats: MP3, MP4, MPEG, MPGA, M4A, WAV, WebM
- Language detection: Automatic
- Response: Cleaned, trimmed transcript text

### Image Processing

**Flow:**
1. Frontend: Convert image to base64
2. Frontend: `POST /chat` or `/refine` with base64 in attachments
3. Backend: Pass base64 directly to prompt engineer LLM
4. Specification: GPT-4o is natively multimodal

**Rules:**
- Do NOT run separate image processing pipeline
- Do NOT run OCR or feature extraction
- Max file size: 5MB
- Supported formats: JPEG, PNG, GIF, WebP
- State: Set `input_modality: "image"`

### File Processing (PDF, DOCX, TXT)

**Flow:**
1. Frontend: `POST /chat` with file in attachments
2. Backend: Extract text server-side
3. Backend: Inject as `additional_context` in state
4. Agents: Process extracted text

**Tools:**
- PDF: PyMuPDF (`fitz`)
- DOCX: `python-docx`
- TXT: Direct read

**Rules:**
- Max file size: 2MB
- Text formats ONLY (PDF, DOCX, TXT)
- No executables, spreadsheets, or binary files
- Extract → clean whitespace → inject
- Do NOT run RAG or embedding pipeline — this is context enrichment only
- State: Set `input_modality: "file"`

### Input Validation

**Rules (Enforce in Pydantic schema BEFORE processing):**
- Image: 5MB max, image formats only
- File: 2MB max, text formats only
- Voice: 25MB max, audio formats only
- Reject: Executables, spreadsheets, archives

---

## MCP INTEGRATION

Model Context Protocol support for Cursor, Claude Desktop, and compatible clients.

### Progressive Trust Levels

**Level 0: Cold (0-10 sessions)**
- MCP works but no personalization
- Kira message: "Use me via the app more — I'll get sharper."
- All agents run
- Generic tone

**Level 1: Warm (10-30 sessions)**
- Domain skip active (>85% confidence)
- Tone adaptation active
- Targeted clarification questions
- Partial personalization

**Level 2: Tuned (30+ sessions)**
- Full profile active
- Pattern references in Kira's messages
- History-aware rewrites
- Feels like a senior collaborator

**Rule:** DO NOT hard-gate MCP. Always available. Personalization depth scales naturally.

### Tool Definitions

```
forge_refine
  Parameters: prompt (str), session_id (str)
  Maps to: POST /refine
  Returns: {improved_prompt, quality_score, breakdown}

forge_chat
  Parameters: message (str), session_id (str)
  Maps to: POST /chat
  Returns: {type, reply, improved_prompt, breakdown}
```

### MCP Context Injection

- Supermemory MCP server queries at conversation start
- Injects top 3 relevant memories into MCP client context
- User sees history automatically in Cursor/Claude Desktop
- Swarm pipeline runs identically regardless of MCP or web app origin

---

## TECH STACK

| Component | Service | Notes | Requirement |
|-----------|---------|-------|---|
| **API** | FastAPI + Uvicorn | REST + SSE streaming | Core |
| **Orchestration** | LangGraph | StateGraph, conditional edges, Send() | Core |
| **LLM (Fast)** | GPT-4o-mini | 400 tokens, 0.1 temp | Core |
| **LLM (Full)** | GPT-4o | 2048 tokens, 0.3 temp | Core |
| **Voice** | OpenAI Whisper | Via /transcribe endpoint | MVP |
| **Database** | Supabase | Supavisor pooler enabled | Core |
| **Cache** | Redis | Upstash free tier | Core |
| **Pipeline Memory** | LangMem | Native LangGraph | Core |
| **MCP Memory** | Supermemory | MCP surface only | MCP Phase |
| **Observability** | Langfuse | LLM call tracing | MVP |
| **Errors** | Sentry | Error tracking | MVP |
| **Hosting** | Fly.io | Docker container | Core |
| **Edge** | Cloudflare | SSL, DDoS, rate limiting | Core |

**Critical Rule:** DO NOT use Pollinations.ai. Use OpenAI paid API only.

---

## SECURITY — NON-NEGOTIABLE

Every rule in this section is mandatory. No exceptions.

| # | Rule | Implementation |
|---|------|---|
| 1 | JWT required on all endpoints except /health | Middleware validates token in header |
| 2 | session_id ownership verified via RLS | Prevent cross-user data access |
| 3 | RLS on ALL Supabase tables | `auth.uid() = user_id` on every query |
| 4 | CORS locked to frontend domain | No wildcard (`*`) |
| 5 | No hot-reload in Dockerfile | Development flag only |
| 6 | SHA-256 for cache keys | Never MD5 |
| 7 | Prompt sanitization | Remove injection attempts before agent processing |
| 8 | Rate limiting per user_id | Middleware tracks requests |
| 9 | Input length validation | Pydantic: `5-2000` chars for prompts |
| 10 | File size limits enforced first | Before any processing |
| 11 | No secrets in code | All environment variables |
| 12 | HTTPS only in production | Cloudflare enforces |
| 13 | Session timeout after inactivity | 24 hours default |

---

## PERFORMANCE TARGETS

| Scenario | LLM Calls | Target Response | Notes |
|----------|-----------|---|---|
| Cache hit | 0 | <100ms | Instant return |
| CONVERSATION | 1 | 2-3s | Kira only |
| FOLLOWUP | 1 | 2-3s | Refine last prompt |
| NEW_PROMPT (parallel) | 3+1 | 3-5s | Full swarm |
| Clarification question | 1 | 1s | Orchestrator only |

**Key Principle:** All DB saves are `BackgroundTask`. User never waits for writes. Context load (Supabase + LangMem + history) is parallel — adds zero sequential latency.

---

## CODE QUALITY STANDARDS

### Core Principles

Every line of code must meet these standards. AI-generated code should be indistinguishable from human-written code by senior developers.

### Type Hints — Mandatory on Every Function

```python
# ✅ CORRECT
def analyze_intent(message: str, history: list[dict]) -> dict[str, Any]:
    """Analyze user's true goal beyond literal words."""
    pass

# ❌ WRONG
def analyze_intent(message, history):
    pass
```

### Error Handling — Comprehensive

```python
# ✅ CORRECT
try:
    result = llm.invoke(messages)
    parsed = parse_json_response(result.content)
    return parsed
except json.JSONDecodeError as e:
    logger.error(f"[intent] JSON parse failed: {e}")
    return {}
except Exception as e:
    logger.error(f"[intent] unexpected error: {e}")
    return {}

# ❌ WRONG
result = llm.invoke(messages)  # What if it fails?
return json.loads(result.content)  # What if JSON is invalid?
```

### Logging — Contextual and Useful

```python
# ✅ CORRECT
logger.info(f"[orchestrator] routing decision: agents={agents}, tone={tone}")
logger.warning(f"[domain] skipped — confidence={conf:.2f} < 0.85")
logger.error(f"[intent] fallback after 3 retries", exc_info=True)

# ❌ WRONG
print("done")  # No context
logger.debug("step 1")  # Vague
logger.error(str(e))  # Missing context
```

### Docstrings — Purpose + Parameters + Returns

```python
# ✅ CORRECT
def orchestrator_node(state: PromptForgeState) -> dict:
    """
    Kira orchestrator: reads profile + history, decides routing.
    
    Args:
        state: Current PromptForgeState with message and context
    
    Returns:
        Dict with orchestrator_decision and user_facing_message
    
    Raises:
        HTTPException: If LLM call fails after retries
    """
    pass

# ❌ WRONG
def orchestrator_node(state):
    # does the thing
    pass
```

---

## DRY PRINCIPLES

### Rule 1: Extract Common Patterns Into Functions

**Anti-Pattern:**
```python
# In agent A
messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]
response = llm.invoke(messages)
result = parse_json_response(response.content, "agent_a")

# In agent B (duplicated!)
messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]
response = llm.invoke(messages)
result = parse_json_response(response.content, "agent_b")
```

**Pattern:**
```python
# In utils.py
def invoke_llm_with_system(
    llm: ChatOpenAI,
    system_prompt: str,
    user_content: str,
    agent_name: str
) -> dict:
    """Common LLM invocation with error handling."""
    try:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
        response = llm.invoke(messages)
        return parse_json_response(response.content, agent_name)
    except Exception as e:
        logger.error(f"[{agent_name}] LLM call failed: {e}")
        return {}

# In both agents
result = invoke_llm_with_system(llm, SYSTEM_PROMPT, prompt, "agent_a")
```

### Rule 2: Extract Configuration Into Separate Module

**Anti-Pattern:**
```python
# In agent.py
BASE_URL = "https://api.openai.com"
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"
TEMPERATURE = 0.3
```

**Pattern:**
```python
# In config.py
LLM_CONFIG = {
    "base_url": os.getenv("LLM_BASE_URL"),
    "api_key": os.getenv("LLM_API_KEY"),
    "model": "gpt-4o",
    "temperature": 0.3,
}

@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(**LLM_CONFIG)

# In agent.py
llm = get_llm()
```

### Rule 3: Extract Constants Into Single Location

```python
# constants.py
KIRA_CHARACTER_CONSTANTS = {
    "forbidden_phrases": ["Certainly", "Great question", "Of course"],
    "max_questions": 1,
    "speed_is_personality": True,
}

AGENT_SPECS = {
    "intent": {"model": "fast", "tokens": 400, "temp": 0.1},
    "context": {"model": "fast", "tokens": 400, "temp": 0.1},
    "domain": {"model": "fast", "tokens": 400, "temp": 0.1},
    "prompt_engineer": {"model": "full", "tokens": 2048, "temp": 0.3},
}

# Use in code
for phrase in KIRA_CHARACTER_CONSTANTS["forbidden_phrases"]:
    if phrase in response:
        # Error handling
        pass
```

### Rule 4: Single Responsibility Per Function

**Anti-Pattern:**
```python
def process_request(user_id, message, session_id):
    # Load profile
    profile = db.get_profile(user_id)
    # Validate message
    if len(message) < 5:
        return error
    # Call LLM
    response = llm.invoke(...)
    # Save to DB
    db.save_conversation(...)
    # Update cache
    cache.set(...)
    # Return response
    return response
```

**Pattern:**
```python
def load_profile(user_id: str) -> dict:
    """Load user profile from Supabase."""
    pass

def validate_input(message: str) -> tuple[bool, str]:
    """Validate message, return (is_valid, error_msg)."""
    pass

def invoke_orchestrator(profile: dict, message: str) -> dict:
    """Call Kira orchestrator."""
    pass

def save_request(user_id: str, message: str, response: dict) -> None:
    """Save request and response to database."""
    pass

async def process_request(user_id: str, message: str, session_id: str) -> dict:
    """Main request handler."""
    profile = load_profile(user_id)
    is_valid, error = validate_input(message)
    if not is_valid:
        return {"error": error}
    
    response = invoke_orchestrator(profile, message)
    await background_tasks.add_task(save_request, user_id, message, response)
    return response
```

---

## MODULARITY — COMPONENT DESIGN

### Rule 1: Organize by Responsibility, Not by Layer

**Anti-Pattern (Layer-Based):**
```
models/
  user.py
  prompt.py
  profile.py
utils/
  auth.py
  cache.py
  llm.py
services/
  agent_service.py
  db_service.py
```

**Pattern (Responsibility-Based):**
```
agents/
  intent.py          # Intent agent + related logic
  context.py         # Context agent + related logic
  domain.py          # Domain agent + related logic
  prompt_engineer.py # Final rewrite agent
memory/
  langmem.py         # LangMem integration
  supermemory.py     # MCP memory
multimodal/
  transcribe.py      # Voice processing
  image.py           # Image handling
  files.py           # File extraction
database.py          # All DB operations
config.py            # Configuration
utils.py             # Shared utilities
```

### Rule 2: Minimize Cross-Module Dependencies

```python
# ✅ CORRECT — Dependency flows one direction
# config.py → no imports from other modules
# agents/intent.py imports config.py ✓
# api.py imports agents and workflow ✓

# ❌ WRONG — Circular dependencies
# config.py imports agents.py
# agents.py imports config.py  ← Circular!
```

### Rule 3: Use Dependency Injection

```python
# ❌ WRONG — Tight coupling
class IntentAgent:
    def __init__(self):
        self.llm = get_llm()  # Hard to test, hard to swap
    
    def analyze(self, prompt):
        pass

# ✅ CORRECT — Loose coupling
class IntentAgent:
    def __init__(self, llm: ChatOpenAI, logger: Logger):
        self.llm = llm
        self.logger = logger
    
    def analyze(self, prompt: str) -> dict:
        pass

# Usage
agent = IntentAgent(llm=get_llm(), logger=logging.getLogger(__name__))
```

### Rule 4: Separate Concerns — Database, LLM, Logic

```python
# database.py — Only Supabase operations
def save_request(user_id: str, prompt: str, response: str) -> str:
    """Save request to Supabase."""
    pass

# agents/intent.py — Only agent logic
def intent_agent(state: PromptForgeState) -> dict:
    """Analyze intent. Returns dict."""
    pass

# api.py — Orchestration and HTTP handling
@app.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    """Handle request: load data, call agents, save results."""
    pass
```

---

## TESTING STANDARDS

### Unit Tests — Test Individual Functions

```python
# tests/agents/test_intent.py
import pytest
from agents.intent import intent_agent
from state import PromptForgeState
from unittest.mock import Mock

def test_intent_agent_success():
    """Test intent agent with valid input."""
    mock_llm = Mock()
    mock_llm.invoke.return_value.content = '{"primary_intent": "test"}'
    
    state = PromptForgeState(raw_prompt="test", ...)
    result = intent_agent(state)
    
    assert "intent_result" in result
    assert mock_llm.invoke.called

def test_intent_agent_json_parse_failure():
    """Test intent agent with invalid JSON response."""
    mock_llm = Mock()
    mock_llm.invoke.return_value.content = "invalid json"
    
    state = PromptForgeState(raw_prompt="test", ...)
    result = intent_agent(state)
    
    assert result["intent_result"] == {}  # Fallback
```

### Integration Tests — Test Workflows

```python
# tests/test_workflow.py
@pytest.mark.asyncio
async def test_full_swarm_workflow():
    """Test complete workflow: orchestrator → agents → engineer."""
    initial_state = PromptForgeState(
        message="write a story",
        user_id="test_user",
        ...
    )
    
    result = await workflow.invoke(initial_state)
    
    assert "improved_prompt" in result
    assert len(result["improved_prompt"]) > 0
```

### AI-Specific Tests — Validate Agent Outputs

```python
# tests/test_agent_outputs.py
def test_intent_agent_returns_required_fields():
    """Verify intent agent output has all required fields."""
    state = PromptForgeState(raw_prompt="test", ...)
    result = intent_agent(state)
    
    required = ["primary_intent", "goal_clarity", "missing_info"]
    for field in required:
        assert field in result["intent_result"]

def test_orchestrator_returns_valid_json():
    """Verify Kira returns valid, structured JSON."""
    from autonomous import orchestrator_node
    
    state = PromptForgeState(message="test", ...)
    result = orchestrator_node(state)
    
    required_fields = ["user_facing_message", "agents_to_run", "tone_used"]
    for field in required_fields:
        assert field in result
```

---

## DOCUMENTATION STANDARDS

### Docstring Format — NumPy Style

```python
def agent_function(
    message: str,
    profile: dict,
    history: list[dict]
) -> dict[str, Any]:
    """
    Short one-line description of what this function does.
    
    Longer explanation if the function is complex. Explain the algorithm,
    assumptions, or non-obvious behavior here.
    
    Parameters
    ----------
    message : str
        User's input message. Length 5-2000 characters.
    profile : dict
        User profile from Supabase. Keys: {dominant_domains, preferred_tone, ...}
    history : list[dict]
        Conversation history. Format: [{role, content, message_type}]
    
    Returns
    -------
    dict[str, Any]
        Output with keys:
        - agent_result: dict with analysis
        - latency_ms: int execution time
    
    Raises
    ------
    ValueError
        If message length < 5 characters
    Exception
        If LLM call fails after retries
    
    Examples
    --------
    >>> result = agent_function("test", {}, [])
    >>> assert "agent_result" in result
    """
    pass
```

### README Documentation

Every module should have a README documenting:
- **Purpose:** What does this module do?
- **Key Functions:** Main entry points
- **Dependencies:** What does it need?
- **Examples:** How to use?
- **Maintenance Notes:** What to watch out for?

```markdown
# agents/intent.py

## Purpose
Analyzes user's true goal beyond literal words. Extracts primary intent,
secondary goals, clarity level, and missing information.

## Key Functions
- `intent_agent(state)` — Main entry point, returns intent_analysis

## Dependencies
- `config.get_fast_llm()` — LLM instance
- `utils.parse_json_response()` — JSON parsing with fallbacks

## Example
```python
state = PromptForgeState(raw_prompt="write a story", ...)
result = intent_agent(state)
print(result["intent_result"]["primary_intent"])
```

## Maintenance
- SYSTEM_PROMPT is stored in constants — change there
- Token limit is 400 — monitor if responses get cut off
- Temperature 0.1 — lower = more consistent, higher = more creative
```

---

## NAMING CONVENTIONS

### Functions — Snake Case, Descriptive Verbs

```python
# ✅ CORRECT
def load_user_profile(user_id: str) -> dict:
    pass

def validate_prompt_length(prompt: str) -> tuple[bool, str]:
    pass

def invoke_llm_with_system_prompt(llm, system, user_content):
    pass

# ❌ WRONG
def get_prof(uid):  # Unclear abbreviation
    pass

def check(p):  # Too vague
    pass

def invoke_llm_call_api(llm, s, uc):  # Unclear abbreviation
    pass
```

### Variables — Snake Case, Self-Documenting

```python
# ✅ CORRECT
user_profile = db.get_profile(user_id)
quality_score = calculate_prompt_quality(improved_prompt)
agent_latencies: dict[str, int] = {}
pending_clarification: bool = False

# ❌ WRONG
prof = db.get_profile(uid)  # Abbreviations
q = calculate_quality(p)  # Shorthand
d: dict = {}  # No type hint, unclear purpose
pc: bool = False  # Unhelpful abbreviation
```

### Classes — Pascal Case, Noun-Based

```python
# ✅ CORRECT
class PromptForgeState(TypedDict):
    pass

class IntentAgent:
    pass

class KiraOrchestrator:
    pass

# ❌ WRONG
class promptforgestate:  # Lowercase
    pass

class intent_analyzer:  # Function-like
    pass

class MyOrchestrator:  # Too generic
    pass
```

### Constants — Upper Case, Descriptive

```python
# ✅ CORRECT
KIRA_MAX_TOKENS = 150
MAX_RETRY_ATTEMPTS = 3
DEFAULT_AGENT_TEMPERATURE = 0.1
CACHE_CAPACITY = 100

# ❌ WRONG
MAX_TOKENS = 150  # Unclear which component
retries = 3  # Lowercase, not constant
temp = 0.1  # Too vague
cache_size = 100  # No hint it's max
```

### Private Functions — Prefix with Underscore

```python
# Public API
def load_profile(user_id: str) -> dict:
    pass

# Internal helper
def _parse_profile_json(raw: str) -> dict:
    pass

# Very internal
def __validate_schema(obj: dict) -> bool:
    pass
```

---

## ERROR HANDLING & LOGGING

### Error Handling Pattern — Always Catch, Always Log, Always Fallback

```python
# ✅ CORRECT
def agent_function(state):
    try:
        # Attempt operation
        result = llm.invoke(messages)
        parsed = parse_json_response(result.content)
        return {"agent_output": parsed}
    
    except json.JSONDecodeError as e:
        logger.error(f"[agent_name] JSON parse failed: {str(e)}")
        return {"agent_output": {}}  # Fallback: empty result
    
    except httpx.TimeoutError as e:
        logger.error(f"[agent_name] LLM timeout: {str(e)}")
        return {"agent_output": {}}  # Fallback
    
    except Exception as e:
        logger.error(f"[agent_name] unexpected error: {str(e)}", exc_info=True)
        return {"agent_output": {}}  # Fallback

# ❌ WRONG
def agent_function(state):
    result = llm.invoke(messages)  # What if timeout?
    return json.loads(result.content)  # What if invalid JSON?
```

### Logging Levels

| Level | Use Case | Example |
|-------|----------|---------|
| DEBUG | Low-level diagnostic info | Variable values, intermediate calculations |
| INFO | General informational | Request start, operation completion |
| WARNING | Potentially problematic | Agent skipped, retry attempt |
| ERROR | Error but recoverable | LLM call failed, fallback initiated |
| CRITICAL | System failure | Database connection lost, cannot start |

```python
logger.debug(f"[intent] starting with prompt: {prompt[:50]}...")
logger.info(f"[orchestrator] routing decision: agents={agents}")
logger.warning(f"[intent] skipped — ambiguity too low")
logger.error(f"[intent] LLM failed: {e}")
logger.critical(f"[database] connection pool exhausted")
```

### Structured Logging Format

```python
# Format: [module_name] action/status: context
logger.info(f"[api] /chat request: session={session_id}, user={user_id}")
logger.warning(f"[cache] miss for prompt: {prompt_hash}")
logger.error(f"[orchestrator] LLM timeout after {retries} retries")
```

---

## PERFORMANCE OPTIMIZATION

### Rule 1: Caching — Check Before Computing

```python
# ✅ CORRECT
def _run_swarm(prompt: str, state: PromptForgeState):
    # Check cache FIRST
    cached = get_cached_result(prompt)
    if cached:
        logger.info("[cache] hit")
        return cached
    
    logger.info("[cache] miss — running swarm")
    result = workflow.invoke(state)
    
    # Store AFTER computation
    set_cached_result(prompt, result)
    return result

# ❌ WRONG
result = workflow.invoke(state)  # Always computes
if result_matches_cache(result):  # Check after compute
    return cached_result  # Too late!
```

### Rule 2: Parallelization — Load Data in Parallel

```python
# ✅ CORRECT — All three fire simultaneously
async def load_context(user_id, session_id):
    profile_task = asyncio.create_task(db.get_profile(user_id))
    history_task = asyncio.create_task(db.get_history(session_id))
    memory_task = asyncio.create_task(langmem.query(user_id))
    
    profile, history, memory = await asyncio.gather(
        profile_task, history_task, memory_task
    )
    
    return {
        "user_profile": profile,
        "conversation_history": history,
        "langmem_context": memory,
    }

# ❌ WRONG — Sequential, adds latency
profile = await db.get_profile(user_id)  # Wait
history = await db.get_history(session_id)  # Wait
memory = await langmem.query(user_id)  # Wait
```

### Rule 3: Background Tasks — Never Block User

```python
# ✅ CORRECT
@app.post("/chat")
async def chat(req: ChatRequest, background_tasks: BackgroundTasks):
    result = await run_swarm(req.message)
    
    # Save to DB in background — user never waits
    background_tasks.add_task(save_conversation, req.session_id, result)
    background_tasks.add_task(update_profile, req.user_id)
    
    return ChatResponse(**result)

# ❌ WRONG
@app.post("/chat")
async def chat(req: ChatRequest):
    result = await run_swarm(req.message)
    save_conversation(req.session_id, result)  # User waits!
    update_profile(req.user_id)  # User waits!
    return ChatResponse(**result)
```

### Rule 4: Model Selection — Use Fast Model When Possible

```python
# ✅ CORRECT
# For intent, context, domain analysis — use fast model (GPT-4o-mini)
def intent_agent(state):
    llm = get_fast_llm()  # 400 tokens, 0.1 temp
    # ...

# For final rewrite — use full model (GPT-4o)
def prompt_engineer_agent(state):
    llm = get_llm()  # 2048 tokens, 0.3 temp
    # ...

# ❌ WRONG
def intent_agent(state):
    llm = get_llm()  # Too expensive for analysis
```

---

## DEPENDENCY MANAGEMENT

### Rule 1: Use requirements.txt with Pinned Versions

```
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
pydantic==2.9.2
langchain==0.3.7
langchain-openai==0.2.6
langgraph==0.2.39
supabase==2.9.1
redis==5.0.1
```

**Why pin versions:**
- Reproducible builds across environments
- Prevents surprise breaking changes
- Easier debugging (know exact versions in production)

### Rule 2: Separate Dev Dependencies

```
# Create requirements-dev.txt
-r requirements.txt
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0
flake8==6.1.0
mypy==1.7.1
```

### Rule 3: Use Virtual Environment Always

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Rule 4: Update Dependencies With Caution

```bash
# Check what would change
pip list --outdated

# Test updates in isolation before production
pip install --upgrade package_name
# Run tests locally

# Update requirements.txt when stable
pip freeze > requirements.txt
```

---

## DO NOT DO THESE THINGS

### Absolute Prohibitions

| ❌ Do NOT | ✅ Do This Instead | Why |
|---------|---|---|
| Add >4 agents without instruction | Use conditional execution in existing 4 | Complexity compounds, breaks architecture |
| Merge LangMem and Supermemory | Keep surfaces separate | Prevents data leakage, protects moat |
| Hard-gate MCP behind session count | Use progressive trust levels | All users deserve access, personalization scales naturally |
| Call Supermemory on web app | Use LangMem only on web | Surface isolation prevents conflicts |
| Run DB saves synchronously | Always use BackgroundTask | Users experience faster responses |
| Use MD5 for cache keys | Use SHA-256 | MD5 has collision vulnerabilities |
| Use wildcard CORS | Lock to frontend domain | Security risk: exposes API to any origin |
| Use hot-reload in Docker | Development flag only | Production stability issues |
| Trust session_id from request | Verify via JWT + RLS | Prevents session hijacking |
| Run profile updater every message | Post-session trigger only | Performance overhead, unnecessary |
| Ask Kira multiple questions | One question maximum | User experience degrades with cognitive load |
| Use in-memory dict for cache | Redis only | Doesn't survive restarts, single instance only |
| Hardcode API keys | Use environment variables | Security risk: exposed in git history |
| Skip error handling | Always try/catch | Crashes hurt user experience |
| Return Stack traces to client | Log server-side, return generic message | Security risk: exposes internals |

---

## FILE STRUCTURE

```
promptforge/
├── main.py                         # uvicorn entry, logging setup
├── api.py                          # FastAPI app, all endpoints
├── workflow.py                     # LangGraph StateGraph definition
├── state.py                        # PromptForgeState TypedDict
├── config.py                       # LLM instances, caching
├── database.py                     # All Supabase operations
├── utils.py                        # Shared utilities, helpers
│
├── agents/
│   ├── __init__.py
│   ├── intent.py                   # Intent analysis agent
│   ├── context.py                  # Context analysis agent
│   ├── domain.py                   # Domain identification agent
│   └── prompt_engineer.py          # Final rewrite agent
│
├── memory/
│   ├── __init__.py
│   ├── langmem.py                  # LangMem integration (app surface)
│   ├── supermemory.py              # Supermemory (MCP surface only)
│   └── profile_updater.py          # Background profile updates
│
├── multimodal/
│   ├── __init__.py
│   ├── transcribe.py               # Whisper voice transcription
│   ├── image.py                    # Image base64 handling
│   └── files.py                    # PDF/DOCX/TXT extraction
│
├── mcp/
│   ├── __init__.py
│   └── server.py                   # MCP protocol, tool definitions
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py              # Agent unit tests
│   ├── test_workflow.py            # Integration tests
│   └── test_endpoints.py           # API endpoint tests
│
├── Dockerfile                      # No hot-reload
├── docker-compose.yml              # Local development
├── requirements.txt                # Python dependencies
├── requirements-dev.txt            # Pytest, linting, etc.
├── .env.example                    # Environment template
├── .gitignore
├── README.md
└── DOCS/
    ├── RULES.md                    # This file
    ├── IMPLEMENTATION_PLAN.md      # Phase-by-phase guide
    ├── Masterplan.html             # High-level vision
    └── ARCHITECTURE.md             # Technical deep dive
```

### Key Organizational Principles

- **Agents live together** — All 4 agents in `agents/` folder
- **Memory systems together** — All memory implementations in `memory/`
- **Multimodal together** — All input types in `multimodal/`
- **Tests mirror source** — `tests/test_agents.py` mirrors `agents/`
- **Docs in DOCS** — All documentation centralized, never in code

---

## FINAL PRINCIPLES — REMEMBER THESE ALWAYS

> **"Keep it simple, keep it fast, keep Kira's personality consistent."**

1. **Simple** — Solve the problem with the least complex solution
2. **Fast** — Optimize for user-perceived latency first
3. **Consistent** — Kira never drifts, never contradicts herself
4. **Maintainable** — Write code junior developers can understand
5. **Testable** — Every function should have a clear input/output
6. **Secure** — Every endpoint protected, every input validated
7. **Observable** — Log contextually, monitor latencies, trace errors
8. **Scalable** — Design for growth from day one

---

## Document Change Log

| Date | Change | Reason |
|------|--------|--------|
| March 2026 | Initial creation | Project inception |
| March 2026 | Added DRY, Modularity, Testing | Enhanced code quality standards |
| March 2026 | Added Naming Conventions | Clarify naming patterns |
| March 2026 | Added Performance Optimization | Ensure targets are met |

---

*This RULES.md represents the complete agreed architecture for PromptForge v2.0. All code must conform to these standards. When in doubt, refer back to these principles.*

**Feed this document to your AI coding agent. Reference it explicitly in all prompts. It is the source of truth for development.**
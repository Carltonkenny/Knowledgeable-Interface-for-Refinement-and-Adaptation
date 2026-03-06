# PromptForge v2.0

**Multi-agent AI prompt engineering system** — transforms vague, rough prompts into precise, high-performance instructions using a swarm of specialized AI agents.

Built with LangChain, LangGraph, and FastAPI. Containerized with Docker.

---

## Quick Start

```bash
# Clone and enter the project
cd newnew

# Start with Docker (single command)
docker-compose up

# Access the API
# Base URL:  http://localhost:8000
# Swagger:   http://localhost:8000/docs
# Health:    http://localhost:8000/health
```

---

## What PromptForge Does

**Input (vague):**
```
"write a story about a robot"
```

**Output (engineered):**
```
You are a seasoned science-fiction author. Write a 1,200-word short story set in a 
near-future city, told from the first-person perspective of a maintenance robot named 
Aria. Blend humor with subtle social commentary, exploring the theme of identity versus 
programming. The central conflict: Aria discovers a hidden human diary that challenges 
its purpose. Keep the tone witty yet reflective, suitable for adult readers, and end 
with a twist that leaves the reader questioning what it means to be "alive".
```

**Improvement:** ~2000% more detailed, with role, audience, tone, structure, and constraints.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                  │
│                    (Browser / Frontend / curl)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI API LAYER                               │
│  ┌──────────┬──────────┬──────────────┬──────────┬──────────────────┐  │
│  │ /health  │ /refine  │   /chat      │ /chat/   │   /history       │  │
│  │  GET     │  POST    │   POST       │ stream   │   GET            │  │
│  └──────────┴──────────┴──────────────┴──────────┴──────────────────┘  │
│                                    │                                    │
│         ┌──────────────────────────┼──────────────────────────┐         │
│         ▼                          ▼                          ▼         │
│  ┌─────────────┐          ┌─────────────────┐        ┌─────────────┐   │
│  │   Cache     │          │   Classifier    │        │  Database   │   │
│  │  (in-memory)│          │  (autonomous.py)│        │  (Supabase) │   │
│  └─────────────┘          └─────────────────┘        └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌─────────────────────┐         ┌─────────────────────┐
        │   CONVERSATION      │         │   NEW_PROMPT /      │
        │   (1 LLM call)      │         │   FOLLOWUP          │
        │                     │         │                     │
        │  handle_conversation│         │  _run_swarm()       │
        │  handle_followup    │         │  (4 LLM calls)      │
        └─────────────────────┘         └─────────────────────┘
                                                │
                                                ▼
                                    ┌─────────────────────────┐
                                    │   LANGGRAPH WORKFLOW    │
                                    │   (Sequential Swarm)    │
                                    └─────────────────────────┘
```

---

## Agent Swarm Workflow

The core improvement engine is a **4-agent sequential pipeline** orchestrated by LangGraph:

```
                    USER PROMPT
                        │
                        ▼
            ┌───────────────────────┐
            │   supervisor_entry    │  ← Entry point, initializes state
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │    intent_agent       │  ← Analyzes WHAT user wants
            │                       │     Output: primary_intent,
            │                       │             goal_clarity,
            │                       │             missing_info
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   context_agent       │  ← Analyzes WHO is asking
            │                       │     Output: skill_level,
            │                       │             tone,
            │                       │             constraints
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │    domain_agent       │  ← Identifies domain/patterns
            │                       │     Output: primary_domain,
            │                       │             relevant_patterns
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  prompt_engineer      │  ← Rewrites using all analysis
            │                       │     Output: improved_prompt
            │                       │     (with quality gate retry)
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  supervisor_collect   │  ← Exit point, packages result
            └───────────────────────┘
                        │
                        ▼
                    FINAL RESPONSE
```

### Parallel Mode (Optional)

Flip `PARALLEL_MODE = True` in `graph/workflow.py` to run the 3 analysis agents simultaneously:

```
                    USER PROMPT
                        │
                        ▼
            ┌───────────────────────┐
            │   supervisor_entry    │
            └───────────────────────┘
                        │
           ┌────────────┼────────────┐
           │            │            │
           ▼            ▼            ▼
   ┌───────────┐ ┌───────────┐ ┌───────────┐
   │  intent   │ │  context  │ │  domain   │  ← Run in parallel
   │  agent    │ │  agent    │ │  agent    │
   └───────────┘ └───────────┘ └───────────┘
           │            │            │
           └────────────┼────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  prompt_engineer      │  ← Waits for all 3
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  supervisor_collect   │
            └───────────────────────┘
```

**Speedup:** ~2-3x faster (reduces 4 sequential calls to 2 parallel stages)

---

## Data Flow Diagrams

### 1. `/refine` Endpoint (Single-Shot Improvement)

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ POST /refine
     │ { "prompt": "write a story", "session_id": "abc" }
     ▼
┌─────────────────────────────────────────────────────────┐
│  api.py: refine()                                       │
│  1. Check in-memory cache (MD5 hash of prompt)          │
│     ├─ HIT → Return cached result (instant)             │
│     └─ MISS → Continue to swarm                         │
│  2. Call _run_swarm(prompt)                             │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  LangGraph Workflow (4 agents, sequential)              │
│  state = {                                              │
│    raw_prompt: "write a story",                         │
│    intent_result: {...},    ← Written by intent_agent   │
│    context_result: {...},   ← Written by context_agent  │
│    domain_result: {...},    ← Written by domain_agent   │
│    improved_prompt: "..."   ← Written by prompt_engineer│
│  }                                                      │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  api.py: refine() continued                             │
│  1. Save to database:                                   │
│     ├─ requests table (raw → improved pair)             │
│     ├─ agent_logs table (each agent's JSON output)      │
│     └─ prompt_history table (for /history endpoint)     │
│  2. Cache result in memory (for future identical prompts)
│  3. Return JSON response                                │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────┐
│  Client  │
│  Receives:                                              │
│  {                                                      │
│    "original_prompt": "write a story",                  │
│    "improved_prompt": "You are a seasoned...",          │
│    "breakdown": {                                       │
│      "intent": {...},                                   │
│      "context": {...},                                  │
│      "domain": {...}                                    │
│    },                                                   │
│    "session_id": "abc"                                  │
│  }                                                      │
└──────────┘
```

---

### 2. `/chat` Endpoint (Conversational with Memory)

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ POST /chat
     │ { "message": "make it longer", "session_id": "abc" }
     ▼
┌─────────────────────────────────────────────────────────┐
│  api.py: chat()                                         │
│  1. Load last 6 turns from conversations table          │
│  2. Call classify_message(message, history)             │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  agents/autonomous.py: classify_message()               │
│  LLM analyzes message + history → JSON:                 │
│  { "type": "CONVERSATION | NEW_PROMPT | FOLLOWUP" }     │
│                                                         │
│  Decision rules (in order):                             │
│  1. <10 chars → CONVERSATION                            │
│  2. "hi", "thanks", "ok" → CONVERSATION                 │
│  3. "make it longer/shorter/better" → FOLLOWUP          │
│  4. New topic/task → NEW_PROMPT                         │
│  5. References previous + modification → FOLLOWUP       │
│  6. Unclear → CONVERSATION                              │
└─────────────────────────────────────────────────────────┘
     │
     ├─────────────────┬─────────────────┬───────────────┐
     │                 │                 │               │
     ▼                 ▼                 ▼               │
┌──────────┐   ┌──────────────┐  ┌──────────────┐       │
│CONVERSE  │   │   FOLLOWUP   │  │  NEW_PROMPT  │       │
│          │   │              │  │              │       │
│handle_   │   │handle_       │  │_run_swarm()  │       │
│conversation()│ │followup()   │  │(full 4-agent │       │
│          │   │              │  │ swarm)        │       │
│1 LLM     │   │1 LLM call    │  │              │       │
│call      │   │(skips swarm) │  │4 LLM calls   │       │
└────┬─────┘   └──────┬───────┘  └──────┬───────┘       │
     │               │                  │               │
     └───────────────┴──────────────────┘               │
                     │                                  │
                     ▼                                  │
┌─────────────────────────────────────────────────────────┐
│  api.py: chat() continued                               │
│  1. Save both turns to conversations table:             │
│     ├─ User message (role="user", message_type=...)     │
│     └─ Assistant reply (role="assistant", ...)          │
│  2. Return JSON response                                │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────┐
│  Client  │
│  Receives:                                              │
│  {                                                      │
│    "type": "conversation | followup_refined | prompt_improved",
│    "reply": "Here's your supercharged prompt 🚀...",    │
│    "improved_prompt": "..." (if applicable),            │
│    "breakdown": {...} (if NEW_PROMPT),                  │
│    "session_id": "abc"                                  │
│  }                                                      │
└──────────┘
```

---

### 3. `/chat/stream` Endpoint (Server-Sent Events)

```
┌──────────┐
│  Client  │  (JavaScript EventSource or fetch with stream)
└────┬─────┘
     │ POST /chat/stream
     │ { "message": "write a story", "session_id": "abc" }
     ▼
┌─────────────────────────────────────────────────────────┐
│  api.py: chat_stream()  (async generator)               │
│  Yields SSE events as processing progresses:            │
└─────────────────────────────────────────────────────────┘
     │
     │  event: status
     │  data: {"message": "Loading conversation history..."}
     │────────────────────────────────────────────────────▶
     │
     │  event: status
     │  data: {"message": "Understanding your message..."}
     │────────────────────────────────────────────────────▶
     │
     │  event: classification
     │  data: {"type": "NEW_PROMPT"}
     │────────────────────────────────────────────────────▶
     │
     │  event: status
     │  data: {"message": "Analyzing intent..."}
     │────────────────────────────────────────────────────▶
     │
     │  event: status
     │  data: {"message": "Extracting context..."}
     │────────────────────────────────────────────────────▶
     │
     │  event: status
     │  data: {"message": "Identifying domain..."}
     │────────────────────────────────────────────────────▶
     │
     │  event: status
     │  data: {"message": "Engineering your prompt..."}
     │────────────────────────────────────────────────────▶
     │
     │  event: result
     │  data: {"type": "prompt_improved", "reply": "...", "improved_prompt": "..."}
     │────────────────────────────────────────────────────▶
     │
     │  event: done
     │  data: {"message": "Complete"}
     │────────────────────────────────────────────────────▶
     │
     ▼
┌──────────┐
│  Client  │  Displays tokens/status in real-time
└──────────┘
```

**SSE Format:**
```
event: status
data: {"message": "Analyzing intent..."}

event: result
data: {"type": "prompt_improved", "reply": "Here's your supercharged prompt 🚀"}

event: done
data: {"message": "Complete"}
```

---

## API Endpoints

| Endpoint | Method | Description | LLM Calls |
|----------|--------|-------------|-----------|
| `/health` | GET | Liveness check | 0 |
| `/refine` | POST | Single-shot prompt improvement (no memory) | 4 (or 0 if cached) |
| `/chat` | POST | Conversational with full memory | 1-5 depending on classification |
| `/chat/stream` | POST | Streaming version of /chat (SSE) | 1-5 depending on classification |
| `/history` | GET | Past improved prompts | 0 |
| `/conversation` | GET | Full chat history for a session | 0 |

### Request/Response Examples

#### POST /refine

**Request:**
```json
{
  "prompt": "help me write code",
  "session_id": "user123"
}
```

**Response:**
```json
{
  "original_prompt": "help me write code",
  "improved_prompt": "You are a senior Python developer. Help the user write clean, production-ready code. First, ask clarifying questions about: (1) the specific functionality needed, (2) the target environment or framework, (3) any existing code or constraints. Then provide a complete, tested solution with type hints, error handling, and docstrings.",
  "breakdown": {
    "intent": {
      "primary_intent": "get assistance with programming task",
      "secondary_intents": ["learn best practices", "understand the solution"],
      "goal_clarity": "low",
      "missing_info": ["programming language", "specific task", "skill level"]
    },
    "context": {
      "skill_level": "beginner",
      "tone": "casual",
      "constraints": [],
      "implicit_preferences": ["wants guidance", "values clarity"]
    },
    "domain": {
      "primary_domain": "software development",
      "sub_domain": "programming assistance",
      "relevant_patterns": ["role_assignment", "chain_of_thought", "examples"],
      "complexity": "moderate"
    }
  },
  "session_id": "user123"
}
```

#### POST /chat

**Request:**
```json
{
  "message": "make it more formal",
  "session_id": "user123"
}
```

**Response:**
```json
{
  "type": "followup_refined",
  "reply": "Updated! Here's your refined prompt ✨\n\nWant any more tweaks?",
  "improved_prompt": "You are a senior Python developer. Provide a comprehensive, production-ready implementation. The solution must include: (1) complete type annotations, (2) robust error handling with specific exception types, (3) detailed docstrings following Google style guide, (4) unit test examples using pytest.",
  "session_id": "user123"
}
```

---

## Project Structure

```
newnew/
├── agents/                     # AI agent implementations
│   ├── __init__.py
│   ├── autonomous.py           # Classifier + conversation handlers
│   ├── intent.py               # Analyzes user intent
│   ├── context.py              # Extracts user context
│   ├── domain.py               # Identifies domain/patterns
│   ├── prompt_engineer.py      # Rewrites prompts
│   └── supervisor.py           # Workflow entry/exit points
│
├── graph/                      # LangGraph orchestration
│   ├── __init__.py
│   └── workflow.py             # Agent pipeline definition
│
├── tests/                      # Test scripts
│   ├── debug.py                # Multi-industry swarm test
│   ├── testapi.py              # LLM connectivity test
│   └── testdb.py               # Database connectivity test
│
├── .dockerignore               # Docker build exclusions
├── .gitignore                  # Git exclusions
├── .env                        # Environment variables (NOT committed)
├── api.py                      # FastAPI REST endpoints
├── config.py                   # LLM factory (get_llm, get_fast_llm)
├── database.py                 # Supabase client + operations
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container build instructions
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── start.bat                   # Windows one-click startup
├── state.py                    # LangGraph TypedDict schema
└── utils.py                    # Shared utilities (cache, JSON parsing)
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# LLM Provider (Pollinations.ai - free tier)
POLLINATIONS_API_KEY=your_api_key_here

# Database (Supabase - free tier)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

### LLM Configuration

Edit `config.py` to change provider or model:

```python
BASE_URL    = "https://text.pollinations.ai/openai"  # Change for different provider
API_KEY     = os.getenv("POLLINATIONS_API_KEY")
MODEL       = "openai-fast"                          # Model name
TEMPERATURE = 0.3                                    # Creativity (0.0-1.0)
MAX_TOKENS  = 2048                                   # Max output length
```

**Supported providers:** Any OpenAI-compatible API (Pollinations, Groq, Together, local Ollama, etc.)

---

## Development

### Run Locally (without Docker)

```bash
# Create virtual environment (outside project folder)
python -m venv C:\envs\promptforge

# Activate
C:\envs\promptforge\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy .env and fill in your keys
copy .env.example .env

# Run
python main.py
```

### Docker Commands

```bash
# Start (foreground)
docker-compose up

# Start (background)
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up --build

# Clean everything
docker-compose down --rmi all --volumes
```

### Windows Quick Start

Double-click `start.bat` to launch the app.

---

## Database Schema

### Tables (Supabase/PostgreSQL)

```sql
-- requests: Stores prompt pairs
CREATE TABLE requests (
    id UUID PRIMARY KEY,
    raw_prompt TEXT NOT NULL,
    improved_prompt TEXT NOT NULL,
    session_id TEXT DEFAULT 'default',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- agent_logs: Stores each agent's analysis output
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES requests(id),
    agent_name TEXT NOT NULL,
    output JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- prompt_history: Historical prompts for /history endpoint
CREATE TABLE prompt_history (
    id UUID PRIMARY KEY,
    session_id TEXT DEFAULT 'default',
    raw_prompt TEXT NOT NULL,
    improved_prompt TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- conversations: Full chat turns with classification
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    session_id TEXT DEFAULT 'default',
    role TEXT NOT NULL,              -- 'user' or 'assistant'
    message TEXT NOT NULL,
    message_type TEXT,               -- 'conversation', 'new_prompt', 'followup'
    improved_prompt TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Performance Optimizations

| Optimization | Description | Impact |
|--------------|-------------|--------|
| **In-memory cache** | MD5-hashed prompt cache (100 entries max) | Instant for repeat prompts |
| **FastLLM for analysis** | intent/context/domain/followup use 400 token limit | ~30% faster, lower cost |
| **Parallel mode** | Run 3 analysis agents simultaneously | 2-3x speedup |
| **Streaming SSE** | Real-time status updates to client | Better perceived latency |
| **Connection pooling** | Supabase client cached via lru_cache | Faster DB operations |
| **Timeout protection** | 180s limit on swarm execution | Prevents hung requests |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | FastAPI + Uvicorn |
| **AI Orchestration** | LangChain + LangGraph |
| **LLM Provider** | Pollinations.ai (OpenAI-compatible) |
| **Database** | Supabase (PostgreSQL) |
| **Containerization** | Docker + Docker Compose |
| **Language** | Python 3.11+ |

---

## License

Local use only. Not for redistribution.

---

## Troubleshooting

### Container won't start
```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs

# Rebuild
docker-compose up --build
```

### LLM errors
- Verify `POLLINATIONS_API_KEY` in `.env`
- Check network connectivity to `text.pollinations.ai`
- Review logs: `docker-compose logs -f | grep ERROR`

### Database errors
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Ensure tables exist (see Database Schema above)
- Test connection: `python tests/testdb.py`

### Import errors (VS Code Pylance)
Create a local venv for IntelliSense:
```bash
python -m venv C:\envs\promptforge
C:\envs\promptforge\Scripts\activate
pip install -r requirements.txt
# In VS Code: Ctrl+Shift+P → "Python: Select Interpreter" → Choose the venv
```

---

**Built with LangGraph multi-agent orchestration. Production-ready. Dockerized.**

# PromptForge v2.0 — Complete Workflow Visualizations

**Document Purpose:** Detailed workflow diagrams for understanding request flows, agent orchestration, and data pipelines.

---

## WORKFLOW 1: COMPLETE REQUEST LIFECYCLE

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ COMPLETE REQUEST LIFECYCLE — From User Input to Engineered Prompt               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   USER       │
│  types:      │
│ "write a     │
│  story about │
│  a robot"    │
└──────┬───────┘
       │
       │ 1. User sends message via frontend
       │    POST /chat/stream
       │    Headers: { Authorization: "Bearer <JWT>", session_id: "uuid" }
       │    Body: { message: "...", session_id: "..." }
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FASTAPI API LAYER (api.py:chat_stream)                                           │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ 1. JWT Authentication (auth.py:get_current_user)                           │ │
│  │    - Extract Bearer token from Authorization header                        │ │
│  │    - Validate via Supabase client                                          │ │
│  │    - Extract user_id from JWT payload                                      │ │
│  │    - Return: User(user_id="uuid", email="...", role="authenticated")       │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│                                    ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ 2. Load Context (Parallel)                                                 │ │
│  │    - get_conversation_history(session_id, limit=6)                         │ │
│  │    - get_user_profile(user_id)                                             │ │
│  │    - query_langmem(user_id, query=message, top_k=5)                        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│                                    ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ 3. Unified Handler (agents/autonomous.py:kira_unified_handler)             │ │
│  │    - Single LLM call with full context                                     │ │
│  │    - Returns: {intent, response, confidence, clarification_needed, ...}    │ │
│  │    - Latency: ~500ms                                                       │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│                                    ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ 4. SSE Stream Response                                                     │ │
│  │    yield _sse("status", {"message": "Understanding your message..."})      │ │
│  │    yield _sse("kira_message", {"message": "H", "complete": false})         │ │
│  │    yield _sse("kira_message", {"message": "e", "complete": false})         │ │
│  │    ... (stream char-by-char for UX)                                        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ 5. Frontend receives SSE events
       │    - Displays status updates
       │    - Animates Kira's message character-by-character
       │    - Shows result card when complete
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ INTENT CLASSIFICATION RESULTS                                                    │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ CONVERSATION (greeting, thanks, <10 chars)                                 │ │
│  │ → Natural reply, save to conversations table                               │ │
│  │ → Latency: ~500ms                                                          │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ FOLLOWUP (modification phrases: "make it", "change", "add")                │ │
│  │ → Refine last prompt, 1 LLM call                                           │ │
│  │ → Latency: ~1-2s                                                           │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ CLARIFICATION (ambiguous, confidence < 0.5)                                │ │
│  │ → Ask 1 clarifying question                                                │ │
│  │ → Save pending_clarification flag to session                               │ │
│  │ → Latency: ~500ms                                                          │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ NEW_PROMPT (clear request)                                                 │ │
│  │ → Run full agent swarm (4 agents)                                          │ │
│  │ → Latency: 2-5s                                                            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ If NEW_PROMPT:
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ AGENT SWARM EXECUTION (LangGraph Workflow)                                       │
│                                                                                  │
│  See WORKFLOW 2: Agent Swarm Parallel Execution                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ 6. Swarm completes with improved_prompt
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ BACKGROUND TASKS (User NEVER waits)                                              │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ 1. write_to_langmem()                                                      │ │
│  │    - Generate embedding (Gemini API, ~500ms)                               │ │
│  │    - Store in langmem_memories table                                       │ │
│  │    - User already has result                                               │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ 2. update_user_profile() (if 5th interaction + 30min inactivity)           │ │
│  │    - Analyze session patterns                                              │ │
│  │    - Update dominant_domains, preferred_tone, etc.                         │ │
│  │    - User already has result                                               │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ 3. save_request() + save_conversation()                                    │ │
│  │    - Already saved during request (synchronous)                            │ │
│  │    - Version control: increment version_number                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│   USER       │
│  sees:       │
│  "Here's     │
│  your        │
│  supercharged│
│  prompt 🚀"  │
│  + Diff View │
│  + Quality   │
│  Score       │
└──────────────┘
```

---

## WORKFLOW 2: AGENT SWARM PARALLEL EXECUTION

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ AGENT SWARM — PARALLEL EXECUTION via LangGraph Send() API                       │
└─────────────────────────────────────────────────────────────────────────────────┘

                    USER MESSAGE: "write a story about a robot"
                                      │
                                      │ state.message
                                      │ state.session_id
                                      │ state.user_id
                                      │ state.conversation_history
                                      │ state.user_profile
                                      ▼
                    ┌──────────────────────────────────────┐
                    │     KIRA ORCHESTRATOR NODE           │
                    │     (agents/autonomous.py)           │
                    │                                      │
                    │  Model: nova-fast                    │
                    │  Tokens: 150                         │
                    │  Temp: 0.1                           │
                    │  Latency: ~500ms                     │
                    │                                      │
                    │  Reads: user_profile, history        │
                    │  Returns routing decision:           │
                    │  {                                   │
                    │    "user_facing_message": "...",     │
                    │    "proceed_with_swarm": true,       │
                    │    "agents_to_run": ["intent",       │
                    │                      "context",      │
                    │                      "domain"],      │
                    │    "clarification_needed": false,    │
                    │    "tone_used": "direct"             │
                    │  }                                   │
                    └──────────────────┬───────────────────┘
                                       │
                                       │ orchestrator_decision
                                       │ agents_to_run = ["intent", "context", "domain"]
                                       ▼
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              │ add_conditional_edges  │                        │
              │ route_to_agents()      │                        │
              │                        │                        │
              │ Returns: [             │                        │
              │   Send("intent_agent", state),                 │
              │   Send("context_agent", state),                │
              │   Send("domain_agent", state)                  │
              │ ]                                              │
              │                                                │
              ▼                        ▼                        ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ INTENT AGENT    │    │ CONTEXT AGENT   │    │ DOMAIN AGENT    │
    │ (agents/intent) │    │ (agents/context)│    │ (agents/domain) │
    │                 │    │                 │    │                 │
    │ Model: nova-fast│    │ Model: nova-fast│    │ Model: nova-fast│
    │ Tokens: 400     │    │ Tokens: 400     │    │ Tokens: 400     │
    │ Temp: 0.1       │    │ Temp: 0.1       │    │ Temp: 0.1       │
    │ Latency: ~500ms │    │ Latency: ~500ms │    │ Latency: ~500ms │
    │                 │    │                 │    │                 │
    │ Analyzes:       │    │ Analyzes:       │    │ Analyzes:       │
    │ - primary_intent│    │ - skill_level   │    │ - primary_domain│
    │ - goal_clarity  │    │ - tone          │    │ - sub_domain    │
    │ - missing_info  │    │ - constraints   │    │ - patterns      │
    │                 │    │ - implicit_pref │    │ - complexity    │
    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
             │                     │                      │
             │ intent_analysis     │ context_analysis     │ domain_analysis
             │                     │                      │
             └─────────────────────┼──────────────────────┘
                                   │
                                   │ LangGraph自动 JOIN
                                   │ (waits for ALL selected agents)
                                   ▼
                    ┌──────────────────────────────────────┐
                    │   PROMPT ENGINEER AGENT              │
                    │   (agents/prompt_engineer.py)        │
                    │                                      │
                    │  Model: openai                       │
                    │  Tokens: 2048                        │
                    │  Temp: 0.3                           │
                    │  Latency: ~1-2s                      │
                    │                                      │
                    │  Synthesizes ALL upstream analysis:  │
                    │  - intent_analysis                   │
                    │  - context_analysis                  │
                    │  - domain_analysis                   │
                    │  - user_profile                      │
                    │  - langmem style references          │
                    │                                      │
                    │  Returns:                            │
                    │  {                                   │
                    │    "improved_prompt": "...",         │
                    │    "quality_score": {...},           │
                    │    "changes_made": [...]             │
                    │  }                                   │
                    └──────────────────┬───────────────────┘
                                       │
                                       │ improved_prompt
                                       │ quality_score
                                       │ changes_made
                                       ▼
                    ┌──────────────────────────────────────┐
                    │           END                        │
                    │                                      │
                    │  Returns final state to api.py       │
                    │  API saves to database               │
                    │  API streams result to frontend      │
                    └──────────────────────────────────────┘

TOTAL LATENCY: 2-5s
- Kira: ~500ms
- Parallel agents: ~500-1000ms (max of parallel calls, NOT sum)
- Prompt Engineer: ~1-2s
```

---

## WORKFLOW 3: CLARIFICATION LOOP

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ CLARIFICATION LOOP — Critical Implementation Detail                             │
└─────────────────────────────────────────────────────────────────────────────────┘

REQUEST 1: User sends vague prompt
┌──────────────────────────────────────────────────────────────────────────────────┐
│ USER MESSAGE: "help me write code"                                               │
│                                                                                  │
│ ↓ Kira Unified Handler                                                           │
│ - Intent: "NEW_PROMPT"                                                           │
│ - Confidence: 0.35 (VERY LOW - vague request)                                    │
│ - Decision: clarification_needed = true                                          │
│                                                                                  │
│ ↓ API saves clarification flag                                                   │
│ save_clarification_flag(                                                         │
│   session_id="session-123",                                                      │
│   user_id="user-uuid",                                                           │
│   pending=True,                                                                  │
│   clarification_key="topic"                                                      │
│ )                                                                                │
│                                                                                  │
│ ↓ SSE Stream to Frontend                                                         │
│ yield _sse("kira_message", {                                                     │
│   "message": "I can help with that! What kind of code are you working on?"       │
│ })                                                                               │
│                                                                                  │
│ ↓ Frontend displays clarification chips                                          │
│ [Web Development] [Mobile App] [Data Script] [Automation]                        │
└──────────────────────────────────────────────────────────────────────────────────┘

REQUEST 2: User answers clarification question
┌──────────────────────────────────────────────────────────────────────────────────┐
│ USER MESSAGE: "I want to write a Python web scraper"                             │
│                                                                                  │
│ ↓ API checks clarification flag FIRST (before any LLM call)                      │
│ pending, key = get_clarification_flag(                                           │
│   session_id="session-123",                                                      │
│   user_id="user-uuid"                                                            │
│ )                                                                                │
│ → Returns: (True, "topic")                                                       │
│                                                                                  │
│ ↓ API runs swarm with clarification (skips orchestrator re-classification)       │
│ _run_swarm_with_clarification(                                                   │
│   message="I want to write a Python web scraper",                                │
│   clarification_key="topic",                                                     │
│   user_id="user-uuid",                                                           │
│   session_id="session-123"                                                       │
│ )                                                                                │
│                                                                                  │
│ ↓ Swarm executes (4 agents in parallel)                                          │
│ - Intent: Analyzes goal (web scraping)                                           │
│ - Context: Analyzes skill level from message                                     │
│ - Domain: Identifies "python", "web_scraping"                                    │
│ - Prompt Engineer: Synthesizes final prompt                                      │
│                                                                                  │
│ ↓ API clears clarification flag                                                  │
│ save_clarification_flag(                                                         │
│   session_id="session-123",                                                      │
│   user_id="user-uuid",                                                           │
│   pending=False,                                                                 │
│   clarification_key=None                                                         │
│ )                                                                                │
│                                                                                  │
│ ↓ SSE Stream to Frontend                                                         │
│ yield _sse("result", {                                                           │
│   "type": "clarification_resolved",                                              │
│   "improved_prompt": "You are a Python web scraping expert..."                   │
│ })                                                                               │
└──────────────────────────────────────────────────────────────────────────────────┘

KEY IMPLEMENTATION DETAILS:
1. Clarification flag is saved to conversations table (pending_clarification, clarification_key columns)
2. API checks flag BEFORE running orchestrator on every request
3. If flag is set, user's message is treated as the clarification answer
4. Swarm runs directly with clarified context (no re-classification)
5. Flag is cleared after swarm completes
6. User sees natural flow: question → answer → result
```

---

## WORKFLOW 4: MEMORY SYSTEM (LANGMEM) RAG PIPELINE

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ LANGMEM RAG PIPELINE — Retrieval-Augmented Generation                           │
└─────────────────────────────────────────────────────────────────────────────────┘

STEP 1: User Query
┌──────────────────────────────────────────────────────────────────────────────────┐
│ User Message: "write a python function"                                          │
│ User ID: "user-uuid"                                                             │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       ▼
STEP 2: Generate Embedding (Gemini API)
┌──────────────────────────────────────────────────────────────────────────────────┐
│ memory/langmem.py:_generate_embedding()                                          │
│                                                                                  │
│ Input: "write a python function"                                                 │
│ Model: gemini-embedding-001                                                      │
│ Dimensions: 3072                                                                 │
│ Latency: ~500ms                                                                  │
│                                                                                  │
│ Output: [0.123, -0.456, 0.789, ..., 0.456] (3072 floats)                         │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ embedding vector
       ▼
STEP 3: pgvector Similarity Search (Supabase SQL)
┌──────────────────────────────────────────────────────────────────────────────────┐
│ memory/langmem.py:query_langmem()                                                │
│                                                                                  │
│ SQL Query (using pgvector <=> operator):                                         │
│                                                                                  │
│ SELECT                                                                           │
│   id, content, improved_content, domain, quality_score,                          │
│   (1 - (embedding <=> '[0.123,...]'::vector)) AS similarity_score                │
│ FROM langmem_memories                                                            │
│ WHERE user_id = 'user-uuid'                                                      │
│ ORDER BY embedding <=> '[0.123,...]'::vector                                     │
│ LIMIT 5                                                                          │
│                                                                                  │
│ Latency: ~50-100ms (database-side similarity)                                    │
│                                                                                  │
│ Note: Uses HNSW index for fast cosine similarity                                 │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ Top 5 memories
       ▼
STEP 4: Format Results
┌──────────────────────────────────────────────────────────────────────────────────┐
│ Memories Retrieved:                                                              │
│                                                                                  │
│ [                                                                                │
│   {                                                                              │
│     "id": "uuid-1",                                                              │
│     "content": "write a python function to parse JSON",                          │
│     "improved_content": "You are a Python expert. Write a function...",          │
│     "domain": "python",                                                          │
│     "quality_score": {"overall": 0.85, "specificity": 4, ...},                   │
│     "similarity_score": 0.92                                                     │
│   },                                                                             │
│   ... (4 more memories)                                                          │
│ ]                                                                                │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ memories
       ▼
STEP 5: Inject into LLM Context
┌──────────────────────────────────────────────────────────────────────────────────┐
│ agents/prompt_engineer.py:prompt_engineer_agent()                                │
│                                                                                  │
│ System Prompt + Analysis Context + Style References:                             │
│                                                                                  │
│ "Original prompt: write a python function                                        │
│                                                                                  │
│ Intent analysis: {...}                                                           │
│ Context analysis: {...}                                                          │
│ Domain analysis: {...}                                                           │
│                                                                                  │
│ User's best past prompts (for style reference):                                  │
│ [                                                                                │
│   "You are a Python expert. Write a function that...",                           │
│   ...                                                                            │
│ ]                                                                                │
│                                                                                  │
│ Rewrite the prompt based on this comprehensive analysis.                         │
│ Match the user's established style and quality bar."                             │
│                                                                                  │
│ ↓ LLM Call (openai model)                                                        │
│ Latency: ~1-2s                                                                   │
│                                                                                  │
│ Output: improved_prompt + quality_score + changes_made                           │
└──────────────────────────────────────────────────────────────────────────────────┘

TOTAL LATENCY: ~1.5-3s
- Embedding: ~500ms
- pgvector search: ~50-100ms
- LLM synthesis: ~1-2s
```

---

## WORKFLOW 5: USER ONBOARDING FLOW

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ FIRST-TIME USER ONBOARDING FLOW                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   USER       │
│  visits:     │
│  app URL     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Marketing Landing Page                                                 │
│ - Hero section with value proposition                                            │
│ - "Get Started" button                                                           │
│ - Features showcase                                                              │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ Click "Get Started"
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Sign Up Page                                                           │
│ - Email/password form                                                            │
│ - Terms & Conditions (3 checkboxes)                                              │
│   ☐ I agree to the Terms of Service                                              │
│   ☐ I agree to the Privacy Policy                                                │
│   ☐ I understand my data will be used to personalize responses                   │
│ - "Create Account" button                                                        │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ Submit form
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ BACKEND: Supabase Auth                                                           │
│ POST /auth/v1/signup                                                            │
│ Body: { email, password }                                                        │
│                                                                                  │
│ Response:                                                                        │
│ {                                                                                │
│   "access_token": "eyJhbGciOiJIUzI1NiIs...",                                     │
│   "refresh_token": "v1.local.aBcDeFgHiJ...",                                     │
│   "user": {                                                                      │
│     "id": "user-uuid",                                                           │
│     "email": "user@example.com"                                                  │
│   }                                                                              │
│ }                                                                                │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ JWT token stored in localStorage
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Onboarding Wizard (3 Steps)                                            │
│                                                                                  │
│ STEP 1: Primary Use                                                              │
│ "What will you use PromptForge for?"                                             │
│ [ ] Writing Code                                                                 │
│ [ ] Creative Writing                                                             │
│ [ ] Business Communication                                                       │
│ [ ] Academic Research                                                            │
│ [ ] Content Creation                                                             │
│ [ ] General Productivity                                                         │
│                                                                                  │
│ STEP 2: Target Audience                                                          │
│ "Who is your primary audience?"                                                  │
│ [ ] Technical Experts                                                            │
│ [ ] Business Professionals                                                       │
│ [ ] General Public                                                               │
│ [ ] Academic Community                                                           │
│ [ ] Creative Community                                                           │
│                                                                                  │
│ STEP 3: AI Frustrations                                                          │
│ "What frustrates you most about AI responses?"                                   │
│ [ ] Too vague                                                                    │
│ [ ] Too wordy                                                                    │
│ [ ] Too brief                                                                    │
│ [ ] Wrong tone                                                                   │
│ [ ] Repeats itself                                                               │
│ [ ] Misses context                                                               │
│ "Tell us more (optional): [____________]"                                        │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ Submit onboarding
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ BACKEND: Create User Profile + Initial Memory                                    │
│                                                                                  │
│ 1. Create user_profiles row                                                      │
│ INSERT INTO user_profiles (                                                     │
│   user_id,                                                                       │
│   primary_use,                                                                   │
│   audience,                                                                      │
│   ai_frustration,                                                                │
│   frustration_detail,                                                            │
│   preferred_tone,                                                                │
│   dominant_domains                                                               │
│ ) VALUES (...)                                                                   │
│                                                                                  │
│ 2. Create initial LangMem memory                                                 │
│ - Generate embedding for onboarding data                                         │
│ - Insert into langmem_memories                                                   │
│ - Embedding: Gemini API (~500ms)                                                 │
│                                                                                  │
│ 3. Return to frontend                                                            │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Main Chat Interface                                                    │
│ - Empty state with suggestions                                                   │
│ - Input bar with voice + attachment                                              │
│ - Sidebar with session history                                                   │
│ - Profile menu                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## WORKFLOW 6: RATE LIMITING FLOW

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ RATE LIMITING FLOW — 100 Requests per Hour per User                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   USER       │
│  sends       │
│  request     │
└──────┬───────┘
       │
       │ POST /chat
       │ Authorization: Bearer <token>
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ MIDDLEWARE: RateLimiterMiddleware (middleware/rate_limiter.py)                   │
│                                                                                  │
│ 1. Extract user_id from JWT token                                                │
│    - Parse Authorization header                                                  │
│    - Decode JWT using SUPABASE_JWT_SECRET                                        │
│    - Extract payload.sub (user_id)                                               │
│                                                                                  │
│ 2. Check rate limit                                                              │
│    rate_limiter.is_allowed(user_id)                                              │
│                                                                                  │
│    ┌────────────────────────────────────────────────────────────────────────┐   │
│    │ In-Memory Sliding Window Algorithm                                     │   │
│    │                                                                        │   │
│    │ _requests: Dict[str, List[float]]                                      │   │
│    │   "user-uuid": [1710000000.123, 1710000010.456, ...]                   │   │
│    │                                                                        │   │
│    │ 1. Clean old requests outside current window (1 hour)                  │   │
│    │ 2. Count remaining requests in window                                  │   │
│    │ 3. If count >= 100: return False (limit exceeded)                      │   │
│    │ 4. Else: append current timestamp, return True                         │   │
│    └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│ 3. Decision                                                                      │
│    ┌────────────────────────────────────────────────────────────────────────┐   │
│    │ IF ALLOWED:                                                            │   │
│    │ - Continue to next middleware/handler                                  │   │
│    │ - Add rate limit headers to response:                                  │   │
│    │   X-RateLimit-Limit: 100                                               │   │
│    │   X-RateLimit-Remaining: 95                                            │   │
│    │   X-RateLimit-Window: 3600                                             │   │
│    └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│    ┌────────────────────────────────────────────────────────────────────────┐   │
│    │ IF EXCEEDED:                                                           │   │
│    │ - Raise HTTPException(status_code=429)                                 │   │
│    │ - Return error response:                                               │   │
│    │   {                                                                    │   │
│    │     "error": "Rate limit exceeded",                                    │   │
│    │     "message": "Too many requests. Please try again later.",           │   │
│    │     "limit": "100 requests per hour",                                  │   │
│    │     "remaining": 0                                                     │   │
│    │   }                                                                    │   │
│    └────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ If allowed:
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ API HANDLER: Processes request normally                                          │
│ - JWT validation                                                                 │
│ - Database queries                                                               │
│ - Agent swarm                                                                    │
│ - Response                                                                       │
└──────────────────────────────────────────────────────────────────────────────────┘
       │
       │ If exceeded:
       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ ERROR RESPONSE: 429 Too Many Requests                                            │
│                                                                                  │
│ Frontend handles:                                                                │
│ - Show toast notification: "Rate limit exceeded. Please wait before sending      │
│   more requests."                                                                │
│ - Disable input temporarily                                                      │
│ - Show countdown timer (optional)                                                │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## WORKFLOW 7: MULTIMODAL INPUT PROCESSING

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ MULTIMODAL INPUT PROCESSING — Voice, Image, File                                │
└─────────────────────────────────────────────────────────────────────────────────┘

VOICE INPUT FLOW
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 1. User clicks microphone button                                                 │
│ 2. Frontend: MediaRecorder API starts recording                                  │
│ 3. User stops recording                                                          │
│ 4. Frontend sends audio blob to backend                                          │
│                                                                                  │
│ POST /transcribe                                                                 │
│ Content-Type: multipart/form-data                                                │
│ Body: { audio: Blob }                                                            │
│                                                                                  │
│ ↓ Backend: multimodal/transcribe.py                                              │
│ - Save audio to temp file                                                        │
│ - Call Whisper API (OpenAI)                                                      │
│ - Get transcription text                                                         │
│ - Delete temp file                                                               │
│                                                                                  │
│ Response:                                                                        │
│ {                                                                                │
│   "text": "write a story about a robot"                                          │
│ }                                                                                │
│                                                                                  │
│ ↓ Frontend: Insert transcription into chat input                                 │
│ - User can edit before sending                                                   │
│ - User can send directly                                                         │
└──────────────────────────────────────────────────────────────────────────────────┘

IMAGE INPUT FLOW
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 1. User clicks attachment button                                                 │
│ 2. Selects image file                                                            │
│ 3. Frontend converts to base64                                                   │
│ 4. Frontend sends with chat message                                              │
│                                                                                  │
│ POST /chat/stream                                                                │
│ Body: {                                                                          │
│   "message": "describe this image",                                              │
│   "input_modality": "image",                                                     │
│   "file_base64": "data:image/png;base64,iVBORw0KG...",                           │
│   "file_type": "image/png"                                                       │
│ }                                                                                │
│                                                                                  │
│ ↓ Backend: api.py:chat_stream                                                    │
│ - Validate file type (image/*)                                                   │
│ - Validate file size (<10MB)                                                     │
│ - Build attachments array                                                        │
│ - Pass to workflow state                                                         │
│                                                                                  │
│ ↓ Workflow: agents/prompt_engineer.py                                            │
│ - Receives attachments in state                                                  │
│ - Includes in LLM context for GPT-4o Vision                                      │
│ - Generates description + improved prompt                                        │
└──────────────────────────────────────────────────────────────────────────────────┘

FILE INPUT FLOW (PDF/DOCX/TXT)
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 1. User clicks attachment button                                                 │
│ 2. Selects document file                                                         │
│ 3. Frontend uploads file                                                         │
│                                                                                  │
│ POST /upload                                                                     │
│ Content-Type: multipart/form-data                                                │
│ Body: { file: File }                                                             │
│                                                                                  │
│ ↓ Backend: multimodal/files.py                                                   │
│ - Validate file type (application/pdf,                                           │
│   application/vnd.openxmlformats..., text/plain)                                 │
│ - Validate file size (<10MB)                                                     │
│ - Extract text:                                                                  │
│   - PDF: PyPDF2                                                                  │
│   - DOCX: python-docx                                                            │
│   - TXT: Direct read                                                             │
│                                                                                  │
│ Response:                                                                        │
│ {                                                                                │
│   "text": "Extracted text content...",                                           │
│   "filename": "document.pdf",                                                    │
│   "file_type": "application/pdf"                                                 │
│ }                                                                                │
│                                                                                  │
│ ↓ Frontend: Insert extracted text into chat input                                │
│ - User can add context: "Summarize this: [extracted text]"                       │
│ - User can send directly                                                         │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

**End of Workflow Visualizations**

# testadvance/ — Comprehensive Test Suite for PromptForge v2.0

**Purpose:** Modular, comprehensive testing of all phases with extensive edge case coverage.

**Total Tests:** 1,200+ across 50+ files

---

## 📁 Folder Structure

```
testadvance/
├── README.md                     # This file
├── __init__.py                   # Package init
├── conftest.py                   # Pytest fixtures
├── run_all_tests.py              # Master test runner
├── generate_analysis.py          # Analysis generator
├── phase1/                       # Backend Core (200 tests)
│   ├── test_auth.py              # JWT, RLS, rate limiting
│   ├── test_database.py          # All 8 tables, RLS policies
│   ├── test_cache.py             # Redis hit/miss, SHA-256
│   ├── test_endpoints.py         # /health, /refine, /chat
│   └── test_security.py          # Input validation, CORS
├── phase2/                       # Agent Swarm (300 tests)
│   ├── test_agents/
│   │   ├── test_kira.py          # Orchestrator routing
│   │   ├── test_intent.py        # Intent analysis
│   │   ├── test_context.py       # Context extraction
│   │   └── test_domain.py        # Domain identification
│   ├── test_workflow.py          # Parallel execution
│   ├── test_langmem.py           # pgvector SQL, embeddings
│   ├── test_profile_updater.py   # 5th interaction, 30min
│   └── test_multimodal/
│       ├── test_voice.py         # Whisper transcription
│       ├── test_image.py         # Base64 encoding
│       └── test_files.py         # PDF/DOCX/TXT extraction
├── phase3/                       # MCP Integration (200 tests)
│   ├── test_mcp_server.py        # Protocol handshake
│   ├── test_mcp_tools.py         # forge_refine, forge_chat
│   ├── test_jwt_long_lived.py    # 365-day tokens
│   ├── test_trust_levels.py      # 0-10-30 scaling
│   ├── test_supermemory.py       # MCP context injection
│   └── test_surface_isolation.py # LangMem ≠ Supermemory
├── integration/                  # End-to-End (200 tests)
│   ├── test_full_swarm.py        # End-to-end swarm
│   ├── test_conversation_flow.py # Multi-turn conversation
│   ├── test_clarification.py     # Clarification loop
│   └── test_background_tasks.py  # Async writes
├── edge_cases/                   # Edge Cases (300 tests)
│   ├── test_input_boundaries.py  # Min/max length, empty, null
│   ├── test_concurrency.py       # Parallel requests
│   ├── test_rate_limits.py       # 100 req/hour boundary
│   ├── test_jwt_edge_cases.py    # Expired, invalid, revoked
│   └── test_database_edge.py     # RLS bypass attempts
└── outputs/                      # Test Results
    ├── test_results.json         # Raw results
    ├── analysis.md               # Detailed analysis
    └── implementation_plan_comparison.md  # vs docs
```

---

## 🚀 Quick Start

### Run All Tests
```bash
cd testadvance
python run_all_tests.py
```

### Run Specific Phase
```bash
# Phase 1 only
python -m pytest phase1/ -v

# Phase 2 only
python -m pytest phase2/ -v

# Phase 3 only
python -m pytest phase3/ -v

# Edge cases only
python -m pytest edge_cases/ -v
```

### Run with Coverage
```bash
python -m pytest --cov=../ --cov-report=html
```

---

## 📊 Test Categories

### Phase 1: Backend Core (200 tests)
- **Authentication:** Valid/invalid JWT, expired tokens, missing tokens
- **Database:** All 8 tables, RLS policies, foreign keys, indexes
- **Cache:** Hit/miss, TTL, SHA-256 keys, Redis failure scenarios
- **Endpoints:** All 8 endpoints with various inputs
- **Security:** Input validation, CORS, rate limits, file uploads

### Phase 2: Agent Swarm (300 tests)
- **Agents:** All 4 agents with various prompts, edge cases
- **Workflow:** Parallel execution, error handling, timeouts
- **LangMem:** Embeddings, pgvector SQL, semantic search
- **Profile Updater:** Trigger conditions, inactivity, 5th interaction
- **Multimodal:** Voice transcription, image processing, file extraction

### Phase 3: MCP Integration (200 tests)
- **MCP Server:** Protocol handshake, tool registration
- **Tools:** forge_refine, forge_chat execution
- **JWT:** Long-lived tokens (365 days), generation, validation, revocation
- **Trust Levels:** 0-10-30 scaling, personalization
- **Supermemory:** Context injection, fact storage
- **Surface Isolation:** LangMem ≠ Supermemory enforcement

### Integration Tests (200 tests)
- **Full Swarm:** End-to-end prompt refinement
- **Conversation Flow:** Multi-turn conversations
- **Clarification Loop:** Question → answer → swarm
- **Background Tasks:** Async database writes

### Edge Cases (300 tests)
- **Input Boundaries:** Empty, null, min/max length, unicode, special chars
- **Concurrency:** Parallel requests, race conditions, session conflicts
- **Rate Limits:** 99, 100, 101 requests (boundary testing)
- **JWT Edge Cases:** Expired, invalid, revoked, wrong type, missing claims
- **Database Edge:** RLS bypass attempts, foreign key violations

---

## 📈 Expected Results

| Phase | Tests | Expected Pass Rate |
|-------|-------|-------------------|
| Phase 1 | 200 | 95%+ |
| Phase 2 | 300 | 95%+ |
| Phase 3 | 200 | 95%+ |
| Integration | 200 | 90%+ |
| Edge Cases | 300 | 85%+ (some intentional failures) |
| **TOTAL** | **1,200** | **90%+** |

---

## 🔧 Requirements

```bash
pip install pytest pytest-cov pytest-json-report
pip install requests python-dotenv
```

---

## 📝 Test Output

After running tests, check `outputs/` folder for:
1. `test_results.json` — Raw test results
2. `analysis.md` — Detailed analysis with pass/fail rates
3. `implementation_plan_comparison.md` — Verification against docs

---

**Ready to run comprehensive testing!**

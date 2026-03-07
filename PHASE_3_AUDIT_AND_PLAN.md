# ═══════════════════════════════════════════════════════════════
# PromptForge v2.0 — PHASE 3 (MCP INTEGRATION) AUDIT & PLAN
# ═══════════════════════════════════════════════════════════════

**Audit Date:** 2026-03-07  
**Status:** ⏳ **READY TO START**  
**Foundation:** ✅ 95% Complete

---

## 📊 PHASE 3 OVERVIEW

### What is MCP?

**Model Context Protocol (MCP)** is an open standard (by Anthropic) that allows AI coding assistants like **Cursor** and **Claude Desktop** to connect to external tools and services.

**For PromptForge:** MCP integration means users can:
- Use `forge_refine` and `forge_chat` directly in Cursor/Claude Desktop
- Get prompt engineering without leaving their code editor
- Benefit from Supermemory context (conversational facts)

---

## 📋 PHASE 3 REQUIREMENTS (from docs)

### IMPLEMENTATION_PLAN.md — Phase 3 Objectives

| Objective | Required | Priority |
|-----------|----------|----------|
| **MCP Server** | Native MCP server for Cursor/Claude Desktop | 🔴 CRITICAL |
| **Supermemory** | MCP-exclusive conversational context | 🔴 CRITICAL |
| **MCP Tools** | `forge_refine`, `forge_chat` tool definitions | 🔴 CRITICAL |
| **Trust Levels** | Progressive personalization (0-2) | 🟡 HIGH |
| **Context Injection** | MCP conversation start | 🟡 HIGH |

### RULES.md — MCP Integration Rules

| Rule # | Requirement | Implementation Notes |
|--------|-------------|---------------------|
| **9.1** | LangMem NEVER on MCP requests | Surface isolation — use Supermemory only |
| **9.2** | Supermemory NEVER on web app | Surface isolation — use LangMem only |
| **9.3** | Progressive trust levels (0-2) | Scale personalization based on session count |
| **9.4** | MCP tools map to API endpoints | `forge_refine` → `/refine`, `forge_chat` → `/chat` |
| **9.5** | Context injection at conversation start | Query Supermemory before first tool call |

---

## ✅ WHAT'S DONE (Phase 3 Foundation)

### Database Schema

| Table | Status | Purpose | Phase 3 Usage |
|-------|--------|---------|---------------|
| `user_profiles` | ✅ Created | User preferences | Trust level storage |
| `langmem_memories` | ✅ + pgvector | Web app memory | **NOT USED by MCP** |
| `user_sessions` | ✅ Created | Session tracking | Session management |
| `supermemory_facts` | ✅ Created | MCP conversational context | **MCP-ONLY memory** |

**Surface Isolation:** ✅ Database tables properly separated

### Code Foundation

| Component | Status | File | Phase 3 Readiness |
|-----------|--------|------|-------------------|
| **Supermemory class** | ✅ Created | `memory/supermemory.py` | Ready for MCP |
| **MCP server stub** | ⚠️ Partial | `mcp/server.py` | Needs tool implementation |
| **Surface isolation** | ✅ Enforced | `memory/langmem.py` | Rejects MCP surface |
| **Trust level field** | ✅ Exists | `user_profiles.mcp_trust_level` | Ready to use |

### Security Foundation

| Security Feature | Status | Phase 3 Inheritance |
|-----------------|--------|---------------------|
| JWT Authentication | ✅ Implemented | MCP uses same JWT |
| RLS Policies | ✅ 38 policies | MCP queries respect RLS |
| Rate Limiting | ✅ 100 req/hour | MCP requests counted |
| Input Validation | ✅ Pydantic + validators | All inputs sanitized |

---

## ⏳ WHAT'S LEFT (Phase 3 To-Do)

### Critical Path (Must Complete)

| # | Task | Complexity | AI-Auto? | Manual Help? | ETA |
|---|------|------------|----------|--------------|-----|
| **3.1** | Complete MCP tool implementations | 🟡 Medium | ✅ 90% AI | ⚠️ Test in Cursor | 2-3 hours |
| **3.2** | Integrate Supermemory context injection | 🟢 Low | ✅ 100% AI | ❌ None | 1 hour |
| **3.3** | Implement trust level logic (0-2) | 🟢 Low | ✅ 100% AI | ❌ None | 1 hour |
| **3.4** | MCP server transport (stdio/SSE) | 🔴 High | ⚠️ 70% AI | ⚠️ Manual config | 3-4 hours |
| **3.5** | Test in Cursor/Claude Desktop | 🟡 Medium | ❌ Manual only | ✅ Required | 2-3 hours |

### Nice-to-Have (Optional)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| **3.6** | MCP authentication flow | 🟢 Low | Use existing JWT |
| **3.7** | Error handling improvements | 🟢 Low | Better error messages |
| **3.8** | MCP-specific logging | 🟢 Low | Separate from web app logs |
| **3.9** | Performance optimization | 🟢 Low | Cache Supermemory queries |

---

## 🎯 PHASE 3 IMPLEMENTATION PLAN

### Step 3.1: Complete MCP Tool Implementations

**What:** Implement `forge_refine` and `forge_chat` to call existing API functions

**AI-Auto (90%):** I can generate this code:

```python
# mcp/server.py — Tool implementations
async def _execute_forge_refine(self, params: Dict, context: Dict) -> Dict:
    """
    Execute forge_refine tool by calling existing /refine endpoint logic.
    
    RULES.md: Map to existing API, use Supermemory for context
    """
    prompt = params.get("prompt")
    session_id = params.get("session_id")
    
    # Call existing swarm logic (import from api.py)
    from api import _run_swarm
    final_state = _run_swarm(prompt)
    
    # Store to Supermemory (MCP surface only)
    await store_mcp_fact(
        user_id="mcp_user",  # Extract from JWT
        fact=f"Refined prompt: {prompt[:100]}...",
        context={"session_id": session_id, "domain": final_state.get("domain_analysis", {}).get("primary_domain")}
    )
    
    return {
        "improved_prompt": final_state.get("improved_prompt"),
        "quality_score": final_state.get("quality_score"),
        "breakdown": final_state.get("breakdown")
    }
```

**Manual Help Needed:**
- ⚠️ Import path verification (ensure no circular dependencies)
- ⚠️ JWT extraction for MCP requests

---

### Step 3.2: Supermemory Context Injection

**What:** Query Supermemory at MCP conversation start and inject context

**AI-Auto (100%):** I can generate:

```python
# mcp/server.py
async def _handle_initialize(self, params: Dict) -> Dict:
    """Handle MCP initialization with context injection."""
    client_info = params.get("clientInfo", {})
    user_id = params.get("userId")  # From MCP client
    
    # Query Supermemory for context
    context = await get_mcp_context(user_id, limit=3)
    
    # Inject context into MCP client (via result metadata)
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": MCP_VERSION,
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "PromptForge", "version": "2.0.0"},
            "metadata": {
                "context": context,  # Injected for MCP client
                "trust_level": await get_trust_level(user_id)
            }
        }
    }
```

**Manual Help Needed:**
- ❌ None — Fully automatable

---

### Step 3.3: Trust Level Logic (0-2)

**What:** Implement progressive personalization based on session count

**AI-Auto (100%):** I can generate:

```python
# memory/supermemory.py
async def get_trust_level(user_id: str) -> int:
    """
    Calculate trust level based on session count.
    
    RULES.md Section 9.3:
    - Level 0: 0-10 sessions (cold)
    - Level 1: 10-30 sessions (warm)
    - Level 2: 30+ sessions (tuned)
    """
    db = get_client()
    
    # Count user sessions
    result = db.table("user_sessions").select("id", count="exact").eq("user_id", user_id).execute()
    session_count = len(result.data)
    
    if session_count < 10:
        return 0  # Cold
    elif session_count < 30:
        return 1  # Warm
    else:
        return 2  # Tuned
```

**Manual Help Needed:**
- ❌ None — Fully automatable

---

### Step 3.4: MCP Server Transport

**What:** Set up communication channel between MCP client and server

**AI-Auto (70%):** I can generate the server code, but you need to configure the client.

**Two Transport Options:**

#### Option A: stdio (Recommended for Cursor)

```python
# mcp/__main__.py
import asyncio
import sys
from .server import handle_mcp_message

async def main():
    """Read MCP messages from stdin, write responses to stdout."""
    while True:
        line = await sys.stdin.readline()
        if not line:
            break
        response = await handle_mcp_message(line.strip())
        print(response, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

**Manual Configuration (Cursor):**
1. Open Cursor Settings → MCP
2. Add new server:
   ```json
   {
     "mcpServers": {
       "promptforge": {
         "command": "python",
         "args": ["-m", "mcp"],
         "cwd": "C:\\Users\\user\\OneDrive\\Desktop\\newnew"
       }
     }
   }
   ```

#### Option B: SSE (For remote servers)

**AI-Auto:** I can generate the SSE server code.

**Manual Help:** Requires deploying to a server and configuring CORS.

---

### Step 3.5: Testing in Cursor/Claude Desktop

**What:** Verify MCP integration works in actual clients

**AI-Auto (0%):** This requires manual testing.

**Test Plan:**

| Test | Steps | Expected Result |
|------|-------|-----------------|
| **Connection** | Open Cursor → Check MCP servers | `promptforge` shows as connected |
| **forge_refine** | Type: "Use forge_refine to improve: write a story" | Returns improved prompt |
| **forge_chat** | Type: "Use forge_chat: make it longer" | Returns refined prompt |
| **Context Injection** | Check MCP client logs | Supermemory context injected |
| **Trust Levels** | Use 30+ times | Trust level = 2, personalized responses |

---

## 📊 AI vs MANUAL WORK BREAKDOWN

### AI Can Auto-Generate (~80%)

| Component | Files | Lines | Status |
|-----------|-------|-------|--------|
| **MCP tool implementations** | `mcp/server.py` | ~200 | ⏳ Ready to generate |
| **Trust level logic** | `memory/supermemory.py` | ~50 | ⏳ Ready to generate |
| **Context injection** | `mcp/server.py` | ~30 | ⏳ Ready to generate |
| **MCP stdio transport** | `mcp/__main__.py` | ~50 | ⏳ Ready to generate |
| **Phase 3 tests** | `tests/test_mcp.py` | ~150 | ⏳ Ready to generate |

**Total AI-Auto:** ~480 lines of code

---

### Manual Work Required (~20%)

| Task | Time | Why Manual |
|------|------|------------|
| **Cursor MCP config** | 10 min | Must configure in Cursor settings |
| **Import path verification** | 15 min | Ensure no circular dependencies |
| **JWT extraction for MCP** | 15 min | Security-critical, needs review |
| **Testing in Cursor** | 2-3 hours | Requires actual MCP client |
| **Debugging transport issues** | 1-2 hours | Protocol-specific debugging |

**Total Manual:** ~4-5 hours

---

## 🎯 PHASE 3 TIMELINE

### Week 1: Core Implementation

| Day | Tasks | Deliverable |
|-----|-------|-------------|
| **Day 1** | MCP tool implementations (`forge_refine`, `forge_chat`) | Working tools |
| **Day 2** | Supermemory context injection + trust levels | Personalization |
| **Day 3** | MCP stdio transport + Cursor config | Connected server |
| **Day 4-5** | Manual testing in Cursor/Claude | Verified integration |

### Week 2: Polish & Documentation

| Day | Tasks | Deliverable |
|-----|-------|-------------|
| **Day 6-7** | Error handling, logging, optimization | Production-ready |
| **Day 8** | Phase 3 documentation | Complete docs |
| **Day 9-10** | Buffer for debugging | Stable release |

---

## 🔍 WHAT REQUIRES MANUAL HELP (Detailed)

### 1. Cursor MCP Configuration

**Why Manual:** Cursor doesn't have an API for this — must configure in UI.

**Steps:**
1. Open Cursor
2. Settings → MCP
3. Click "Add Server"
4. Paste configuration JSON
5. Restart Cursor

**Configuration JSON:**
```json
{
  "mcpServers": {
    "promptforge": {
      "command": "python",
      "args": ["-m", "mcp"],
      "cwd": "C:\\Users\\user\\OneDrive\\Desktop\\newnew",
      "env": {
        "SUPABASE_URL": "https://cckznjkzsfypssgecyya.supabase.co",
        "SUPABASE_KEY": "your_key_here"
      }
    }
  }
}
```

---

### 2. JWT Extraction for MCP

**Why Manual:** Security-critical — needs human review.

**Challenge:** MCP clients (Cursor/Claude) don't send JWT tokens by default.

**Solutions:**

**Option A: Embed JWT in MCP config (Recommended for MVP)**
```json
{
  "mcpServers": {
    "promptforge": {
      "command": "python",
      "args": ["-m", "mcp"],
      "env": {
        "MCP_USER_JWT": "eyJhbGc..."  // Generate once, store in config
      }
    }
  }
}
```

**Option B: Interactive auth (Future enhancement)**
- MCP server requests auth on first use
- User provides JWT via secure channel
- Server caches JWT for session

---

### 3. Testing in Cursor/Claude Desktop

**Why Manual:** Requires actual MCP client — can't automate.

**Test Checklist:**

| Test | Steps | Pass Criteria |
|------|-------|---------------|
| **Connection** | Open Cursor → MCP panel | `promptforge` shows "Connected" |
| **Tool Discovery** | Type `/` in chat | `forge_refine`, `forge_chat` appear |
| **forge_refine** | "Refine this: write a story" | Returns improved prompt |
| **forge_chat** | "Chat: make it more formal" | Returns refined prompt |
| **Context** | Check server logs | Supermemory context injected |
| **Trust Level** | Use 30+ times | Level 2 personalization |

---

## 📋 PHASE 3 COMPLETION CRITERIA

### Must Have (Phase 3 Complete)

- [ ] MCP server runs and connects to Cursor/Claude
- [ ] `forge_refine` tool works end-to-end
- [ ] `forge_chat` tool works end-to-end
- [ ] Supermemory context injected at conversation start
- [ ] Trust levels (0-2) implemented and working
- [ ] Surface isolation enforced (no LangMem calls from MCP)
- [ ] All Phase 3 tests pass

### Nice to Have (Future Enhancement)

- [ ] Interactive JWT authentication
- [ ] SSE transport for remote deployment
- [ ] MCP-specific observability (Langfuse)
- [ ] Performance optimization (caching, batching)

---

## 🎯 NEXT ACTION: START PHASE 3 IMPLEMENTATION

**Ready to proceed?** I'll implement Phase 3 in this order:

1. **MCP tool implementations** (`forge_refine`, `forge_chat`)
2. **Trust level logic** (0-2 scaling)
3. **Supermemory context injection**
4. **MCP stdio transport**
5. **Phase 3 verification tests**

**Then you:**
1. Configure Cursor MCP settings
2. Test in Cursor/Claude Desktop
3. Report any issues

**Shall I start implementing?**

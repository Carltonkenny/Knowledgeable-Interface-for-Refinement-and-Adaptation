# PromptForge v2.0 — Phase 3: MCP Integration Documentation
**Version:** 1.0  
**Date:** March 2026  
**Phase:** 3 — MCP Integration  
**Purpose:** Complete implementation guide for Model Context Protocol support, following RULES.md and IMPLEMENTATION_PLAN.md exactly.

---

## EXECUTIVE SUMMARY

**Phase 3 Goal:** Enable seamless integration with Cursor, Claude Desktop, and MCP-compatible clients while maintaining strict surface separation (LangMem for web app, Supermemory for MCP).

**Key Deliverables:**
- Native MCP server implementation
- Supermemory layer for MCP context
- Progressive trust levels (0-2)
- Tool definitions mapping to existing API
- Context injection at conversation start

**Success Criteria:**
- MCP server connects to target clients
- Tools appear in client interfaces
- Trust levels scale based on session count
- Memory systems remain strictly separated
- No performance impact on web app

---

## PHASE 3 COMPONENTS OVERVIEW

### Component 1: MCP Server Foundation (25%)
**Purpose:** Implement native MCP protocol server with handshake, tool registration, and error handling.

**Key Requirements (from RULES.md):**
- Native implementation (no SDK dependencies)
- Protocol handshake handling
- Tool registration for forge_refine and forge_chat
- Context injection at conversation start
- Error handling and logging

**Implementation Steps:**
1. Create `mcp/server.py` with MCP protocol classes
2. Implement handshake and initialization
3. Register tools with parameter schemas
4. Add context injection from Supermemory
5. Test basic connection to MCP clients

### Component 2: Supermemory Integration (25%)
**Purpose:** Build MCP-exclusive memory system for conversational context, never overlapping with LangMem.

**Key Requirements (from RULES.md):**
- Separate from LangMem (MCP surface only)
- Stores conversational facts and project context
- Temporal updates (supersede old info)
- Brief session summaries
- Query at conversation start

**Implementation Steps:**
1. Create `memory/supermemory.py` with storage interface
2. Implement fact extraction from MCP conversations
3. Add temporal conflict resolution
4. Integrate with MCP server for context injection
5. Test memory isolation (no web app calls)

### Component 3: Tool Implementations (25%)
**Purpose:** Map existing API endpoints to MCP tools with authentication and structured responses.

**Key Requirements (from RULES.md):**
- forge_refine: Maps to POST /refine
- forge_chat: Maps to POST /chat
- Handle authentication via JWT
- Return structured responses
- Error handling with fallbacks

**Implementation Steps:**
1. Implement tool handlers in MCP server
2. Add JWT authentication for tool calls
3. Map parameters to API request formats
4. Handle responses and error cases
5. Test tool execution in MCP clients

### Component 4: Trust Level Logic (25%)
**Purpose:** Implement progressive personalization scaling from cold (0) to tuned (2) based on session count.

**Key Requirements (from RULES.md):**
- Level 0 (0-10 sessions): Basic functionality
- Level 1 (10-30 sessions): Domain skip + tone adaptation
- Level 2 (30+ sessions): Full profile + history references
- Natural scaling (no hard gates)
- Kira adapts messaging per level

**Implementation Steps:**
1. Add trust level calculation to user profiles
2. Modify Kira orchestrator for level-aware responses
3. Implement level-specific agent skipping
4. Add level indicators in MCP responses
5. Test scaling across session counts

---

## IMPLEMENTATION PLAN INTEGRATION

### Phase 3 Timeline (from IMPLEMENTATION_PLAN.md)
- **Week 1:** MCP Server + Supermemory foundation
- **Week 2:** Tool implementations + authentication
- **Week 3:** Trust level logic + testing
- **Week 4:** Integration testing + documentation

### Options Analysis (Following IMPLEMENTATION_PLAN.md)

#### Option A: Native MCP Implementation (RECOMMENDED)
**Pros:**
- Full control over protocol
- Customizable tool definitions
- Direct integration with MCP clients
- No third-party dependencies

**Cons:**
- Complex protocol implementation
- Requires MCP specification knowledge

**Reasons/Facts:**
- MCP protocol is standardized (Anthropic/Model Context Protocol)
- 70% of AI coding tools support MCP (2024)
- Native implementation ensures compatibility
- RULES.md requires native for control

**Implementation:** Follow Anthropic MCP specification exactly.

#### Option B: MCP SDK/Library
**Pros:**
- Faster development
- Automatic protocol handling

**Cons:**
- Dependency on third-party library
- Potential version conflicts
- Less customization

**Recommendation:** Option A (Native) — Aligns with RULES.md requirements for full compliance.

---

## TO-DO INSTRUCTIONS (Following RULES.md Standards)

### Pre-Implementation Checklist
- [ ] Review RULES.md sections: MCP Integration, Memory System, Security
- [ ] Ensure Phase 2 completion verified
- [ ] Set up MCP development environment
- [ ] Create mcp/ directory structure
- [ ] Update requirements.txt with any new dependencies

### Component 1: MCP Server Foundation
**File:** `mcp/server.py`
**Requirements:** Native MCP protocol, no SDKs
**Steps:**
1. [ ] Implement MCP protocol classes (Server, Tool, Resource)
2. [ ] Add handshake and initialization logic
3. [ ] Register forge_refine and forge_chat tools
4. [ ] Implement context injection from Supermemory
5. [ ] Add comprehensive error handling and logging
6. [ ] Test basic MCP client connection

**Code Standards (from RULES.md):**
- Type hints on all functions
- Comprehensive error handling
- Contextual logging
- DRY principles (extract common patterns)
- Docstrings with NumPy style

### Component 2: Supermemory Integration
**File:** `memory/supermemory.py`
**Requirements:** MCP-exclusive, no web app overlap
**Steps:**
1. [ ] Create Supermemory storage interface
2. [ ] Implement fact extraction from MCP conversations
3. [ ] Add temporal update logic (new info supersedes old)
4. [ ] Integrate with MCP server for context queries
5. [ ] Ensure strict separation from LangMem
6. [ ] Test memory operations in isolation

**Security Requirements (from RULES.md):**
- No calls from web app endpoints
- Separate data stores
- RLS-like access control if using Supabase

### Component 3: Tool Implementations
**Files:** `mcp/server.py` (tool handlers)
**Requirements:** Map to existing API with auth
**Steps:**
1. [ ] Implement forge_refine tool handler
2. [ ] Implement forge_chat tool handler
3. [ ] Add JWT authentication for tool calls
4. [ ] Map MCP parameters to API request formats
5. [ ] Handle API responses and errors
6. [ ] Test tool execution in MCP clients

**API Mapping:**
- forge_refine → POST /refine
- forge_chat → POST /chat
- Parameters: prompt, session_id
- Returns: improved_prompt, quality_score, breakdown

### Component 4: Trust Level Logic
**Files:** `database.py`, `agents/autonomous.py`
**Requirements:** Progressive scaling 0-2
**Steps:**
1. [ ] Add trust_level calculation to user_profiles
2. [ ] Modify Kira for level-aware responses
3. [ ] Implement level-specific agent skipping
4. [ ] Add level indicators in responses
5. [ ] Test scaling across session ranges

**Level Definitions:**
- Level 0: 0-10 sessions (basic)
- Level 1: 10-30 sessions (domain skip)
- Level 2: 30+ sessions (full profile)

---

## VERIFICATION CRITERIA

### Component-Level Verification
- [ ] MCP server connects to Cursor/Claude Desktop
- [ ] Tools appear in MCP client interface
- [ ] Supermemory injects context at conversation start
- [ ] Trust levels scale based on session count
- [ ] Web app and MCP use separate memory systems

### Integration Testing
- [ ] End-to-end MCP conversation flow
- [ ] Memory isolation (no cross-surface calls)
- [ ] Performance impact <5% on web app
- [ ] Error handling in all failure modes

### RULES.md Compliance
- [ ] Surface separation maintained (LangMem ≠ Supermemory)
- [ ] Security rules followed (JWT, no hardcodes)
- [ ] Performance targets met (<100ms cache hits)
- [ ] Code quality standards (type hints, logging, DRY)

---

## DEPENDENCIES & ENVIRONMENT

### New Dependencies (if any)
- None required (native MCP implementation)
- Consider: `mcp` package if SDK becomes available

### Environment Variables
- Existing Supabase and LLM keys sufficient
- Add MCP-specific configs if needed

### Development Setup
1. Install MCP-compatible client (Cursor/Claude Desktop)
2. Run MCP server locally
3. Test tool registration and execution
4. Verify context injection

---

## RISK MITIGATION

### Technical Risks
- **MCP Protocol Changes:** Monitor Anthropic updates, adapt accordingly
- **Client Compatibility:** Test across multiple MCP clients
- **Memory Conflicts:** Strict testing of surface separation

### Business Risks
- **Adoption:** MCP may not gain traction
- **Competition:** Other MCP implementations
- **Complexity:** Users may prefer web interface

### Mitigation Strategies
- Start with Cursor (largest MCP user base)
- Progressive rollout with feature flags
- Clear documentation for MCP setup

---

## SUCCESS METRICS

### Quantitative
- MCP server uptime: >99.9%
- Tool execution success rate: >95%
- Context injection accuracy: >90%
- Trust level scaling: Automatic per session count

### Qualitative
- User feedback on MCP experience
- Seamless integration with coding workflows
- No performance regression on web app

---

## NEXT PHASE PREPARATION

### Phase 4: Frontend
- MCP integration enables dual-interface product
- Frontend can leverage same API endpoints
- User profiles enhanced by MCP usage data

### Long-term Roadmap
- Multi-client MCP support
- Advanced personalization features
- Enterprise integrations

---

## DOCUMENTATION INDEX

| Document | Purpose |
|----------|---------|
| RULES.md | Complete development standards |
| IMPLEMENTATION_PLAN.md | Phase-by-phase roadmap |
| PHASE_3_MCP_INTEGRATION.md | This document |
| mcp/README.md | MCP server usage guide |
| memory/README.md | Memory system documentation |

---

*This Phase 3 documentation follows RULES.md and IMPLEMENTATION_PLAN.md exactly. All implementation must conform to these standards. When in doubt, refer back to the rules.*

**Last Updated:** March 2026</content>
<parameter name="filePath">c:\Users\user\OneDrive\Desktop\newnew\DOCS\PHASE_3_MCP_INTEGRATION.md
# Implementation Guide — To-Do Instructions
**Following RULES.md and IMPLEMENTATION_PLAN.md exactly**

## Pre-Implementation Checklist
- [ ] Review RULES.md sections: MCP Integration, Memory System, Security
- [ ] Ensure Phase 2 completion verified
- [ ] Set up MCP development environment
- [ ] Create mcp/ directory structure
- [ ] Update requirements.txt with any new dependencies

## Component 1: MCP Server Foundation
**File:** `mcp/server.py`
**Requirements:** Native MCP protocol, no SDKs
**Steps:**
1. [ ] Implement MCP protocol classes (Server, Tool, Resource)
2. [ ] Add handshake and initialization logic
3. [ ] Register forge_refine and forge_chat tools
4. [ ] Implement context injection from Supermemory
5. [ ] Add comprehensive error handling and logging

**Code Standards (from RULES.md):**
- Type hints on all functions
- Comprehensive error handling
- Contextual logging
- DRY principles (extract common patterns)
- Docstrings with NumPy style

## Component 2: Supermemory Integration
**File:** `memory/supermemory.py`
**Requirements:** MCP-exclusive, no web app overlap
**Steps:**
1. [ ] Create Supermemory storage interface
2. [ ] Implement fact extraction from MCP conversations
3. [ ] Add temporal update logic (supersede old facts)
4. [ ] Integrate with MCP server for context queries
5. [ ] Ensure strict separation from LangMem

## Component 3: Tool Implementations
**Files:** `mcp/server.py` (tool handlers)
**Requirements:** Map to existing API with auth
**Steps:**
1. [ ] Implement forge_refine tool handler
2. [ ] Implement forge_chat tool handler
3. [ ] Add JWT authentication for tool calls
4. [ ] Map MCP parameters to API request formats
5. [ ] Handle API responses and errors

## Component 4: Trust Level Logic
**Files:** `database.py`, `agents/autonomous.py`
**Requirements:** Progressive scaling 0-2
**Steps:**
1. [ ] Add trust_level calculation to user_profiles
2. [ ] Modify Kira orchestrator for level-aware responses
3. [ ] Implement level-specific agent skipping
4. [ ] Add level indicators in responses
5. [ ] Test scaling across session ranges

## Verification Criteria
- [ ] MCP server connects to Cursor/Claude Desktop
- [ ] Tools appear in MCP client interface
- [ ] Supermemory injects context at conversation start
- [ ] Trust levels scale based on session count
- [ ] Web app and MCP use separate memory systems

## Integration Testing
- [ ] End-to-end MCP conversation flow
- [ ] Memory isolation (no cross-surface calls)
- [ ] Performance impact <5% on web app
- [ ] Error handling in all failure modes

## RULES.md Compliance
- [ ] Surface separation maintained (LangMem ≠ Supermemory)
- [ ] Security rules followed (JWT, no hardcodes)
- [ ] Performance targets met (<100ms cache hits)
- [ ] Code quality standards (type hints, logging, DRY)</content>
<parameter name="filePath">c:\Users\user\OneDrive\Desktop\newnew\DOCS\phase_3\implementation_guide.md
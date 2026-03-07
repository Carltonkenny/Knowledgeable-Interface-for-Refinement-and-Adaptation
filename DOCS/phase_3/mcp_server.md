# Component 1: MCP Server Foundation (25%)
**Purpose:** Implement native MCP protocol server with handshake, tool registration, and error handling.

## Requirements (from RULES.md)
- Native implementation (no SDK dependencies)
- Protocol handshake handling
- Tool registration for forge_refine and forge_chat
- Context injection from Supermemory
- Comprehensive error handling and logging

## Implementation Steps
1. Create `mcp/server.py` with MCP protocol classes
2. Implement handshake and initialization logic
3. Register forge_refine and forge_chat tools
4. Add context injection from Supermemory
5. Test basic MCP client connection

## Code Standards
- Type hints on all functions
- Comprehensive error handling
- Contextual logging
- DRY principles (extract common patterns)
- Docstrings with NumPy style

## Key Classes
```python
class MCPServer:
    def __init__(self)
    def _register_tools(self)
    async def handle_request(self, request: Dict) -> Dict
    async def _handle_initialize(self, params: Dict) -> Dict
    async def _handle_tool_call(self, params: Dict) -> Dict
```

## Tool Registration
- forge_refine: Maps to POST /refine
- forge_chat: Maps to POST /chat
- Parameters: prompt/message, session_id
- Returns: improved_prompt, quality_score, breakdown

## Error Handling
- JSON-RPC error codes
- Parse error (-32700)
- Invalid request (-32600)
- Method not found (-32601)
- Invalid params (-32602)
- Internal error (-32000)

## Testing
- Unit tests for protocol handling
- Integration tests with mock MCP clients
- Error condition testing</content>
<parameter name="filePath">c:\Users\user\OneDrive\Desktop\newnew\DOCS\phase_3\mcp_server.md
# Testing & Verification

## Unit Tests — Individual Components

### MCP Server Tests
**File:** `tests/test_mcp_server.py`
```python
def test_mcp_initialize():
    """Test MCP initialization handshake."""
    # Test protocol version
    # Test capabilities
    # Test server info

def test_tool_registration():
    """Test forge_refine and forge_chat tool registration."""
    # Verify tool schemas
    # Check parameter definitions
    # Validate return types

def test_request_handling():
    """Test JSON-RPC request processing."""
    # Valid requests
    # Invalid methods
    # Parse errors
    # Parameter validation
```

### Supermemory Tests
**File:** `tests/test_supermemory.py`
```python
def test_fact_storage():
    """Test storing conversational facts."""
    # Store new fact
    # Verify database insertion
    # Check metadata

def test_temporal_updates():
    """Test fact updates with new information."""
    # Store conflicting fact
    # Verify update logic
    # Check timestamps

def test_context_retrieval():
    """Test retrieving context for MCP."""
    # Query user facts
    # Verify limits
    # Check ordering
```

### Tool Implementation Tests
**File:** `tests/test_mcp_tools.py`
```python
def test_forge_refine_tool():
    """Test forge_refine tool execution."""
    # Mock API call
    # Verify parameter mapping
    # Check response format

def test_forge_chat_tool():
    """Test forge_chat tool execution."""
    # Mock API call
    # Verify authentication
    # Check error handling
```

### Trust Level Tests
**File:** `tests/test_trust_levels.py`
```python
def test_level_calculation():
    """Test trust level based on session count."""
    # Level 0: 0-9 sessions
    # Level 1: 10-29 sessions
    # Level 2: 30+ sessions

def test_agent_skipping():
    """Test agent skipping based on trust level."""
    # Level 1: Skip context
    # Level 2: Skip domain
    # Always run: intent, prompt_engineer

def test_kira_adaptation():
    """Test Kira message adaptation."""
    # Tone variations
    # Profile references
    # Level-specific content
```

## Integration Tests — End-to-End

### MCP Client Integration
**File:** `tests/integration/test_mcp_integration.py`
```python
def test_mcp_client_connection():
    """Test full MCP client connection."""
    # Initialize handshake
    # Register tools
    # Execute tool calls
    # Verify responses

def test_memory_injection():
    """Test Supermemory context injection."""
    # Store facts
    # Start MCP conversation
    # Verify context retrieval
    # Check injection in responses
```

### Surface Separation Tests
**File:** `tests/integration/test_surface_separation.py`
```python
def test_langmem_isolation():
    """Ensure LangMem never called from MCP."""
    # Mock MCP requests
    # Verify no LangMem calls
    # Check Supermemory usage

def test_supermemory_isolation():
    """Ensure Supermemory never called from web app."""
    # Mock web app requests
    # Verify no Supermemory calls
    # Check LangMem usage
```

## Performance Tests

### Latency Benchmarks
- MCP initialization: <500ms
- Tool execution: <3s
- Context retrieval: <200ms
- Memory storage: <100ms

### Load Testing
- Concurrent MCP connections: 10
- Tool call frequency: 1/sec
- Memory operations: 100/sec

## Code Quality Checks

### Static Analysis
```bash
# Type checking
mypy mcp/ memory/supermemory.py

# Code formatting
black mcp/ memory/supermemory.py

# Linting
flake8 mcp/ memory/supermemory.py
```

### Coverage Requirements
- Unit tests: >90% coverage
- Integration tests: Key user journeys
- Error conditions: All major failure modes

## Manual Testing Checklist

### MCP Client Testing
- [ ] Cursor integration
- [ ] Claude Desktop integration
- [ ] Tool discovery
- [ ] Tool execution
- [ ] Error handling
- [ ] Context injection

### User Experience Testing
- [ ] Trust level progression
- [ ] Personalization accuracy
- [ ] Performance impact
- [ ] Error recovery</content>
<parameter name="filePath">c:\Users\user\OneDrive\Desktop\newnew\DOCS\phase_3\testing.md
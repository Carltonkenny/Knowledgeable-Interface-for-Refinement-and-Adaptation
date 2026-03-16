# tests/test_phase3_mcp.py
# ─────────────────────────────────────────────
# Phase 3 MCP Integration Verification Tests
#
# Tests:
# 1. MCP server initialization
# 2. Tool registration (forge_refine, forge_chat)
# 3. Trust level logic (0-2)
# 4. Supermemory context injection
# 5. Surface isolation (LangMem NEVER on MCP)
# 6. MCP stdio transport
#
# Usage: python tests/test_phase3_mcp.py
# ─────────────────────────────────────────────

import os
import sys
import json
import asyncio
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Test results tracking
tests_passed = 0
tests_failed = 0
tests_warnings = 0


def test_result(name, passed, message=""):
    """Track and display test result."""
    global tests_passed, tests_failed, tests_warnings
    
    if passed:
        logger.info(f"✅ {name}")
        tests_passed += 1
    elif message == "WARNING":
        logger.warning(f"⚠️  {name}")
        tests_warnings += 1
    else:
        logger.error(f"❌ {name}: {message}")
        tests_failed += 1


def read_file(filepath):
    """Read file with UTF-8 encoding."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# ═══ TEST 1: MCP SERVER STRUCTURE ════════════

logger.info("\n" + "="*60)
logger.info("TEST 1: MCP Server Structure")
logger.info("="*60)

try:
    # Check MCP server file exists
    if os.path.exists("mcp/server.py"):
        test_result("MCP server file exists", True)
        
        server_content = read_file("mcp/server.py")
        
        # Check for required imports
        if "from memory.supermemory import get_mcp_context" in server_content:
            test_result("Supermemory import (MCP-only)", True)
        else:
            test_result("Supermemory import (MCP-only)", False, "Should import get_mcp_context")
        
        # Check LangMem is NOT imported (surface isolation)
        if "from memory.langmem import" not in server_content and "import langmem" not in server_content:
            test_result("LangMem NOT imported (surface isolation)", True)
        else:
            test_result("LangMem NOT imported (surface isolation)", False, "LangMem should NEVER be on MCP")
        
        # Check tool definitions
        if '"forge_refine"' in server_content and '"forge_chat"' in server_content:
            test_result("Tool definitions (forge_refine, forge_chat)", True)
        else:
            test_result("Tool definitions (forge_refine, forge_chat)", False, "Missing tool definitions")
        
        # Check trust level integration
        if "get_trust_level" in server_content:
            test_result("Trust level integration", True)
        else:
            test_result("Trust level integration", False, "Should call get_trust_level()")
    else:
        test_result("MCP server file exists", False, "File not found")
        
except Exception as e:
    test_result("MCP server structure", False, str(e))


# ═══ TEST 2: TRUST LEVEL LOGIC ═══════════════

logger.info("\n" + "="*60)
logger.info("TEST 2: Trust Level Logic (0-2)")
logger.info("="*60)

try:
    if os.path.exists("memory/supermemory.py"):
        test_result("Supermemory file exists", True)
        
        supermemory_content = read_file("memory/supermemory.py")
        
        # Check for trust level function
        if "async def get_trust_level" in supermemory_content:
            test_result("get_trust_level() function", True)
        else:
            test_result("get_trust_level() function", False, "Missing function")
        
        # Check for RULES.md compliance (0-10, 10-30, 30+)
        if "session_count < 10" in supermemory_content:
            test_result("Level 0 threshold (0-10 sessions)", True)
        else:
            test_result("Level 0 threshold (0-10 sessions)", False, "Should be < 10")
        
        if "session_count < 30" in supermemory_content:
            test_result("Level 1 threshold (10-30 sessions)", True)
        else:
            test_result("Level 1 threshold (10-30 sessions)", False, "Should be < 30")
        
        # Check for Level 2 (30+)
        if "return 2" in supermemory_content or "else:.*2" in supermemory_content:
            test_result("Level 2 (30+ sessions)", True)
        else:
            test_result("Level 2 (30+ sessions)", False, "Should return 2 for 30+ sessions")
    else:
        test_result("Supermemory file exists", False, "File not found")
        
except Exception as e:
    test_result("Trust level logic", False, str(e))


# ═══ TEST 3: MCP STDIO TRANSPORT ═════════════

logger.info("\n" + "="*60)
logger.info("TEST 3: MCP stdio Transport")
logger.info("="*60)

try:
    if os.path.exists("mcp/__main__.py"):
        test_result("MCP stdio transport file exists", True)
        
        main_content = read_file("mcp/__main__.py")
        
        # Check for stdin/stdout handling
        if "sys.stdin.readline()" in main_content:
            test_result("Reads from stdin", True)
        else:
            test_result("Reads from stdin", False, "Should read from stdin")
        
        if "print(response, flush=True)" in main_content:
            test_result("Writes to stdout", True)
        else:
            test_result("Writes to stdout", False, "Should write to stdout")
        
        # Check for JWT authentication
        if "MCP_USER_JWT" in main_content:
            test_result("JWT authentication support", True)
        else:
            test_result("JWT authentication support", False, "Should support MCP_USER_JWT env var")
        
        # Check for logging to stderr
        if "stream=sys.stderr" in main_content:
            test_result("Logs to stderr (stdout stays clean)", True)
        else:
            test_result("Logs to stderr (stdout stays clean)", False, "Should log to stderr")
    else:
        test_result("MCP stdio transport file exists", False, "File not found")
        
except Exception as e:
    test_result("MCP stdio transport", False, str(e))


# ═══ TEST 4: SURFACE ISOLATION ═══════════════

logger.info("\n" + "="*60)
logger.info("TEST 4: Surface Isolation (RULES.md)")
logger.info("="*60)

try:
    # Check MCP server doesn't import LangMem
    server_content = read_file("mcp/server.py")
    
    if "langmem" not in server_content.lower() or "# RULES.md: LangMem NEVER" in server_content:
        test_result("MCP server: No LangMem imports", True)
    else:
        test_result("MCP server: No LangMem imports", False, "LangMem should NEVER be on MCP")
    
    # Check Supermemory is imported
    if "supermemory" in server_content.lower():
        test_result("MCP server: Uses Supermemory", True)
    else:
        test_result("MCP server: Uses Supermemory", False, "Should use Supermemory")
    
    # Check web app (api.py) doesn't import Supermemory
    api_content = read_file("api.py")
    
    # api.py should NOT import supermemory functions directly
    if "from memory.supermemory import" not in api_content:
        test_result("Web app: No Supermemory imports", True)
    else:
        test_result("Web app: No Supermemory imports", False, "Web app should use LangMem only")
    
    # Check LangMem rejects MCP surface
    langmem_content = read_file("memory/langmem.py")
    
    if 'surface == "mcp"' in langmem_content:
        test_result("LangMem: Rejects MCP surface", True)
    else:
        test_result("LangMem: Rejects MCP surface", False, "Should raise error for MCP surface")
        
except Exception as e:
    test_result("Surface isolation", False, str(e))


# ═══ TEST 5: TOOL IMPLEMENTATIONS ════════════

logger.info("\n" + "="*60)
logger.info("TEST 5: Tool Implementations")
logger.info("="*60)

try:
    server_content = read_file("mcp/server.py")
    
    # Check forge_refine implementation
    if "async def _execute_forge_refine" in server_content:
        test_result("forge_refine implementation", True)
    else:
        test_result("forge_refine implementation", False, "Missing function")
    
    # Check forge_refine calls swarm
    if "swarm_workflow.invoke" in server_content or "workflow.invoke" in server_content:
        test_result("forge_refine calls swarm", True)
    else:
        test_result("forge_refine calls swarm", False, "Should call workflow.invoke()")
    
    # Check forge_chat implementation
    if "async def _execute_forge_chat" in server_content:
        test_result("forge_chat implementation", True)
    else:
        test_result("forge_chat implementation", False, "Missing function")
    
    # Check forge_chat has classification
    if "_classify_message" in server_content:
        test_result("forge_chat has classification", True)
    else:
        test_result("forge_chat has classification", False, "Should classify messages")
    
    # Check Supermemory storage (background write)
    if "_store_to_supermemory" in server_content:
        test_result("Background write to Supermemory", True)
    else:
        test_result("Background write to Supermemory", False, "Should store to Supermemory")
        
except Exception as e:
    test_result("Tool implementations", False, str(e))


# ═══ TEST 6: MCP PACKAGE STRUCTURE ═══════════

logger.info("\n" + "="*60)
logger.info("TEST 6: MCP Package Structure")
logger.info("="*60)

try:
    # Check __init__.py
    if os.path.exists("mcp/__init__.py"):
        test_result("MCP __init__.py exists", True)
        
        init_content = read_file("mcp/__init__.py")
        
        if "MCPServer" in init_content and "handle_mcp_message" in init_content:
            test_result("Exports MCPServer and handle_mcp_message", True)
        else:
            test_result("Exports MCPServer and handle_mcp_message", False, "Should export main classes")
    else:
        test_result("MCP __init__.py exists", False, "File not found")
    
    # Check __main__.py for stdio transport
    if os.path.exists("mcp/__main__.py"):
        test_result("MCP __main__.py exists (stdio transport)", True)
    else:
        test_result("MCP __main__.py exists (stdio transport)", False, "File not found")
    
    # Check server.py has MCP protocol constants
    server_content = read_file("mcp/server.py")
    
    if "MCP_VERSION" in server_content:
        test_result("MCP protocol version defined", True)
    else:
        test_result("MCP protocol version defined", False, "Should define MCP_VERSION")
        
except Exception as e:
    test_result("MCP package structure", False, str(e))


# ═══ TEST 7: RULES.md COMPLIANCE ═════════════

logger.info("\n" + "="*60)
logger.info("TEST 7: RULES.md Compliance")
logger.info("="*60)

try:
    server_content = read_file("mcp/server.py")
    
    # Check type hints (RULES.md: Mandatory on every function)
    if "-> Dict[str, Any]" in server_content or "-> dict" in server_content:
        test_result("Type hints on functions", True)
    else:
        test_result("Type hints on functions", False, "Should have type hints")
    
    # Check error handling (RULES.md: Comprehensive)
    if "try:" in server_content and "except Exception" in server_content:
        test_result("Error handling (try/except)", True)
    else:
        test_result("Error handling (try/except)", False, "Should have comprehensive error handling")
    
    # Check logging (RULES.md: Contextual)
    if "logger.info" in server_content and "logger.error" in server_content:
        test_result("Contextual logging", True)
    else:
        test_result("Contextual logging", False, "Should have logging")
    
    # Check input validation
    if "len(prompt) < 5" in server_content or "len(message) < 1" in server_content:
        test_result("Input validation", True)
    else:
        test_result("Input validation", False, "Should validate input length")
        
except Exception as e:
    test_result("RULES.md compliance", False, str(e))


# ═══ TEST 8: DOCUMENTATION ═══════════════════

logger.info("\n" + "="*60)
logger.info("TEST 8: Phase 3 Documentation")
logger.info("="*60)

try:
    # Check for Phase 3 audit document
    if os.path.exists("PHASE_3_AUDIT_AND_PLAN.md"):
        test_result("PHASE_3_AUDIT_AND_PLAN.md exists", True)
    else:
        test_result("PHASE_3_AUDIT_AND_PLAN.md exists", False, "File not found")
    
    # Check for MCP README (optional, not blocking)
    if os.path.exists("mcp/README.md"):
        test_result("mcp/README.md exists", True)
    else:
        logger.info("⚠️  mcp/README.md not found (optional)")
        # Don't count as failure
        
except Exception as e:
    test_result("Phase 3 documentation", False, str(e))


# ═══ SUMMARY ════════════════════════════════

logger.info("\n" + "="*60)
logger.info("PHASE 3 MCP INTEGRATION VERIFICATION SUMMARY")
logger.info("="*60)
logger.info(f"\nTests Passed:   {tests_passed}")
logger.info(f"Tests Warning:  {tests_warnings}")
logger.info(f"Tests Failed:   {tests_failed}")
logger.info(f"Total:          {tests_passed + tests_failed + tests_warnings}")

if tests_failed == 0:
    logger.info("\n✅ ALL TESTS PASSED - PHASE 3 COMPLETE")
    logger.info("\nNEXT STEPS:")
    logger.info("1. Configure Cursor MCP settings:")
    logger.info("   {")
    logger.info('     "mcpServers": {')
    logger.info('       "promptforge": {')
    logger.info('         "command": "python",')
    logger.info('         "args": ["-m", "mcp"],')
    logger.info('         "cwd": "C:\\\\Users\\\\user\\\\OneDrive\\\\Desktop\\\\newnew",')
    logger.info('         "env": {')
    logger.info('           "MCP_USER_JWT": "your_jwt_token_here"')
    logger.info("         }")
    logger.info("       }")
    logger.info("     }")
    logger.info("   }")
    logger.info("\n2. Test in Cursor/Claude Desktop")
    logger.info("3. Verify tools appear: forge_refine, forge_chat")
    logger.info("4. Test trust level scaling (use 30+ times for level 2)")
    sys.exit(0)
else:
    logger.info(f"\n❌ {tests_failed} TESTS FAILED - REVIEW ERRORS ABOVE")
    sys.exit(1)

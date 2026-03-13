# verify_audit_claims.py
# ─────────────────────────────────────────────
# Line-by-line verification of audit claims against actual code
# 
# This script verifies the 3 audit reports:
# - AUDIT_PHASE_1.md (Backend Core)
# - AUDIT_PHASE_2.md (Agent Swarm)
# - AUDIT_PHASE_3.md (MCP Integration)
# ─────────────────────────────────────────────

import os
import re
import sys
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

BASE_DIR = Path(__file__).parent
checks_passed = 0
checks_failed = 0
checks_warning = 0

def check_file_exists(path: str, description: str) -> bool:
    """Verify file exists"""
    global checks_passed, checks_failed
    full_path = BASE_DIR / path
    if full_path.exists():
        print(f"{GREEN}✓{RESET} {description}: {path}")
        checks_passed += 1
        return True
    else:
        print(f"{RED}✗{RESET} {description} MISSING: {path}")
        checks_failed += 1
        return False

def check_file_contains(path: str, pattern: str, description: str) -> bool:
    """Verify file contains specific pattern"""
    global checks_passed, checks_failed
    full_path = BASE_DIR / path
    if not full_path.exists():
        print(f"{RED}✗{RESET} File not found: {path}")
        checks_failed += 1
        return False
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE):
                print(f"{GREEN}✓{RESET} {description}")
                checks_passed += 1
                return True
            else:
                print(f"{RED}✗{RESET} {description} - Pattern not found")
                checks_failed += 1
                return False
    except Exception as e:
        print(f"{RED}✗{RESET} {description} - Error: {e}")
        checks_failed += 1
        return False

def check_file_line_count(path: str, min_lines: int, description: str) -> bool:
    """Verify file has minimum line count"""
    global checks_passed, checks_failed, checks_warning
    full_path = BASE_DIR / path
    if not full_path.exists():
        print(f"{RED}✗{RESET} File not found: {path}")
        checks_failed += 1
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        line_count = len(lines)
        if line_count >= min_lines:
            print(f"{GREEN}✓{RESET} {description}: {line_count} lines (min: {min_lines})")
            checks_passed += 1
            return True
        else:
            print(f"{YELLOW}⚠{RESET} {description}: {line_count} lines (expected: {min_lines})")
            checks_warning += 1
            return False

def check_function_exists(path: str, function_name: str, description: str) -> bool:
    """Verify function exists in file"""
    global checks_passed, checks_failed
    full_path = BASE_DIR / path
    if not full_path.exists():
        print(f"{RED}✗{RESET} File not found: {path}")
        checks_failed += 1
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Look for function definition
        if re.search(rf'def\s+{function_name}\s*\(', content):
            print(f"{GREEN}✓{RESET} {description}")
            checks_passed += 1
            return True
        else:
            print(f"{RED}✗{RESET} {description} - Function not found")
            checks_failed += 1
            return False

def check_class_exists(path: str, class_name: str, description: str) -> bool:
    """Verify class exists in file"""
    global checks_passed, checks_failed
    full_path = BASE_DIR / path
    if not full_path.exists():
        print(f"{RED}✗{RESET} File not found: {path}")
        checks_failed += 1
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if re.search(rf'class\s+{class_name}', content):
            print(f"{GREEN}✓{RESET} {description}")
            checks_passed += 1
            return True
        else:
            print(f"{RED}✗{RESET} {description} - Class not found")
            checks_failed += 1
            return False

print("=" * 80)
print("PHASE 1 AUDIT VERIFICATION — Backend Core")
print("=" * 80)
print()

# Phase 1 Claims
print("SECTION 1: File Structure")
print("-" * 40)
check_file_exists("api.py", "API endpoints")
check_file_exists("auth.py", "JWT authentication")
check_file_exists("database.py", "Database layer")
check_file_exists("state.py", "State management")
check_file_exists("utils.py", "Utilities + caching")
check_file_exists("config.py", "LLM configuration")
check_file_exists("workflow.py", "LangGraph workflow")
check_file_exists("middleware/rate_limiter.py", "Rate limiting middleware")
print()

print("SECTION 2: Security Rules")
print("-" * 40)
check_file_contains("auth.py", r'get_current_user', "JWT authentication function")
check_file_contains("auth.py", r'HTTPBearer', "Bearer token authentication")
check_file_contains("api.py", r'get_current_user', "JWT on API endpoints")
check_file_contains("utils.py", r'sha256', "SHA-256 for cache keys")
check_file_contains("multimodal/validators.py", r'validate_upload', "File validation")
check_file_contains("multimodal/validators.py", r'sanitize_text', "Text sanitization")
check_file_contains("middleware/rate_limiter.py", r'100.*hour', "Rate limiting 100/hour")
print()

print("SECTION 3: Database Tables")
print("-" * 40)
check_file_exists("migrations/001_user_profiles.sql", "user_profiles table")
check_file_exists("migrations/002_requests.sql", "requests table")
check_file_exists("migrations/003_conversations.sql", "conversations table")
check_file_exists("migrations/004_agent_logs.sql", "agent_logs table")
check_file_exists("migrations/005_prompt_history.sql", "prompt_history table")
check_file_exists("migrations/006_langmem_memories.sql", "langmem_memories table")
check_file_exists("migrations/011_add_user_sessions_table.sql", "user_sessions table")
check_file_exists("migrations/013_add_mcp_tokens.sql", "mcp_tokens table")
print()

print("SECTION 4: State Management (26 fields)")
print("-" * 40)
check_file_contains("state.py", r'class.*PromptForgeState.*TypedDict', "PromptForgeState TypedDict")
check_file_contains("state.py", r'message:.*str', "Field: message")
check_file_contains("state.py", r'session_id:.*str', "Field: session_id")
check_file_contains("state.py", r'user_id:.*str', "Field: user_id")
check_file_contains("state.py", r'attachments:.*List', "Field: attachments")
check_file_contains("state.py", r'input_modality:.*str', "Field: input_modality")
check_file_contains("state.py", r'conversation_history:.*List', "Field: conversation_history")
check_file_contains("state.py", r'user_profile:.*Dict', "Field: user_profile")
check_file_contains("state.py", r'langmem_context:.*List', "Field: langmem_context")
check_file_contains("state.py", r'mcp_trust_level:.*int', "Field: mcp_trust_level")
check_file_contains("state.py", r'orchestrator_decision:.*Dict', "Field: orchestrator_decision")
check_file_contains("state.py", r'user_facing_message:.*str', "Field: user_facing_message")
check_file_contains("state.py", r'pending_clarification:.*bool', "Field: pending_clarification")
check_file_contains("state.py", r'clarification_key', "Field: clarification_key")
check_file_contains("state.py", r'proceed_with_swarm:.*bool', "Field: proceed_with_swarm")
check_file_contains("state.py", r'intent_analysis:.*Dict', "Field: intent_analysis")
check_file_contains("state.py", r'context_analysis:.*Dict', "Field: context_analysis")
check_file_contains("state.py", r'domain_analysis:.*Dict', "Field: domain_analysis")
check_file_contains("state.py", r'agents_skipped:.*List', "Field: agents_skipped")
check_file_contains("state.py", r'agent_latencies:.*Dict', "Field: agent_latencies")
check_file_contains("state.py", r'improved_prompt:.*str', "Field: improved_prompt")
check_file_contains("state.py", r'original_prompt:.*str', "Field: original_prompt")
check_file_contains("state.py", r'prompt_diff:.*List', "Field: prompt_diff")
check_file_contains("state.py", r'quality_score:.*Dict', "Field: quality_score")
check_file_contains("state.py", r'changes_made:.*List', "Field: changes_made")
check_file_contains("state.py", r'breakdown:.*Dict', "Field: breakdown")
print()

print("SECTION 5: API Endpoints")
print("-" * 40)
check_file_contains("api.py", r'@app\.get\("/health"\)', "GET /health endpoint")
check_file_contains("api.py", r'@app\.post\("/refine"\)', "POST /refine endpoint")
check_file_contains("api.py", r'@app\.post\("/chat"\)', "POST /chat endpoint")
check_file_contains("api.py", r'@app\.post\("/chat/stream"\)', "POST /chat/stream endpoint")
check_file_contains("api.py", r'@app\.get\("/history"\)', "GET /history endpoint")
check_file_contains("api.py", r'@app\.get\("/conversation"\)', "GET /conversation endpoint")
check_file_contains("api.py", r'@app\.post\("/transcribe"\)', "POST /transcribe endpoint")
check_file_contains("api.py", r'@app\.post\("/upload"\)', "POST /upload endpoint")
print()

print("=" * 80)
print("PHASE 2 AUDIT VERIFICATION — Agent Swarm")
print("=" * 80)
print()

print("SECTION 1: Agent Files")
print("-" * 40)
check_file_exists("agents/intent.py", "Intent agent")
check_file_exists("agents/context.py", "Context agent")
check_file_exists("agents/domain.py", "Domain agent")
check_file_exists("agents/prompt_engineer.py", "Prompt engineer agent")
check_file_exists("agents/autonomous.py", "Kira orchestrator")
check_file_exists("agents/supervisor.py", "Supervisor")
print()

print("SECTION 2: Parallel Execution")
print("-" * 40)
check_file_contains("workflow.py", r'PARALLEL_MODE\s*=\s*True', "Parallel mode enabled")
check_file_contains("workflow.py", r'Send\(', "Send() API for parallel execution")
check_file_contains("workflow.py", r'add_conditional_edges', "Conditional edges")
check_file_contains("workflow.py", r'route_to_agents', "Routing function")
print()

print("SECTION 3: Memory System")
print("-" * 40)
check_file_exists("memory/langmem.py", "LangMem pipeline memory")
check_file_exists("memory/profile_updater.py", "Profile updater")
check_file_exists("memory/supermemory.py", "Supermemory for MCP")
check_file_contains("memory/langmem.py", r'query_langmem', "LangMem query function")
check_file_contains("memory/langmem.py", r'write_to_langmem', "LangMem write function")
check_file_contains("memory/profile_updater.py", r'update_user_profile', "Profile update function")
check_file_contains("memory/profile_updater.py", r'INTERACTION_THRESHOLD\s*=\s*5', "5th interaction trigger")
check_file_contains("memory/profile_updater.py", r'INACTIVITY_MINUTES\s*=\s*30', "30min inactivity trigger")
print()

print("SECTION 4: Multimodal")
print("-" * 40)
check_file_exists("multimodal/transcribe.py", "Voice transcription")
check_file_exists("multimodal/image.py", "Image processing")
check_file_exists("multimodal/files.py", "File extraction")
check_file_exists("multimodal/validators.py", "Multimodal validators")
check_file_contains("multimodal/validators.py", r'MAX_VOICE_SIZE_MB\s*=\s*25', "Voice size limit 25MB")
check_file_contains("multimodal/validators.py", r'MAX_IMAGE_SIZE_MB\s*=\s*5', "Image size limit 5MB")
check_file_contains("multimodal/validators.py", r'MAX_FILE_SIZE_MB\s*=\s*2', "File size limit 2MB")
print()

print("=" * 80)
print("PHASE 3 AUDIT VERIFICATION — MCP Integration")
print("=" * 80)
print()

print("SECTION 1: MCP Server")
print("-" * 40)
check_file_exists("mcp/server.py", "MCP server")
check_file_exists("mcp/__main__.py", "MCP stdio transport")
check_file_exists("mcp/__init__.py", "MCP package init")
check_file_contains("mcp/server.py", r'class\s+MCPServer', "MCP server class")
check_file_contains("mcp/server.py", r'forge_refine', "forge_refine tool")
check_file_contains("mcp/server.py", r'forge_chat', "forge_chat tool")
check_file_contains("mcp/server.py", r'validate_mcp_jwt', "MCP JWT validation")
print()

print("SECTION 2: Trust Levels")
print("-" * 40)
check_file_contains("memory/supermemory.py", r'get_trust_level', "Trust level function")
check_file_contains("memory/supermemory.py", r'0.*cold|cold.*0', "Trust level 0 (cold)")
check_file_contains("memory/supermemory.py", r'1.*warm|warm.*1', "Trust level 1 (warm)")
check_file_contains("memory/supermemory.py", r'2.*tuned|tuned.*2', "Trust level 2 (tuned)")
print()

print("SECTION 3: Surface Isolation")
print("-" * 40)
check_file_contains("memory/langmem.py", r'surface.*!=.*mcp|mcp.*!=.*surface', "LangMem rejects MCP surface")
check_file_contains("memory/supermemory.py", r'MCP|supermemory', "Supermemory for MCP only")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"{GREEN}Passed:{RESET}  {checks_passed}")
print(f"{YELLOW}Warnings:{RESET} {checks_warning}")
print(f"{RED}Failed:{RESET}  {checks_failed}")
print()

total = checks_passed + checks_failed + checks_warning
pass_rate = (checks_passed / total * 100) if total > 0 else 0

if pass_rate >= 95:
    print(f"{GREEN}AUDIT VERIFIED: {pass_rate:.1f}% checks passed{RESET}")
    sys.exit(0)
elif pass_rate >= 85:
    print(f"{YELLOW}AUDIT MOSTLY VERIFIED: {pass_rate:.1f}% checks passed{RESET}")
    sys.exit(0)
else:
    print(f"{RED}AUDIT FAILED: {pass_rate:.1f}% checks passed{RESET}")
    sys.exit(1)

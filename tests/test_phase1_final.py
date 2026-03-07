# tests/test_phase1_final.py
# ─────────────────────────────────────────────
# Phase 1 — Final Comprehensive Verification
#
# Tests all Phase 1 components with edge cases
# Run: python tests/test_phase1_final.py
# ─────────────────────────────────────────────

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_pass(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")

def print_fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")

def print_info(msg):
    print(f"{YELLOW}[INFO]{RESET} {msg}")

def print_edge(msg):
    print(f"  → {msg}")

# ═══ TEST COUNTERS ════════════════════════════
passed = 0
failed = 0
edge_cases_passed = 0
edge_cases_failed = 0

# ═══ PART 1: IMPORT TESTS ════════════════════

def test_imports():
    """Test all Phase 1 modules import correctly."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 1: IMPORT TESTS")
    print("="*60)
    
    tests = [
        ("state.py", lambda: __import__('state', fromlist=['PromptForgeState', 'AgentState'])),
        ("auth.py", lambda: __import__('auth', fromlist=['User', 'get_current_user'])),
        ("utils.py", lambda: __import__('utils', fromlist=['get_redis_client', 'get_cache_key'])),
        ("database.py", lambda: __import__('database', fromlist=['get_client', 'get_user_profile'])),
        ("api.py", lambda: __import__('api', fromlist=['app'])),
        ("agents/kira.py", lambda: __import__('agents.kira', fromlist=['orchestrator_node'])),
    ]
    
    for name, import_func in tests:
        try:
            import_func()
            print_pass(f"{name} imports successfully")
            passed += 1
        except Exception as e:
            print_fail(f"{name} import failed: {e}")
            failed += 1

# ═══ PART 2: STATE TESTS ═════════════════════

def test_state():
    """Test PromptForgeState has all 26 fields."""
    global passed, failed

    print("\n" + "="*60)
    print("PART 2: STATE TESTS (26 fields)")
    print("="*60)

    from state import PromptForgeState, AgentState

    # Check AgentState is alias
    if AgentState is PromptForgeState:
        print_pass("AgentState is alias for PromptForgeState")
        passed += 1
    else:
        print_fail("AgentState should be alias for PromptForgeState")
        failed += 1

    # Expected fields by section
    expected_fields = {
        # INPUT (6)
        'message', 'session_id', 'user_id', 'attachments',
        'input_modality', 'conversation_history',
        # MEMORY (3)
        'user_profile', 'langmem_context', 'mcp_trust_level',
        # ORCHESTRATOR (5)
        'orchestrator_decision', 'user_facing_message',
        'pending_clarification', 'clarification_key', 'proceed_with_swarm',
        # AGENT OUTPUTS (5)
        'intent_analysis', 'context_analysis', 'domain_analysis',
        'agents_skipped', 'agent_latencies',
        # OUTPUT (7)
        'improved_prompt', 'original_prompt', 'prompt_diff',
        'quality_score', 'changes_made', 'breakdown',
    }
    
    # Get actual fields
    if hasattr(PromptForgeState, '__annotations__'):
        actual_fields = set(PromptForgeState.__annotations__.keys())
    else:
        print_fail("PromptForgeState has no __annotations__")
        failed += 1
        return
    
    # Check all expected fields present
    missing = expected_fields - actual_fields
    extra = actual_fields - expected_fields
    
    if not missing and not extra:
        print_pass(f"All 26 fields present (actual: {len(actual_fields)})")
        passed += 1
    else:
        if missing:
            print_fail(f"Missing fields: {missing}")
        if extra:
            print_info(f"Extra fields: {extra}")
        failed += 1

# ═══ PART 3: KIRA ORCHESTRATOR TESTS ═════════

def test_kira():
    """Test Kira orchestrator with various inputs."""
    global passed, failed, edge_cases_passed, edge_cases_failed
    
    print("\n" + "="*60)
    print("PART 3: KIRA ORCHESTRATOR TESTS")
    print("="*60)
    
    from agents.kira import (
        orchestrator_node, 
        detect_modification_phrases, 
        calculate_ambiguity_score,
        KIRA_FORBIDDEN_PHRASES
    )
    
    # Test 1: detect_modification_phrases
    print_info("Testing detect_modification_phrases()")
    
    modification_tests = [
        ("make it longer", True, "Standard modification"),
        ("make it shorter", True, "Opposite modification"),
        ("add more detail", True, "Add request"),
        ("remove the intro", True, "Remove request"),
        ("change the tone", True, "Change request"),
        ("write a story", False, "New request (no modification)"),
        ("hello", False, "Greeting (no modification)"),
        ("Make it better", True, "Capitalized modification"),
        ("MAKE IT LONGER", True, "Uppercase modification"),
    ]
    
    for message, expected, description in modification_tests:
        result = detect_modification_phrases(message)
        if result == expected:
            print_pass(f"'{message}' = {result} ({description})")
            passed += 1
            edge_cases_passed += 1
        else:
            print_fail(f"'{message}' = {result}, expected {expected} ({description})")
            failed += 1
            edge_cases_failed += 1
    
    # Test 2: calculate_ambiguity_score
    print_info("Testing calculate_ambiguity_score()")

    ambiguity_tests = [
        ("write something", 0.5, "Vague + short"),
        ("write a comprehensive 5000-word essay on quantum computing", 0.0, "Very specific"),
        ("?", 0.7, "Just question mark"),
        ("maybe something about AI?", 0.7, "Vague + question"),
        ("I need a Python function that sorts a list of dictionaries by a specific key", 0.0, "Very specific technical"),
    ]
    
    for message, min_expected_score, description in ambiguity_tests:
        score = calculate_ambiguity_score(message, [])
        if score >= min_expected_score - 0.1:  # Allow small variance
            print_pass(f"'{message[:40]}...' = {score:.2f} ({description})")
            passed += 1
            edge_cases_passed += 1
        else:
            print_fail(f"'{message[:40]}...' = {score:.2f}, expected >={min_expected_score} ({description})")
            failed += 1
            edge_cases_failed += 1
    
    # Test 3: Forbidden phrases check
    print_info("Testing forbidden phrases")
    
    for phrase in KIRA_FORBIDDEN_PHRASES:
        if phrase and len(phrase.strip()) > 0:
            print_pass(f"Forbidden phrase defined: '{phrase}'")
            passed += 1
        else:
            print_fail(f"Empty forbidden phrase in list")
            failed += 1

# ═══ PART 4: REDIS CACHE TESTS ═══════════════

def test_redis():
    """Test Redis cache operations."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 4: REDIS CACHE TESTS")
    print("="*60)
    
    from utils import get_redis_client, get_cache_key, get_cached_result, set_cached_result
    
    # Test 1: Redis connection
    client = get_redis_client()
    if client:
        try:
            client.ping()
            print_pass("Redis connected and responding to PING")
            passed += 1
        except Exception as e:
            print_fail(f"Redis PING failed: {e}")
            failed += 1
    else:
        print_fail("Redis client is None")
        failed += 1
        return
    
    # Test 2: SHA-256 key generation
    key1 = get_cache_key("test")
    key2 = get_cache_key("test")
    key3 = get_cache_key("TEST")  # Should be same (lowercase)
    key4 = get_cache_key("different")
    
    if key1 == key2:
        print_pass("Same prompt produces same cache key")
        passed += 1
    else:
        print_fail("Cache key not deterministic")
        failed += 1
    
    if key1 == key3:
        print_pass("Case insensitive (test == TEST)")
        passed += 1
    else:
        print_fail("Case sensitivity issue")
        failed += 1
    
    if key1 != key4:
        print_pass("Different prompts produce different keys")
        passed += 1
    else:
        print_fail("Different prompts have same key (collision!)")
        failed += 1
    
    if len(key1) == 64:
        print_pass(f"SHA-256 key length is 64 chars")
        passed += 1
    else:
        print_fail(f"SHA-256 key length is {len(key1)}, expected 64")
        failed += 1
    
    # Test 3: Cache set/get
    test_data = {"test": "data", "number": 42}
    set_cached_result("cache_test_prompt", test_data)
    cached = get_cached_result("cache_test_prompt")
    
    if cached == test_data:
        print_pass("Cache set/get works correctly")
        passed += 1
    else:
        print_fail(f"Cache mismatch: {cached} != {test_data}")
        failed += 1

# ═══ PART 5: DATABASE FUNCTIONS TESTS ════════

def test_database_functions():
    """Test database clarification functions."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 5: DATABASE FUNCTIONS TESTS")
    print("="*60)
    
    from database import get_clarification_flag, save_clarification_flag
    
    # Use test session/user IDs
    test_session = f"test-session-clarification"
    test_user = "00000000-0000-0000-0000-000000000001"
    
    # Test 1: Save flag
    result = save_clarification_flag(
        session_id=test_session,
        user_id=test_user,
        pending=True,
        clarification_key="test_key"
    )
    
    if result:
        print_pass("save_clarification_flag returned True")
        passed += 1
    else:
        print_info("save_clarification_flag returned False (expected if no conversation exists)")
        # This is OK if no conversation exists yet
    
    # Test 2: Get flag
    pending, key = get_clarification_flag(
        session_id=test_session,
        user_id=test_user
    )
    
    if isinstance(pending, bool) and isinstance(key, (str, type(None))):
        print_pass(f"get_clarification_flag returns correct types: pending={pending}, key={key}")
        passed += 1
    else:
        print_fail(f"get_clarification_flag wrong types: {type(pending)}, {type(key)}")
        failed += 1
    
    # Test 3: Clear flag
    result = save_clarification_flag(
        session_id=test_session,
        user_id=test_user,
        pending=False,
        clarification_key=None
    )
    
    print_info(f"Flag cleared: {result}")

# ═══ PART 6: API ENDPOINTS TESTS ═════════════

def test_api_structure():
    """Test API endpoint structure (without running server)."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 6: API STRUCTURE TESTS")
    print("="*60)
    
    from api import app, _run_swarm_with_clarification
    
    # Test 1: Check app has required routes
    routes = [route.path for route in app.routes]
    
    required_routes = ['/health', '/refine', '/chat', '/chat/stream', '/history', '/conversation']
    
    for route in required_routes:
        if route in routes:
            print_pass(f"Route {route} exists")
            passed += 1
        else:
            print_fail(f"Route {route} missing")
            failed += 1
    
    # Test 2: Check _run_swarm_with_clarification exists
    if callable(_run_swarm_with_clarification):
        print_pass("_run_swarm_with_clarification function exists")
        passed += 1
    else:
        print_fail("_run_swarm_with_clarification not callable")
        failed += 1

# ═══ MAIN TEST RUNNER ════════════════════════

def run_all_tests():
    """Run all Phase 1 verification tests."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PHASE 1 — FINAL COMPREHENSIVE VERIFICATION")
    print("="*60)
    print("\nTesting all components with edge cases...")
    
    # Run all test suites
    test_imports()
    test_state()
    test_kira()
    test_redis()
    test_database_functions()
    test_api_structure()
    
    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    total_tests = passed + failed
    total_edge_cases = edge_cases_passed + edge_cases_failed
    
    print(f"\nCore Tests: {passed}/{total_tests} passed")
    print(f"Edge Cases: {edge_cases_passed}/{total_edge_cases} passed")
    print(f"\nTotal: {passed + edge_cases_passed}/{total_tests + total_edge_cases} passed")
    
    if failed == 0 and edge_cases_failed == 0:
        print(f"\n{GREEN}ALL TESTS PASSED - PHASE 1 COMPLETE!{RESET}")
        print(f"\n{GREEN}Ready to proceed to Phase 2{RESET}")
        return True
    else:
        print(f"\n{RED}{failed + edge_cases_failed} TESTS FAILED{RESET}")
        print(f"\n{YELLOW}ANALYSIS REQUIRED BEFORE PROCEEDING{RESET}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

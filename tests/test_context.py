# tests/test_context.py
# ─────────────────────────────────────────────
# Context Agent Tests — Phase 2 STEP 3
#
# Run: python tests/test_context.py
# ─────────────────────────────────────────────

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.context import context_agent, validate_context_output
from state import AgentState

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_pass(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")


def print_fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")


passed = 0
failed = 0


def test_imports():
    """Test context agent imports correctly."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 1: IMPORT TESTS")
    print("="*60)
    
    try:
        from agents.context import context_agent
        print_pass("context_agent imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"context_agent import failed: {e}")
        failed += 1
    
    try:
        from agents.context import validate_context_output
        print_pass("validate_context_output imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"validate_context_output import failed: {e}")
        failed += 1


def test_skip_no_history():
    """Test context agent skips with no history."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 2: SKIP CONDITION TESTS")
    print("="*60)
    
    state = AgentState(
        raw_prompt="hello",
        conversation_history=[]
    )
    
    result = context_agent(state)
    
    if result["was_skipped"] == True and "no conversation history" in result["skip_reason"]:
        print_pass("Skip condition works (no history)")
        passed += 1
    else:
        print_fail("Skip condition not working")
        failed += 1


def test_with_history():
    """Test context agent runs with history."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 3: WITH HISTORY TESTS")
    print("="*60)
    
    state = AgentState(
        raw_prompt="build a React component",
        conversation_history=[{"role": "user", "message": "I need help"}]
    )
    
    result = context_agent(state)
    
    if result["was_skipped"] == False and "context_analysis" in result:
        print_pass("Context analysis runs with history")
        passed += 1
    else:
        print_fail("Context analysis not running")
        failed += 1


def test_validation():
    """Test context output validation."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 4: VALIDATION TESTS")
    print("="*60)
    
    good = {"skill_level": "intermediate", "tone": "technical", "confidence": 0.8}
    bad = {"skill_level": "unknown", "tone": "invalid"}
    
    if validate_context_output(good) == True:
        print_pass("Good output passes validation")
        passed += 1
    else:
        print_fail("Good output should pass")
        failed += 1
    
    if validate_context_output(bad) == False:
        print_pass("Bad output fails validation")
        passed += 1
    else:
        print_fail("Bad output should fail")
        failed += 1


def run_all_tests():
    """Run all context agent tests."""
    global passed, failed
    
    print("\n" + "="*60)
    print("CONTEXT AGENT — PHASE 2 STEP 3 VERIFICATION")
    print("="*60)
    
    test_imports()
    test_skip_no_history()
    test_with_history()
    test_validation()
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    total = passed + failed
    print(f"\nTests passed: {passed}/{total}")
    
    if failed == 0:
        print(f"\n{GREEN}ALL TESTS PASSED - STEP 3 COMPLETE!{RESET}")
        print(f"\n{GREEN}Ready to proceed to STEP 4 (Domain Agent){RESET}")
        return True
    else:
        print(f"\n{RED}{failed} TESTS FAILED{RESET}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

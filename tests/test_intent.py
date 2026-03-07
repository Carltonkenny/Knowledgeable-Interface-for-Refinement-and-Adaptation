# tests/test_intent.py
# ─────────────────────────────────────────────
# Intent Agent Tests — Phase 2 STEP 2
#
# Run: python tests/test_intent.py
# ─────────────────────────────────────────────

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.intent import intent_agent, validate_intent_output
from state import AgentState

# Colors for output
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


# ═══ TEST COUNTERS ════════════════════════════
passed = 0
failed = 0


# ═══ PART 1: IMPORT TESTS ════════════════════

def test_imports():
    """Test intent agent imports correctly."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 1: IMPORT TESTS")
    print("="*60)
    
    try:
        from agents.intent import intent_agent
        print_pass("intent_agent imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"intent_agent import failed: {e}")
        failed += 1
    
    try:
        from agents.intent import validate_intent_output
        print_pass("validate_intent_output imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"validate_intent_output import failed: {e}")
        failed += 1


# ═══ PART 2: BASIC INTENT ANALYSIS TESTS ════

def test_basic_intent():
    """Test intent agent with various prompts."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 2: BASIC INTENT ANALYSIS TESTS")
    print("="*60)
    
    tests = [
        ("write a story", "create narrative", "Creative writing request"),
        ("help me code", "get assistance", "Programming help request"),
        ("explain quantum computing", "understand complex topic", "Educational request"),
    ]
    
    for prompt, expected_keyword, description in tests:
        state = AgentState(
            raw_prompt=prompt,
            orchestrator_decision={}
        )
        
        result = intent_agent(state)
        
        if result["was_skipped"] == False and "intent_analysis" in result:
            print_pass(f"'{prompt}' - {description}")
            passed += 1
        else:
            print_fail(f"'{prompt}' - {description}")
            failed += 1


# ═══ PART 3: SKIP CONDITION TESTS ═══════════

def test_skip_condition():
    """Test intent agent skip condition."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 3: SKIP CONDITION TESTS")
    print("="*60)
    
    # Test with skip flag set
    state = AgentState(
        raw_prompt="hi",
        orchestrator_decision={"skip_intent": True, "intent_skip_reason": "simple command"}
    )
    
    result = intent_agent(state)
    
    if result["was_skipped"] == True and "simple command" in result["skip_reason"]:
        print_pass("Skip condition works correctly")
        passed += 1
    else:
        print_fail("Skip condition not working")
        failed += 1


# ═══ PART 4: VALIDATION TESTS ═══════════════

def test_validation():
    """Test intent output validation."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 4: VALIDATION TESTS")
    print("="*60)
    
    # Good output
    good_result = {
        "primary_intent": "create engaging content",
        "goal_clarity": "high",
        "confidence": 0.85
    }
    
    # Bad output
    bad_result = {
        "primary_intent": "",
        "goal_clarity": "unknown"
    }
    
    if validate_intent_output(good_result) == True:
        print_pass("Good output passes validation")
        passed += 1
    else:
        print_fail("Good output should pass validation")
        failed += 1
    
    if validate_intent_output(bad_result) == False:
        print_pass("Bad output fails validation")
        passed += 1
    else:
        print_fail("Bad output should fail validation")
        failed += 1


# ═══ PART 5: EDGE CASE TESTS ═══════════════

def test_edge_cases():
    """Test intent agent edge cases."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 5: EDGE CASE TESTS")
    print("="*60)
    
    # Empty prompt
    state = AgentState(
        raw_prompt="",
        orchestrator_decision={}
    )
    
    try:
        result = intent_agent(state)
        if "intent_analysis" in result:
            print_pass("Empty prompt handled gracefully")
            passed += 1
        else:
            print_fail("Empty prompt not handled")
            failed += 1
    except Exception as e:
        print_fail(f"Empty prompt caused exception: {e}")
        failed += 1
    
    # Very long prompt
    state = AgentState(
        raw_prompt="write a very long and detailed story " * 50,
        orchestrator_decision={}
    )
    
    try:
        result = intent_agent(state)
        if "intent_analysis" in result:
            print_pass("Long prompt handled gracefully")
            passed += 1
        else:
            print_fail("Long prompt not handled")
            failed += 1
    except Exception as e:
        print_fail(f"Long prompt caused exception: {e}")
        failed += 1


# ═══ MAIN TEST RUNNER ════════════════════════

def run_all_tests():
    """Run all intent agent tests."""
    global passed, failed
    
    print("\n" + "="*60)
    print("INTENT AGENT — PHASE 2 STEP 2 VERIFICATION")
    print("="*60)
    
    # Run all test suites
    test_imports()
    test_basic_intent()
    test_skip_condition()
    test_validation()
    test_edge_cases()
    
    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    total = passed + failed
    
    print(f"\nTests passed: {passed}/{total}")
    
    if failed == 0:
        print(f"\n{GREEN}ALL TESTS PASSED - STEP 2 COMPLETE!{RESET}")
        print(f"\n{GREEN}Ready to proceed to STEP 3 (Context Agent){RESET}")
        return True
    else:
        print(f"\n{RED}{failed} TESTS FAILED{RESET}")
        print(f"\n{YELLOW}Fix failures before proceeding{RESET}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# tests/test_domain.py
# ─────────────────────────────────────────────
# Domain Agent Tests — Phase 2 STEP 4
#
# Run: python tests/test_domain.py
# ─────────────────────────────────────────────

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.domain import domain_agent, validate_domain_output
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
    """Test domain agent imports correctly."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 1: IMPORT TESTS")
    print("="*60)
    
    try:
        from agents.domain import domain_agent
        print_pass("domain_agent imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"domain_agent import failed: {e}")
        failed += 1
    
    try:
        from agents.domain import validate_domain_output
        print_pass("validate_domain_output imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"validate_domain_output import failed: {e}")
        failed += 1


def test_skip_high_confidence():
    """Test domain agent skips with high confidence."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 2: SKIP CONDITION TESTS")
    print("="*60)
    
    state = AgentState(
        raw_prompt="React component",
        user_profile={"domain_confidence": 0.95}
    )
    
    result = domain_agent(state)
    
    if result["was_skipped"] == True and "confidence" in result["skip_reason"]:
        print_pass("Skip condition works (high confidence)")
        passed += 1
    else:
        print_fail("Skip condition not working")
        failed += 1


def test_domain_identification():
    """Test domain agent identifies domains."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 3: DOMAIN IDENTIFICATION TESTS")
    print("="*60)
    
    tests = [
        ("FastAPI endpoint", "backend"),
        ("React component", "frontend"),
        ("write a story", "creative"),
    ]
    
    for prompt, expected_keyword in tests:
        state = AgentState(
            raw_prompt=prompt,
            user_profile={}
        )
        
        result = domain_agent(state)
        
        if result["was_skipped"] == False and "domain_analysis" in result:
            print_pass(f"'{prompt}' - domain identified")
            passed += 1
        else:
            print_fail(f"'{prompt}' - domain not identified")
            failed += 1


def test_validation():
    """Test domain output validation."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 4: VALIDATION TESTS")
    print("="*60)
    
    good = {"primary_domain": "fastapi", "relevant_patterns": ["role_assignment"], "confidence": 0.8}
    bad = {"primary_domain": "tech", "relevant_patterns": [], "confidence": 0.3}
    
    if validate_domain_output(good) == True:
        print_pass("Good output passes validation")
        passed += 1
    else:
        print_fail("Good output should pass")
        failed += 1
    
    if validate_domain_output(bad) == False:
        print_pass("Bad output fails validation")
        passed += 1
    else:
        print_fail("Bad output should fail")
        failed += 1


def run_all_tests():
    """Run all domain agent tests."""
    global passed, failed
    
    print("\n" + "="*60)
    print("DOMAIN AGENT — PHASE 2 STEP 4 VERIFICATION")
    print("="*60)
    
    test_imports()
    test_skip_high_confidence()
    test_domain_identification()
    test_validation()
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    total = passed + failed
    print(f"\nTests passed: {passed}/{total}")
    
    if failed == 0:
        print(f"\n{GREEN}ALL TESTS PASSED - STEP 4 COMPLETE!{RESET}")
        print(f"\n{GREEN}Ready to proceed to STEP 5 (Prompt Engineer){RESET}")
        return True
    else:
        print(f"\n{RED}{failed} TESTS FAILED{RESET}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

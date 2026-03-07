# tests/test_prompt_engineer.py
# ─────────────────────────────────────────────
# Prompt Engineer Agent Tests — Phase 2 STEP 5
#
# Run: python tests/test_prompt_engineer.py
# ─────────────────────────────────────────────

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.prompt_engineer import prompt_engineer_agent, validate_engineer_output
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
    """Test prompt engineer imports correctly."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 1: IMPORT TESTS")
    print("="*60)
    
    try:
        from agents.prompt_engineer import prompt_engineer_agent
        print_pass("prompt_engineer_agent imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"prompt_engineer_agent import failed: {e}")
        failed += 1
    
    try:
        from agents.prompt_engineer import validate_engineer_output
        print_pass("validate_engineer_output imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"validate_engineer_output import failed: {e}")
        failed += 1


def test_never_skips():
    """Test prompt engineer never skips."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 2: NEVER SKIP TESTS")
    print("="*60)
    
    state = AgentState(
        raw_prompt="test",
        intent_analysis={},
        context_analysis={},
        domain_analysis={}
    )
    
    result = prompt_engineer_agent(state)
    
    if result["was_skipped"] == False:
        print_pass("Prompt engineer never skips")
        passed += 1
    else:
        print_fail("Prompt engineer should never skip")
        failed += 1


def test_with_full_swarm():
    """Test prompt engineer with full swarm analysis."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 3: FULL SWARM TESTS")
    print("="*60)
    
    state = AgentState(
        raw_prompt="write a story",
        intent_analysis={"primary_intent": "create narrative", "goal_clarity": "low"},
        context_analysis={"skill_level": "intermediate", "tone": "creative"},
        domain_analysis={"primary_domain": "creative writing", "relevant_patterns": ["role_assignment"]}
    )
    
    result = prompt_engineer_agent(state)
    
    if "improved_prompt" in result and result["improved_prompt"]:
        print_pass("Improved prompt generated")
        passed += 1
    else:
        print_fail("Improved prompt not generated")
        failed += 1


def test_validation():
    """Test prompt engineer output validation."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 4: VALIDATION TESTS")
    print("="*60)
    
    original = "write a story"
    
    good = {
        "improved_prompt": "You are a seasoned author. Write a 1,200-word story with atmosphere and tension.",
        "changes_made": ["Added role assignment", "Specified length", "Included tone guidance"],
        "quality_score": {"specificity": 4, "clarity": 5, "actionability": 4}
    }
    
    bad = {
        "improved_prompt": "write a story",
        "changes_made": ["Minor tweak"],
        "quality_score": {"specificity": 1, "clarity": 1, "actionability": 1}
    }
    
    if validate_engineer_output(good, original) == True:
        print_pass("Good output passes validation")
        passed += 1
    else:
        print_fail("Good output should pass")
        failed += 1
    
    if validate_engineer_output(bad, original) == False:
        print_pass("Bad output fails validation")
        passed += 1
    else:
        print_fail("Bad output should fail")
        failed += 1


def test_fallback():
    """Test prompt engineer fallback on error."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 5: FALLBACK TESTS")
    print("="*60)
    
    # Empty upstream results should return fallback
    state = AgentState(
        raw_prompt="test prompt",
        intent_analysis={},
        context_analysis={},
        domain_analysis={}
    )
    
    result = prompt_engineer_agent(state)
    
    if "improved_prompt" in result and "[Analysis failed]" in result["improved_prompt"]:
        print_pass("Fallback works for empty upstream")
        passed += 1
    else:
        print_fail("Fallback not working")
        failed += 1


def run_all_tests():
    """Run all prompt engineer tests."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PROMPT ENGINEER AGENT — PHASE 2 STEP 5 VERIFICATION")
    print("="*60)
    
    test_imports()
    test_never_skips()
    test_with_full_swarm()
    test_validation()
    test_fallback()
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    total = passed + failed
    print(f"\nTests passed: {passed}/{total}")
    
    if failed == 0:
        print(f"\n{GREEN}ALL TESTS PASSED - STEP 5 COMPLETE!{RESET}")
        print(f"\n{GREEN}Ready to proceed to STEP 6 (LangGraph Workflow){RESET}")
        return True
    else:
        print(f"\n{RED}{failed} TESTS FAILED{RESET}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

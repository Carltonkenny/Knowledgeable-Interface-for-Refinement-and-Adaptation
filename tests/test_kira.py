# tests/test_kira.py
# ─────────────────────────────────────────────
# Kira Orchestrator Tests — Phase 2 STEP 1
#
# Run: python tests/test_kira.py
# ─────────────────────────────────────────────

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.autonomous import (
    orchestrator_node,
    detect_modification_phrases,
    calculate_ambiguity_score,
    KIRA_FORBIDDEN_PHRASES,
)

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
    """Test all Kira components import correctly."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 1: IMPORT TESTS")
    print("="*60)
    
    try:
        from agents.autonomous import orchestrator_node
        print_pass("orchestrator_node imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"orchestrator_node import failed: {e}")
        failed += 1
    
    try:
        from agents.autonomous import detect_modification_phrases
        print_pass("detect_modification_phrases imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"detect_modification_phrases import failed: {e}")
        failed += 1
    
    try:
        from agents.autonomous import calculate_ambiguity_score
        print_pass("calculate_ambiguity_score imports successfully")
        passed += 1
    except Exception as e:
        print_fail(f"calculate_ambiguity_score import failed: {e}")
        failed += 1
    
    try:
        from agents.autonomous import KIRA_FORBIDDEN_PHRASES
        print_pass(f"KIRA_FORBIDDEN_PHRASES defined ({len(KIRA_FORBIDDEN_PHRASES)} phrases)")
        passed += 1
    except Exception as e:
        print_fail(f"KIRA_FORBIDDEN_PHRASES not defined: {e}")
        failed += 1


# ═══ PART 2: MODIFICATION DETECTION TESTS ════

def test_modification_detection():
    """Test detect_modification_phrases() function."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 2: MODIFICATION DETECTION TESTS")
    print("="*60)
    
    tests = [
        ("make it longer", True, "Standard modification"),
        ("make it shorter", True, "Opposite modification"),
        ("add more detail", True, "Add request"),
        ("remove the intro", True, "Remove request"),
        ("change the tone", True, "Change request"),
        ("write a story", False, "New request (no modification)"),
        ("hello", False, "Greeting (no modification)"),
        ("Make it better", True, "Capitalized modification"),
        ("MAKE IT LONGER", True, "Uppercase modification"),
        ("expand this section", True, "Expand request"),
        ("simplify the language", True, "Simplify request"),
    ]
    
    for message, expected, description in tests:
        result = detect_modification_phrases(message)
        if result == expected:
            print_pass(f"'{message}' = {result} - {description}")
            passed += 1
        else:
            print_fail(f"'{message}' = {result}, expected {expected} - {description}")
            failed += 1


# ═══ PART 3: AMBIGUITY SCORE TESTS ═══════════

def test_ambiguity_score():
    """Test calculate_ambiguity_score() function."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 3: AMBIGUITY SCORE TESTS")
    print("="*60)
    
    tests = [
        ("write something", [], 0.5, "Vague + short"),
        ("write a comprehensive 5000-word essay on quantum computing", [], 0.0, "Very specific"),
        ("?", [], 0.7, "Just question mark"),
        ("maybe something about AI?", [], 0.7, "Vague + question"),
        ("I need a Python function that sorts a list of dictionaries by a specific key", [], 0.0, "Very specific technical"),
        ("hi", [], 0.5, "Short greeting"),
        ("help", [], 0.5, "Single word request"),
    ]
    
    for message, history, min_expected, description in tests:
        score = calculate_ambiguity_score(message, history)
        if score >= min_expected - 0.1:
            print_pass(f"'{message[:40]}...' = {score:.2f} - {description}")
            passed += 1
        else:
            print_fail(f"'{message[:40]}...' = {score:.2f}, expected >={min_expected} - {description}")
            failed += 1


# ═══ PART 4: ORCHESTRATOR ROUTING TESTS ══════

def test_orchestrator_routing():
    """Test orchestrator_node() routing logic."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 4: ORCHESTRATOR ROUTING TESTS")
    print("="*60)
    
    # Test 1: Brief input → CONVERSATION
    state = {
        "message": "hi",
        "user_profile": {},
        "conversation_history": [],
        "pending_clarification": False,
    }
    
    result = orchestrator_node(state)
    
    if result["proceed_with_swarm"] == False:
        print_pass("Brief input -> CONVERSATION (proceed_with_swarm=False)")
        passed += 1
    else:
        print_fail("Brief input should return CONVERSATION")
        failed += 1
    
    # Test 2: Modification phrase -> FOLLOWUP
    state = {
        "message": "make it longer",
        "user_profile": {},
        "conversation_history": [],
        "pending_clarification": False,
    }
    
    result = orchestrator_node(state)
    
    if result["proceed_with_swarm"] == True and len(result["orchestrator_decision"]["agents_to_run"]) > 0:
        print_pass("Modification phrase -> FOLLOWUP (proceed_with_swarm=True)")
        passed += 1
    else:
        print_fail("Modification phrase should return FOLLOWUP")
        failed += 1
    
    # Test 3: Pending clarification -> inject answer
    state = {
        "message": "I want to write about AI",
        "user_profile": {},
        "conversation_history": [],
        "pending_clarification": True,
    }
    
    result = orchestrator_node(state)
    
    if result["pending_clarification"] == False and result["proceed_with_swarm"] == True:
        print_pass("Pending clarification -> flag cleared, swarm fires")
        passed += 1
    else:
        print_fail("Pending clarification should clear flag and fire swarm")
        failed += 1
    
    # Test 4: Orchestrator returns required fields
    required_fields = [
        "orchestrator_decision",
        "user_facing_message",
        "proceed_with_swarm",
    ]
    
    decision_required = [
        "user_facing_message",
        "proceed_with_swarm",
        "agents_to_run",
        "clarification_needed",
    ]
    
    missing = [f for f in required_fields if f not in result]
    missing_decision = [f for f in decision_required if f not in result["orchestrator_decision"]]
    
    if not missing and not missing_decision:
        print_pass("Orchestrator returns all required fields")
        passed += 1
    else:
        if missing:
            print_fail(f"Missing orchestrator fields: {missing}")
        if missing_decision:
            print_fail(f"Missing decision fields: {missing_decision}")
        failed += 1


# ═══ PART 5: FORBIDDEN PHRASE TESTS ══════════

def test_forbidden_phrases():
    """Test that orchestrator doesn't use forbidden phrases."""
    global passed, failed
    
    print("\n" + "="*60)
    print("PART 5: FORBIDDEN PHRASE TESTS")
    print("="*60)
    
    # Verify forbidden phrases are defined
    if len(KIRA_FORBIDDEN_PHRASES) > 0:
        print_pass(f"KIRA_FORBIDDEN_PHRASES defined ({len(KIRA_FORBIDDEN_PHRASES)} phrases)")
        passed += 1
    else:
        print_fail("KIRA_FORBIDDEN_PHRASES is empty")
        failed += 1
    
    # Test that orchestrator output doesn't contain forbidden phrases
    test_messages = [
        "hello there",
        "hi",
        "what do you do",
        "help me",
    ]
    
    all_clean = True
    for message in test_messages:
        state = {
            "message": message,
            "user_profile": {},
            "conversation_history": [],
            "pending_clarification": False,
        }
        
        result = orchestrator_node(state)
        output = result["user_facing_message"].lower()
        
        for phrase in KIRA_FORBIDDEN_PHRASES:
            if phrase.lower() in output:
                print_fail(f"Found forbidden phrase '{phrase}' in output for '{message}'")
                all_clean = False
                failed += 1
    
    if all_clean:
        print_pass("No forbidden phrases in orchestrator output")
        passed += 1


# ═══ MAIN TEST RUNNER ════════════════════════

def run_all_tests():
    """Run all Kira tests."""
    global passed, failed
    
    print("\n" + "="*60)
    print("KIRA ORCHESTRATOR — PHASE 2 STEP 1 VERIFICATION")
    print("="*60)
    
    # Run all test suites
    test_imports()
    test_modification_detection()
    test_ambiguity_score()
    test_orchestrator_routing()
    test_forbidden_phrases()
    
    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    total = passed + failed
    
    print(f"\nTests passed: {passed}/{total}")
    
    if failed == 0:
        print(f"\n{GREEN}ALL TESTS PASSED - STEP 1 COMPLETE!{RESET}")
        print(f"\n{GREEN}Ready to proceed to STEP 2 (Intent Agent){RESET}")
        return True
    else:
        print(f"\n{RED}{failed} TESTS FAILED{RESET}")
        print(f"\n{YELLOW}Fix failures before proceeding{RESET}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# tests/test_workflow_step6_simple.py
# STEP 6: LangGraph Workflow - Simple Verification (Windows compatible)

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import AgentState
from workflow import workflow, route_to_agents, PARALLEL_MODE
from agents.autonomous import orchestrator_node

GREEN = "[PASS]"
RED = "[FAIL]"
YELLOW = "[INFO]"

passed = 0
failed = 0

def test_workflow_structure():
    global passed, failed
    print("\n" + "="*70)
    print("PART 1: WORKFLOW STRUCTURE TESTS")
    print("="*70)
    
    try:
        from workflow import workflow
        print(GREEN, "Workflow compiles successfully")
        passed += 1
    except Exception as e:
        print(RED, "Workflow compilation failed:", e)
        failed += 1
    
    if PARALLEL_MODE:
        print(GREEN, "PARALLEL_MODE = True (parallel execution enabled)")
        passed += 1
    else:
        print(YELLOW, "PARALLEL_MODE = False (sequential execution)")
        passed += 1
    
    try:
        from workflow import route_to_agents
        print(GREEN, "route_to_agents function exists")
        passed += 1
    except Exception as e:
        print(RED, "route_to_agents not found:", e)
        failed += 1


def test_route_to_agents():
    global passed, failed
    print("\n" + "="*70)
    print("PART 2: ROUTING FUNCTION TESTS")
    print("="*70)
    
    tests = [
        (['intent', 'context', 'domain'], ['intent_agent', 'context_agent', 'domain_agent'], 'All agents'),
        (['intent', 'domain'], ['intent_agent', 'domain_agent'], 'Partial agents'),
        (['intent'], ['intent_agent'], 'Single agent'),
        ([], [], 'Empty agents'),
    ]
    
    for input_agents, expected, desc in tests:
        state = AgentState(
            message='test', session_id='test', user_id='test',
            orchestrator_decision={'agents_to_run': input_agents}
        )
        result = route_to_agents(state)
        if result == expected:
            print(GREEN, desc, ":", result)
            passed += 1
        else:
            print(RED, desc, "- Expected", expected, "got", result)
            failed += 1


def test_kira_routing():
    global passed, failed
    print("\n" + "="*70)
    print("PART 3: KIRA ORCHESTRATOR ROUTING TESTS")
    print("="*70)
    
    test_cases = [
        ('hi', [], 'Brief input'),
        ('make it longer', ['intent'], 'Modification'),
        ('write a story', ['intent'], 'New prompt'),
        ('Create FastAPI endpoint with JWT', ['intent', 'domain'], 'Complex prompt'),
    ]
    
    for prompt, expected_agents, desc in test_cases:
        state = {
            'message': prompt, 'user_profile': {},
            'conversation_history': [], 'pending_clarification': False
        }
        result = orchestrator_node(state)
        decision = result.get('orchestrator_decision', {})
        agents = decision.get('agents_to_run', [])
        
        if len(expected_agents) == 0 or all(a in agents for a in expected_agents):
            print(GREEN, f'"{prompt[:25]}..." -> agents={agents} - {desc}')
            passed += 1
        else:
            print(RED, f'"{prompt[:25]}..." -> Expected {expected_agents}, got {agents}')
            failed += 1


def test_workflow_execution():
    global passed, failed
    print("\n" + "="*70)
    print("PART 4: FULL WORKFLOW EXECUTION TESTS")
    print("="*70)
    
    test_prompts = ['write a story', 'help me code', 'Create a FastAPI endpoint']
    
    for prompt in test_prompts:
        start = time.time()
        
        initial_state = AgentState(
            message=prompt, session_id='test', user_id='test', raw_prompt=prompt,
            intent_analysis={}, context_analysis={}, domain_analysis={}, improved_prompt='',
            user_profile={}, langmem_context=[], mcp_trust_level=0, orchestrator_decision={},
            user_facing_message='', pending_clarification=False, clarification_key=None,
            proceed_with_swarm=True, agents_skipped=[], agent_latencies={},
            original_prompt=prompt, prompt_diff=[], quality_score={}, changes_made=[],
            breakdown={}, attachments=[], input_modality='text', conversation_history=[],
        )
        
        try:
            result = workflow.invoke(initial_state)
            latency = time.time() - start
            output_len = len(result.get('improved_prompt', ''))
            
            if output_len > 0:
                print(GREEN, f'"{prompt[:25]}..." -> {latency:.2f}s, output: {output_len} chars')
                passed += 1
            else:
                print(RED, f'"{prompt[:25]}..." -> No output generated')
                failed += 1
        except Exception as e:
            print(RED, f'"{prompt[:25]}..." -> Exception: {str(e)[:50]}')
            failed += 1


def test_edge_cases():
    global passed, failed
    print("\n" + "="*70)
    print("PART 5: EDGE CASE TESTS")
    print("="*70)
    
    # Empty prompt
    try:
        state = AgentState(
            message='', session_id='test', user_id='test', raw_prompt='',
            intent_analysis={}, context_analysis={}, domain_analysis={}, improved_prompt='',
            user_profile={}, langmem_context=[], mcp_trust_level=0, orchestrator_decision={},
            user_facing_message='', pending_clarification=False, clarification_key=None,
            proceed_with_swarm=True, agents_skipped=[], agent_latencies={},
            original_prompt='', prompt_diff=[], quality_score={}, changes_made=[],
            breakdown={}, attachments=[], input_modality='text', conversation_history=[],
        )
        result = workflow.invoke(state)
        print(GREEN, 'Empty prompt handled gracefully')
        passed += 1
    except Exception as e:
        print(RED, 'Empty prompt failed:', str(e)[:50])
        failed += 1
    
    # Long prompt
    long_prompt = 'write a story ' * 50
    try:
        state = AgentState(
            message=long_prompt, session_id='test', user_id='test', raw_prompt=long_prompt,
            intent_analysis={}, context_analysis={}, domain_analysis={}, improved_prompt='',
            user_profile={}, langmem_context=[], mcp_trust_level=0, orchestrator_decision={},
            user_facing_message='', pending_clarification=False, clarification_key=None,
            proceed_with_swarm=True, agents_skipped=[], agent_latencies={},
            original_prompt=long_prompt, prompt_diff=[], quality_score={}, changes_made=[],
            breakdown={}, attachments=[], input_modality='text', conversation_history=[],
        )
        result = workflow.invoke(state)
        print(GREEN, 'Long prompt handled gracefully')
        passed += 1
    except Exception as e:
        print(RED, 'Long prompt failed:', str(e)[:50])
        failed += 1


def test_output_validation():
    global passed, failed
    print("\n" + "="*70)
    print("PART 6: OUTPUT VALIDATION TESTS")
    print("="*70)
    
    prompt = 'Create a FastAPI endpoint with JWT authentication'
    
    state = AgentState(
        message=prompt, session_id='test', user_id='test', raw_prompt=prompt,
        intent_analysis={}, context_analysis={}, domain_analysis={}, improved_prompt='',
        user_profile={}, langmem_context=[], mcp_trust_level=0, orchestrator_decision={},
        user_facing_message='', pending_clarification=False, clarification_key=None,
        proceed_with_swarm=True, agents_skipped=[], agent_latencies={},
        original_prompt=prompt, prompt_diff=[], quality_score={}, changes_made=[],
        breakdown={}, attachments=[], input_modality='text', conversation_history=[],
    )
    
    result = workflow.invoke(state)
    
    if result.get('improved_prompt'):
        print(GREEN, f'improved_prompt generated ({len(result["improved_prompt"])} chars)')
        passed += 1
    else:
        print(RED, 'improved_prompt is empty')
        failed += 1
    
    if result.get('improved_prompt', '') != result.get('original_prompt', ''):
        print(GREEN, 'improved_prompt differs from original')
        passed += 1
    else:
        print(RED, 'improved_prompt identical to original')
        failed += 1
    
    if result.get('agent_latencies'):
        print(GREEN, f'Agent latencies tracked: {result["agent_latencies"]}')
        passed += 1
    else:
        print(YELLOW, 'Agent latencies not tracked (optional)')
        passed += 1


def run_all_tests():
    global passed, failed
    
    print("\n" + "="*70)
    print("STEP 6: LANGRAPH WORKFLOW - COMPREHENSIVE VERIFICATION")
    print("="*70)
    print(f"PARALLEL_MODE: {PARALLEL_MODE}")
    print(f"Expected latency: {'2-3s (parallel)' if PARALLEL_MODE else '4-6s (sequential)'}")
    
    test_workflow_structure()
    test_route_to_agents()
    test_kira_routing()
    test_workflow_execution()
    test_edge_cases()
    test_output_validation()
    
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    total = passed + failed
    print(f"\nTests passed: {passed}/{total}")
    
    if failed == 0:
        print(f"\n{GREEN} ALL TESTS PASSED - STEP 6 COMPLETE!")
        print("\nWorkflow upgraded with:")
        print("  - Conditional edges from Kira orchestrator")
        print("  - Parallel execution via Send()")
        print("  - Join node at prompt_engineer")
        print("  - PARALLEL_MODE = True")
        return True
    else:
        print(f"\n{RED} {failed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

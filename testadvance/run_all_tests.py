# testadvance/run_all_tests.py
# Master Test Runner for PromptForge v2.0

import subprocess
import sys
import os
import json
from datetime import datetime

def run_tests():
    """Run all tests and generate report."""
    
    print("="*60)
    print("PromptForge v2.0 — Comprehensive Test Suite")
    print("="*60)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test directories
    test_dirs = [
        ("Phase 1: Backend Core", "phase1"),
        ("Phase 2: Agent Swarm", "phase2"),
        ("Phase 3: MCP Integration", "phase3"),
        ("Integration Tests", "integration"),
        ("Edge Cases", "edge_cases"),
    ]
    
    results = {}
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for phase_name, phase_dir in test_dirs:
        print(f"\n{'='*60}")
        print(f"Running: {phase_name}")
        print(f"{'='*60}\n")
        
        # Run pytest
        cmd = [
            sys.executable, "-m", "pytest",
            phase_dir + "/",
            "-v",
            "--tb=short",
            "--maxfail=5",
            "-q"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per phase
            )
            
            # Parse results
            output = result.stdout + result.stderr
            
            # Count tests
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            skipped = output.count(" SKIPPED")
            errors = output.count(" ERROR")
            
            phase_total = passed + failed + skipped + errors
            
            results[phase_name] = {
                "total": phase_total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
                "output": output[-2000:]  # Last 2000 chars
            }
            
            total_tests += phase_total
            total_passed += passed
            total_failed += failed
            
            print(f"Results: {passed}/{phase_total} passed")
            if failed > 0:
                print(f"  ⚠️  {failed} failed")
            if errors > 0:
                print(f"  ❌ {errors} errors")
                
        except subprocess.TimeoutExpired:
            results[phase_name] = {"error": "Timeout (5 minutes)"}
            print("  ❌ TIMEOUT (5 minutes)")
        except Exception as e:
            results[phase_name] = {"error": str(e)}
            print(f"  ❌ ERROR: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Pass Rate: {(total_passed/total_tests*100) if total_tests > 0 else 0:.1f}%")
    
    # Save results
    os.makedirs("outputs", exist_ok=True)
    
    with open("outputs/test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "pass_rate": (total_passed/total_tests*100) if total_tests > 0 else 0,
            "phases": results
        }, f, indent=2)
    
    print(f"\nResults saved to: outputs/test_results.json")
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

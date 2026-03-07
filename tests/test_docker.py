#!/usr/bin/env python3
# tests/test_docker.py
# ─────────────────────────────────────────────
# Quick Docker deployment test script
# Run: python tests/test_docker.py
# ─────────────────────────────────────────────

import requests
import jwt
import datetime
import sys
import time

BASE_URL = "http://localhost:8000"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_test(msg):
    print(f"{BLUE}[TEST]{RESET} {msg}")

def print_pass(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")

def print_fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")

def print_info(msg):
    print(f"{YELLOW}[INFO]{RESET} {msg}")


def get_test_token():
    """Generate a test JWT token."""
    # Using the SUPABASE_JWT_SECRET from .env
    secret = '0144dddf-219e-4c2d-b8de-eb2aed6f597d'
    supabase_url = 'https://cckznjkzsfypssgecyya.supabase.co'
    
    payload = {
        'sub': '00000000-0000-0000-0000-000000000001',  # Supabase uses 'sub' claim
        'iss': supabase_url,  # Must match SUPABASE_URL
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def test_health():
    """Test health endpoint."""
    print_test("GET /health")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200 and resp.json().get('status') == 'ok':
            print_pass(f"Health check OK - {resp.json()}")
            return True
        else:
            print_fail(f"Unexpected response: {resp.text}")
            return False
    except Exception as e:
        print_fail(f"Connection failed: {e}")
        return False


def test_refine(token):
    """Test /refine endpoint."""
    print_test("POST /refine")
    
    test_prompt = "write a python function"
    
    try:
        resp = requests.post(
            f"{BASE_URL}/refine",
            json={
                "prompt": test_prompt,
                "session_id": "docker-test-session"
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"/refine succeeded")
            print_info(f"Original: {data.get('original_prompt', '')[:50]}...")
            print_info(f"Improved: {data.get('improved_prompt', '')[:100]}...")
            print_info(f"Breakdown keys: {list(data.get('breakdown', {}).keys())}")
            return True
        else:
            print_fail(f"Status {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_fail("Request timed out (expected if LLM is slow)")
        return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_chat_new_prompt(token):
    """Test /chat with new prompt."""
    print_test("POST /chat (NEW_PROMPT)")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": "write a short story",
                "session_id": "docker-test-chat"
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"/chat succeeded - type: {data.get('type')}")
            print_info(f"Reply: {data.get('reply', '')[:80]}...")
            return True
        else:
            print_fail(f"Status {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_fail("Request timed out")
        return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_chat_followup(token):
    """Test /chat with followup modification."""
    print_test("POST /chat (FOLLOWUP)")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": "make it longer",
                "session_id": "docker-test-chat"
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"/chat followup succeeded - type: {data.get('type')}")
            print_info(f"Reply: {data.get('reply', '')[:80]}...")
            return True
        else:
            print_fail(f"Status {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_fail("Request timed out")
        return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_history(token):
    """Test /history endpoint."""
    print_test("GET /history")
    
    try:
        resp = requests.get(
            f"{BASE_URL}/history?limit=5",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"/history succeeded - count: {data.get('count')}")
            return True
        else:
            print_fail(f"Status {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_conversation(token):
    """Test /conversation endpoint."""
    print_test("GET /conversation")
    
    try:
        resp = requests.get(
            f"{BASE_URL}/conversation?session_id=docker-test-chat&limit=10",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"/conversation succeeded - count: {data.get('count')}")
            return True
        else:
            print_fail(f"Status {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def main():
    """Run all Docker tests."""
    print("\n" + "="*60)
    print(f"{GREEN}PromptForge v2.0 - Docker Deployment Test{RESET}")
    print("="*60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Swagger:  {BASE_URL}/docs\n")
    
    # Wait for API to be ready
    print_info("Waiting for API to be ready...")
    for i in range(10):
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                print_pass("API is ready!\n")
                break
        except:
            pass
        time.sleep(1)
    else:
        print_fail("API did not respond within 10 seconds")
        print_info("Check logs: docker-compose logs -f")
        sys.exit(1)
    
    # Run tests
    passed = 0
    failed = 0
    
    # Test 1: Health (no auth)
    if test_health():
        passed += 1
    else:
        failed += 1
        print("\n" + RED + "Health check failed - stopping tests" + RESET)
        sys.exit(1)
    
    # Generate test token
    token = get_test_token()
    print_info(f"Generated test JWT token: {token[:40]}...\n")
    
    # Test 2: /refine
    print("="*60)
    if test_refine(token):
        passed += 1
    else:
        failed += 1
    
    # Test 3: /chat (new prompt)
    print("="*60)
    if test_chat_new_prompt(token):
        passed += 1
    else:
        failed += 1
    
    # Test 4: /chat (followup)
    print("="*60)
    if test_chat_followup(token):
        passed += 1
    else:
        failed += 1
    
    # Test 5: /history
    print("="*60)
    if test_history(token):
        passed += 1
    else:
        failed += 1
    
    # Test 6: /conversation
    print("="*60)
    if test_conversation(token):
        passed += 1
    else:
        failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"\n{GREEN}Passed: {passed}{RESET}")
    if failed > 0:
        print(f"{RED}Failed: {failed}{RESET}")
    
    if failed == 0:
        print(f"\n{GREEN}ALL TESTS PASSED! Docker deployment is working.{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print(f"  1. Open Swagger UI: {BASE_URL}/docs")
        print(f"  2. View logs: docker-compose logs -f")
        print(f"  3. Test interactively with curl or browser")
        return 0
    else:
        print(f"\n{YELLOW}Some tests failed. Check logs: docker-compose logs -f{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

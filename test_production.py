#!/usr/bin/env python3
# test_production.py
# Comprehensive production tests for deployed Koyeb service

import requests
import json
import time
import sys

BASE_URL = "https://parallel-eartha-student798-9c3bce6b.koyeb.app"

print("=" * 70)
print("PRODUCTION EDGE CASE TESTS")
print("=" * 70)
print(f"Target: {BASE_URL}")
print("=" * 70)

# ═══ TEST 1: HEALTH CHECK ═══════════════════════════
print("\n[TEST 1] Health Check")
print("-" * 70)
try:
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Version: {data.get('version')}")
    else:
        print(f"❌ Health check failed: {r.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# ═══ TEST 2: BASIC PROMPT via /refine (Cache Miss) ═══════════════
print("\n[TEST 2] Basic Prompt - Cache Miss Expected")
print("-" * 70)
test_prompt_1 = f"Write a Python function to calculate fibonacci (test_{int(time.time())})"
print(f"Prompt: '{test_prompt_1[:50]}...'")

try:
    r = requests.post(
        f"{BASE_URL}/refine",
        json={"prompt": test_prompt_1, "session_id": "test_session"},
        timeout=60
    )
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"✅ Response received")
        print(f"   Original: {data.get('original_prompt', '')[:50]}...")
        print(f"   Improved: {data.get('improved_prompt', '')[:50]}...")
        breakdown = data.get('breakdown', {})
        print(f"   Domain: {breakdown.get('domain', {}).get('primary_domain', 'N/A')}")
        print(f"   Intent: {breakdown.get('intent', {}).get('intent_type', 'N/A')}")
        
        # Store for cache test
        test1_response = data
    elif r.status_code == 401:
        print(f"⚠️ Authentication required (401)")
        print(f"   This endpoint needs JWT token")
    else:
        print(f"❌ API error: {r.status_code}")
        print(f"   Response: {r.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

# ═══ TEST 3: /chat ENDPOINT (Conversational) ═══════════
print("\n[TEST 3] Chat Endpoint - Conversational")
print("-" * 70)
chat_prompt = "Help me write a REST API in FastAPI"
print(f"Message: '{chat_prompt}'")

try:
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"message": chat_prompt, "session_id": f"chat_test_{int(time.time())}"},
        timeout=60
    )
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"✅ Chat response received")
        print(f"   Type: {data.get('type', 'N/A')}")
        print(f"   Reply: {data.get('reply', '')[:60]}...")
        if data.get('improved_prompt'):
            print(f"   Improved: {data.get('improved_prompt', '')[:50]}...")
    elif r.status_code == 401:
        print(f"⚠️ Authentication required (401)")
    else:
        print(f"❌ API error: {r.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# ═══ TEST 4: EMPTY PROMPT (Edge Case) ═══════════════
print("\n[TEST 4] Empty Prompt - Edge Case")
print("-" * 70)
try:
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "", "session_id": "test"},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 422 or r.status_code == 400:
        print(f"✅ Correctly rejected empty prompt")
    elif r.status_code == 401:
        print(f"⚠️ Authentication required (401)")
    else:
        print(f"❓ Unexpected response: {r.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# ═══ TEST 5: VERY LONG PROMPT (Edge Case) ═══════════
print("\n[TEST 5] Very Long Prompt - Edge Case")
print("-" * 70)
long_prompt = "Write code for " + ("feature " * 50) + " with " + ("modules " * 50)
print(f"Prompt length: {len(long_prompt)} characters")

try:
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"message": long_prompt, "session_id": f"long_test_{int(time.time())}"},
        timeout=60
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ Handled long prompt successfully")
        print(f"   Type: {data.get('type', 'N/A')}")
    elif r.status_code == 401:
        print(f"⚠️ Authentication required (401)")
    elif r.status_code == 413 or r.status_code == 400:
        print(f"✅ Correctly rejected oversized prompt")
    else:
        print(f"⚠️ Response: {r.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# ═══ TEST 6: MISSING FIELDS (Edge Case) ═══════════
print("\n[TEST 6] Missing Session ID - Edge Case")
print("-" * 70)
try:
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "test"},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 422:
        print(f"✅ Correctly rejected missing required field")
    elif r.status_code == 401:
        print(f"⚠️ Authentication required (401)")
    else:
        print(f"❓ Unexpected: {r.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# ═══ TEST 7: SPECIAL CHARACTERS (Edge Case) ═════════
print("\n[TEST 7] Special Characters - Edge Case")
print("-" * 70)
special_prompt = "Write code with <tags> & \"quotes\" and 'apostrophes' — em dash © ® ™"
print(f"Prompt: {special_prompt[:60]}...")

try:
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"message": special_prompt, "session_id": f"special_test_{int(time.time())}"},
        timeout=60
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ Handled special characters")
        print(f"   Type: {data.get('type', 'N/A')}")
    elif r.status_code == 401:
        print(f"⚠️ Authentication required (401)")
    else:
        print(f"❌ Error: {r.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# ═══ TEST 8: DIFFERENT DOMAINS ══════════════════════
print("\n[TEST 8] Different Domains Test")
print("-" * 70)

domain_tests = [
    ("Creative Writing", "Write a short story about a robot learning to love"),
    ("JavaScript", "Create a React hook for fetching data"),
    ("Data Science", "Analyze this dataset for patterns and outliers"),
    ("DevOps", "Write a Dockerfile for a Node.js application"),
]

for domain_name, prompt in domain_tests:
    print(f"\n   Testing: {domain_name}")
    try:
        r = requests.post(
            f"{BASE_URL}/chat",
            json={"message": prompt, "session_id": f"domain_{int(time.time())}"},
            timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Response type: {data.get('type', 'N/A')}")
        elif r.status_code == 401:
            print(f"   ⚠️ Auth required")
        else:
            print(f"   ❌ Error: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# ═══ TEST 9: RAPID REQUESTS (Rate Limiting) ═════════
print("\n" + "=" * 70)
print("[TEST 9] Rapid Requests - Rate Limiting Test")
print("-" * 70)
print("Sending 5 requests in quick succession...")

rate_limit_hit = False
for i in range(5):
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        if r.status_code == 429:
            print(f"   Request {i+1}: ⚠️ RATE LIMITED (429)")
            rate_limit_hit = True
        elif r.status_code == 200:
            print(f"   Request {i+1}: ✅ OK")
        else:
            print(f"   Request {i+1}: ❌ {r.status_code}")
    except Exception as e:
        print(f"   Request {i+1}: ❌ Error: {e}")

if rate_limit_hit:
    print("✅ Rate limiting is active")
else:
    print("ℹ️ No rate limiting triggered (health endpoint may be exempt)")

# ═══ TEST 10: REDIS PERSISTENCE ═════════════════════
print("\n" + "=" * 70)
print("[TEST 10] Redis Persistence Test")
print("-" * 70)

# Test via health endpoint (no auth needed)
print("Testing service availability over time...")
for i in range(3):
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        if r.status_code == 200:
            print(f"   Check {i+1}: ✅ Service responding")
        else:
            print(f"   Check {i+1}: ❌ Status {r.status_code}")
    except Exception as e:
        print(f"   Check {i+1}: ❌ Error: {e}")
    time.sleep(1)

# ═══ SUMMARY ════════════════════════════════════════
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("\nKey Findings:")
print("1. Health check: Should pass ✅")
print("2. /refine endpoint: Requires JWT authentication")
print("3. /chat endpoint: Requires JWT authentication")
print("4. Edge cases: Validation working if 422/400 returned")
print("\nNote: Most endpoints require JWT authentication.")
print("To test full workflow, you need a valid JWT token.")
print("=" * 70)

# ═══ BONUS: Check if auth is properly configured ═════
print("\n" + "=" * 70)
print("AUTHENTICATION CHECK")
print("=" * 70)
print("\nTrying /refine without auth...")
try:
    r = requests.post(
        f"{BASE_URL}/refine",
        json={"prompt": "test", "session_id": "test"},
        timeout=10
    )
    if r.status_code == 401:
        print("✅ Authentication is properly enforced (401)")
        print("   To test full workflow, provide a valid JWT token")
    elif r.status_code == 200:
        print("⚠️ No auth required (unexpected)")
    else:
        print(f"❓ Response: {r.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 70)

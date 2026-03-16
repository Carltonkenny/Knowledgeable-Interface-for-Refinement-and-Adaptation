#!/usr/bin/env python3
# test_with_login.py
# Sign in with test user and test the API

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

BASE_URL = "https://parallel-eartha-student798-9c3bce6b.koyeb.app"

print("=" * 70)
print("SIGN IN AND TEST API")
print("=" * 70)

# Use the user we just created
test_email = "testuser4638@example.com"
test_password = "TestPassword123!"

print(f"\nSigning in with: {test_email}")

try:
    # Sign in
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": test_email, "password": test_password},
        timeout=10
    )
    
    print(f"Sign-in response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access_token', '')
        
        if access_token:
            print(f"✅ Signed in successfully!")
            print(f"\nToken: {access_token[:50]}...")
            
            # Test the API
            test_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Test 1: /refine
            print("\n" + "=" * 70)
            print("TEST 1: /refine endpoint")
            print("=" * 70)
            
            r = requests.post(
                f"{BASE_URL}/refine",
                json={"prompt": "Write a Python function to calculate fibonacci", "session_id": "test_1"},
                headers=test_headers,
                timeout=60
            )
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"✅ SUCCESS!")
                print(f"   Original: {data.get('original_prompt', '')[:50]}...")
                print(f"   Improved: {data.get('improved_prompt', '')[:80]}...")
                breakdown = data.get('breakdown', {})
                print(f"   Intent: {breakdown.get('intent', {}).get('intent_type', 'N/A')}")
                print(f"   Domain: {breakdown.get('domain', {}).get('primary_domain', 'N/A')}")
            else:
                print(f"❌ Failed: {r.status_code}")
                print(f"   {r.text[:200]}")
            
            # Test 2: /chat
            print("\n" + "=" * 70)
            print("TEST 2: /chat endpoint")
            print("=" * 70)
            
            r = requests.post(
                f"{BASE_URL}/chat",
                json={"message": "Create a React component for authentication", "session_id": "test_2"},
                headers=test_headers,
                timeout=60
            )
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"✅ SUCCESS!")
                print(f"   Type: {data.get('type', 'N/A')}")
                print(f"   Reply: {data.get('reply', '')[:60]}...")
                if data.get('improved_prompt'):
                    print(f"   Improved: {data.get('improved_prompt', '')[:60]}...")
            else:
                print(f"❌ Failed: {r.status_code}")
            
            # Test 3: Duplicate prompt (cache hit)
            print("\n" + "=" * 70)
            print("TEST 3: Cache Test (same prompt)")
            print("=" * 70)
            
            r = requests.post(
                f"{BASE_URL}/refine",
                json={"prompt": "Write a Python function to calculate fibonacci", "session_id": "test_3"},
                headers=test_headers,
                timeout=60
            )
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                print(f"✅ Response received (should be faster from cache)")
            else:
                print(f"❌ Failed: {r.status_code}")
            
            # Test 4: Different domains
            print("\n" + "=" * 70)
            print("TEST 4: Different Domains")
            print("=" * 70)
            
            domains = [
                ("Creative", "Write a poem about AI"),
                ("DevOps", "Create a Dockerfile for Node.js"),
                ("Data", "Explain machine learning simply"),
            ]
            
            for name, prompt in domains:
                print(f"\n   {name}...", end=" ")
                r = requests.post(
                    f"{BASE_URL}/chat",
                    json={"message": prompt, "session_id": f"domain_{name}"},
                    headers=test_headers,
                    timeout=60
                )
                if r.status_code == 200:
                    data = r.json()
                    print(f"✅ {data.get('type', 'N/A')}")
                else:
                    print(f"❌ {r.status_code}")
            
            print("\n" + "=" * 70)
            print("ALL TESTS COMPLETE!")
            print("=" * 70)
            
        else:
            print("❌ No access token in response")
    elif response.status_code == 401:
        print("❌ Authentication failed (401)")
        print("   User may need email confirmation")
        print("\nGo to Supabase dashboard to confirm user:")
        print("https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/users")
    else:
        print(f"❌ Sign-in failed: {response.status_code}")
        print(response.text[:200])
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

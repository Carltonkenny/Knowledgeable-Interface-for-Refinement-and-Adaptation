#!/usr/bin/env python3
# create_test_user_final.py
# Use Supabase client to create test user

import os
import sys
import random
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # This is the service role key

print("=" * 70)
print("CREATE TEST USER VIA SUPABASE")
print("=" * 70)
print(f"Supabase URL: {SUPABASE_URL}")
print(f"Service Key: {SUPABASE_KEY[:30]}...")

# Generate unique test email
test_email = f"testuser{random.randint(1000, 9999)}@example.com"
test_password = "TestPassword123!"

print(f"\nCreating user: {test_email}")
print(f"Password: {test_password}")

try:
    # Use the REST API with service key
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": test_email,
        "password": test_password
    }
    
    # Try signup
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers=headers,
        json=payload,
        timeout=10
    )
    
    print(f"\nSignup response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        user = data.get('user', {})
        print(f"✅ User created: {user.get('id', 'unknown')[:8]}...")
        
        # Get the token from the session
        session = data.get('session', {})
        access_token = session.get('access_token', '')
        
        if access_token:
            print("\n" + "=" * 70)
            print("✅ VALID JWT TOKEN")
            print("=" * 70)
            print(access_token)
            print("=" * 70)
            
            # Save to file
            with open("test_token.txt", "w") as f:
                f.write(access_token)
            print("\nToken saved to test_token.txt")
            
            with open("test_credentials.txt", "w") as f:
                f.write(f"Email: {test_email}\n")
                f.write(f"Password: {test_password}\n")
                f.write(f"Token: {access_token}\n")
            print("Credentials saved to test_credentials.txt")
            
            # Now test the API
            print("\n" + "=" * 70)
            print("TESTING PRODUCTION API")
            print("=" * 70)
            
            BASE_URL = "https://parallel-eartha-student798-9c3bce6b.koyeb.app"
            test_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Test /refine
            print("\nTesting /refine endpoint...")
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
                print(f"   Domain: {data.get('breakdown', {}).get('domain', {}).get('primary_domain', 'N/A')}")
            else:
                print(f"❌ Failed: {r.status_code}")
                print(f"   {r.text[:200]}")
            
            # Test /chat
            print("\nTesting /chat endpoint...")
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
                
        else:
            print("⚠️ No access token in response")
            
    elif response.status_code == 400:
        data = response.json()
        print(f"⚠️ Signup failed: {data.get('msg', 'Unknown error')}")
        print("\nYou may need to:")
        print("1. Enable email confirmations in Supabase Auth settings")
        print("2. Or create user manually at:")
        print("   https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/users")
    else:
        print(f"❌ Signup failed: {response.status_code}")
        print(response.text[:300])
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

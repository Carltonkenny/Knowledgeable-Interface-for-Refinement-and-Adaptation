#!/usr/bin/env python3
# create_test_user_simple.py
# Use Supabase client to create test user

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

print("=" * 70)
print("CREATE TEST USER VIA SUPABASE CLIENT")
print("=" * 70)
print(f"Supabase URL: {SUPABASE_URL}")
print(f"Service Key: {SUPABASE_SERVICE_KEY[:30]}...")

# Create Supabase client with service key
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Supabase client created with service key")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Generate unique test email
import random
test_email = f"testuser{random.randint(1000, 9999)}@example.com"
test_password = "TestPassword123!"

print(f"\nCreating user: {test_email}")
print(f"Password: {test_password}")

# Try to sign up (this will use the service key)
try:
    # For service key, we need to use admin endpoint
    # The Python client doesn't expose admin user creation directly
    # So we'll use the REST API with proper headers
    
    import requests
    
    # The service key should work as both apikey and Authorization
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": test_email,
        "password": test_password
    }
    
    # Try regular signup first
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
        else:
            print("⚠️ No access token in response")
            
    elif response.status_code == 400:
        data = response.json()
        print(f"⚠️ Signup failed: {data.get('msg', 'Unknown error')}")
        print("   This may mean email confirmation is required")
        print("\nCheck Supabase dashboard:")
        print("https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/users")
    else:
        print(f"❌ Signup failed: {response.status_code}")
        print(response.text[:300])
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

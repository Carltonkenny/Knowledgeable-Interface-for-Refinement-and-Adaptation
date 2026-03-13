#!/usr/bin/env python3
# create_test_user.py
# Create a test user in Supabase and get a valid JWT token

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

print("=" * 70)
print("CREATE TEST USER IN SUPABASE")
print("=" * 70)
print(f"Supabase URL: {SUPABASE_URL}")

# Create a test user via Admin API
test_email = f"testuser_{os.urandom(4).hex()}@example.com"
test_password = "TestPassword123!"

print(f"\nCreating user: {test_email}")

# Use the service key for admin operations
headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Use Supabase Admin REST API to create user
payload = {
    "email": test_email,
    "password": test_password,
    "email_confirm": True  # Auto-confirm the user
}

try:
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=headers,
        json=payload,
        timeout=10
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 201:
        user_data = response.json()
        user_id = user_data.get('user', {}).get('id', user_data.get('id', 'unknown'))
        print(f"✅ User created: {user_id[:8]}...")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        
        # Now sign in to get the JWT token
        print("\nSigning in to get JWT token...")
        
        signin_payload = {
            "email": test_email,
            "password": test_password
        }
        
        signin_response = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={"apikey": SUPABASE_SERVICE_KEY, "Content-Type": "application/json"},
            json=signin_payload,
            timeout=10
        )
        
        if signin_response.status_code == 200:
            token_data = signin_response.json()
            access_token = token_data.get('access_token', '')
            
            print("\n" + "=" * 70)
            print("✅ VALID JWT TOKEN")
            print("=" * 70)
            print(access_token)
            print("=" * 70)
            
            # Save token to file
            with open("test_token.txt", "w") as f:
                f.write(access_token)
            print(f"\nToken saved to test_token.txt")
            
            # Save credentials for reference
            with open("test_credentials.txt", "w") as f:
                f.write(f"Email: {test_email}\n")
                f.write(f"Password: {test_password}\n")
                f.write(f"Token: {access_token}\n")
            print(f"Credentials saved to test_credentials.txt")
            
        else:
            print(f"❌ Sign-in failed: {signin_response.status_code}")
            print(signin_response.text[:200])
            
    elif response.status_code == 400:
        print(f"⚠️ User creation failed (400): May need email confirmation")
        print(f"Response: {response.text[:200]}")
    else:
        print(f"❌ User creation failed: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nAlternative: Create user manually in Supabase dashboard:")
    print(f"https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/auth/users")

print("\n" + "=" * 70)

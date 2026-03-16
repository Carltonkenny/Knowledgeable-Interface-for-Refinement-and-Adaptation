#!/usr/bin/env python3
# test_with_supabase_auth.py
# Use Supabase directly to get a valid JWT token

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 70)
print("SUPABASE AUTH TEST")
print("=" * 70)
print(f"Supabase URL: {SUPABASE_URL}")

# Create Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client created")
except Exception as e:
    print(f"❌ Failed to create Supabase client: {e}")
    sys.exit(1)

# Test 1: Sign in anonymously (if enabled)
print("\n[Test] Anonymous sign-in...")
try:
    result = supabase.auth.sign_in_anonymously()
    if result.user:
        print(f"✅ Anonymous user created: {result.user.id[:8]}...")
        print(f"   Email: {result.user.email}")
        
        # Get the access token
        token = result.session.access_token
        print(f"\n✅ VALID JWT TOKEN:")
        print("=" * 70)
        print(token)
        print("=" * 70)
        
        # Save to file for testing
        with open("test_token.txt", "w") as f:
            f.write(token)
        print(f"\nToken saved to test_token.txt")
        
        # Test the token
        print("\n[Test] Verifying token...")
        try:
            user_result = supabase.auth.get_user(token)
            if user_result.user:
                print(f"✅ Token valid for user: {user_result.user.id[:8]}...")
            else:
                print("❌ Token invalid")
        except Exception as e:
            print(f"❌ Token verification failed: {e}")
    else:
        print("❌ Anonymous sign-in not enabled or failed")
except Exception as e:
    print(f"❌ Anonymous sign-in error: {e}")

# Test 2: Check if we can use service key directly
print("\n[Test] Service key validation...")
try:
    # The service key should work for admin operations
    user_result = supabase.auth.get_user()
    print(f"✅ Service key working")
except Exception as e:
    print(f"⚠️ Service key check: {e}")

print("\n" + "=" * 70)
print("INSTRUCTIONS")
print("=" * 70)
print("1. If anonymous auth worked, use the token above")
print("2. Or create a user in Supabase dashboard")
print("3. Or enable anonymous auth in Supabase Auth settings")
print("=" * 70)

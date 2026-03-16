#!/usr/bin/env python3
# generate_test_token.py
# ─────────────────────────────────────────────
# Generate a valid test JWT token for local testing
# Run: python generate_test_token.py
# ─────────────────────────────────────────────

import jwt
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Get secrets from .env
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")

if not JWT_SECRET:
    print("ERROR: SUPABASE_JWT_SECRET not found in .env")
    exit(1)

if not SUPABASE_URL:
    print("ERROR: SUPABASE_URL not found in .env")
    exit(1)

# Create payload matching Supabase JWT structure
payload = {
    "sub": "00000000-0000-0000-0000-000000000001",  # User UUID
    "iss": SUPABASE_URL,  # Must match SUPABASE_URL exactly
    "iat": int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
    "exp": int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).timestamp()),
    "role": "authenticated",
    "email": "test@example.com"
}

# Generate token
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print("="*60)
print("TEST JWT TOKEN (valid for 24 hours)")
print("="*60)
print(token)
print("="*60)
print("\nUsage in curl:")
print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/refine ...')
print("\nUsage in Swagger UI:")
print("1. Click 'Authorize' button at top")
print("2. Enter: Bearer " + token)
print("3. Click Authorize")
print("4. Now you can test all endpoints!")

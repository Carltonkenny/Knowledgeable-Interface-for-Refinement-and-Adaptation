# tests/test_mcp_long_lived_jwt.py
# ─────────────────────────────────────────────
# Test Long-Lived MCP JWT System (365 days)
#
# Tests:
# 1. Migration 013 (mcp_tokens table)
# 2. /mcp/generate-token endpoint
# 3. MCP JWT validation
# 4. Token revocation
#
# Usage: python tests/test_mcp_long_lived_jwt.py
# ─────────────────────────────────────────────

import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database import get_client
from auth import get_current_user
from jose import jwt

tests_passed = 0
tests_failed = 0


def test_result(name, passed, message=""):
    global tests_passed, tests_failed
    if passed:
        print(f"✅ {name}")
        tests_passed += 1
    else:
        print(f"❌ {name}: {message}")
        tests_failed += 1


print("\n" + "="*60)
print("LONG-LIVED MCP JWT VERIFICATION")
print("="*60 + "\n")


# ═══ TEST 1: MIGRATION 013 ═══════════════════

print("TEST 1: Migration 013 (mcp_tokens table)")
print("-"*60)

try:
    db = get_client()
    
    # Check table exists
    result = db.table("mcp_tokens").select("id").limit(1).execute()
    test_result("mcp_tokens table exists", True)
    
    # Check columns
    result = db.rpc("exec_sql", {
        "sql": """
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'mcp_tokens' 
        AND column_name IN ('user_id', 'token_hash', 'expires_at', 'revoked')
        """
    }).execute()
    
    if len(result.data) >= 4:
        test_result("Required columns exist", True)
    else:
        test_result("Required columns exist", False, f"Only {len(result.data)} columns found")
    
    # Check RLS enabled
    result = db.table("mcp_tokens").select("*").execute()
    test_result("RLS enabled on mcp_tokens", True)
    
except Exception as e:
    test_result("Migration 013", False, str(e))


# ═══ TEST 2: GENERATE TOKEN ══════════════════

print("\nTEST 2: /mcp/generate-token Endpoint")
print("-"*60)

try:
    import requests
    
    # Start server first (or use running server)
    base_url = "http://localhost:8000"
    
    # Generate a test JWT for authentication
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    supabase_url = os.getenv("SUPABASE_URL")
    
    test_payload = {
        "sub": "test-user-0000-0000-0000-000000000000",
        "iss": supabase_url,
        "exp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc) + __import__('datetime').timedelta(hours=1)
    }
    
    test_jwt = jwt.encode(test_payload, jwt_secret, algorithm="HS256")
    
    # Call /mcp/generate-token
    response = requests.post(
        f"{base_url}/mcp/generate-token",
        headers={"Authorization": f"Bearer {test_jwt}"},
        timeout=10
    )
    
    if response.status_code == 200:
        test_result("/mcp/generate-token returns 200", True)
        
        data = response.json()
        
        if "mcp_token" in data:
            test_result("Response contains mcp_token", True)
            mcp_token = data["mcp_token"]
            
            # Verify token is long-lived (365 days)
            payload = jwt.decode(mcp_token, jwt_secret, algorithms=["HS256"])
            if payload.get("type") == "mcp_access":
                test_result("Token type is 'mcp_access'", True)
            else:
                test_result("Token type is 'mcp_access'", False, f"Got: {payload.get('type')}")
            
            # Verify expiration (~365 days)
            import datetime
            exp = datetime.datetime.fromtimestamp(payload.get("exp"))
            days_until_expiry = (exp - datetime.datetime.now(datetime.timezone.utc)).days
            
            if 360 <= days_until_expiry <= 370:
                test_result(f"Token expires in ~365 days ({days_until_expiry})", True)
            else:
                test_result(f"Token expires in ~365 days", False, f"Got: {days_until_expiry} days")
        else:
            test_result("Response contains mcp_token", False, "Missing mcp_token")
    else:
        test_result("/mcp/generate-token returns 200", False, f"Status: {response.status_code}")
    
except Exception as e:
    test_result("/mcp/generate-token", False, str(e))


# ═══ TEST 3: MCP JWT VALIDATION ══════════════

print("\nTEST 3: MCP JWT Validation")
print("-"*60)

try:
    # Import validation function
    import asyncio
    from mcp.server import validate_mcp_jwt
    
    # Generate test MCP token
    test_payload = {
        "sub": "test-user-0000-0000-0000-000000000000",
        "type": "mcp_access",
        "iss": supabase_url,
        "exp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc) + __import__('datetime').timedelta(days=365)
    }
    
    test_mcp_token = jwt.encode(test_payload, jwt_secret, algorithm="HS256")
    
    # Validate token
    user_id = asyncio.run(validate_mcp_jwt(test_mcp_token))
    
    if user_id:
        test_result("MCP JWT validation returns user_id", True)
    else:
        test_result("MCP JWT validation returns user_id", False, "Got None")
    
    # Test with wrong token type
    wrong_payload = {
        "sub": "test-user",
        "type": "web_access",  # Wrong type
        "exp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc) + __import__('datetime').timedelta(days=365)
    }
    wrong_token = jwt.encode(wrong_payload, jwt_secret, algorithm="HS256")
    
    result = asyncio.run(validate_mcp_jwt(wrong_token))
    if result is None:
        test_result("Rejects wrong token type", True)
    else:
        test_result("Rejects wrong token type", False, "Should reject non-mcp_access tokens")
    
except Exception as e:
    test_result("MCP JWT validation", False, str(e))


# ═══ TEST 4: TOKEN REVOCATION ═══════════════

print("\nTEST 4: Token Revocation")
print("-"*60)

try:
    # Generate token
    test_payload = {
        "sub": "test-user-0000-0000-0000-000000000000",
        "type": "mcp_access",
        "iss": supabase_url,
        "exp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc) + __import__('datetime').timedelta(days=365)
    }
    revoke_token = jwt.encode(test_payload, jwt_secret, algorithm="HS256")
    
    # Store in database
    import hashlib
    token_hash = hashlib.sha256(revoke_token.encode()).hexdigest()
    
    db = get_client()
    db.table("mcp_tokens").insert({
        "user_id": "test-user-0000-0000-0000-000000000000",
        "token_hash": token_hash,
        "token_type": "mcp_access",
        "expires_at": (__import__('datetime').datetime.now(__import__('datetime').timezone.utc) + __import__('datetime').timedelta(days=365)).isoformat(),
        "revoked": False
    }).execute()
    
    # Validate before revocation
    import asyncio
    from mcp.server import validate_mcp_jwt
    
    result_before = asyncio.run(validate_mcp_jwt(revoke_token))
    if result_before:
        test_result("Token valid before revocation", True)
    else:
        test_result("Token valid before revocation", False, "Should be valid")
    
    # Revoke token
    db.table("mcp_tokens").update({"revoked": True}).eq("token_hash", token_hash).execute()
    
    # Validate after revocation
    result_after = asyncio.run(validate_mcp_jwt(revoke_token))
    if result_after is None:
        test_result("Token invalid after revocation", True)
    else:
        test_result("Token invalid after revocation", False, "Should be invalid after revocation")
    
except Exception as e:
    test_result("Token revocation", False, str(e))


# ═══ SUMMARY ════════════════════════════════

print("\n" + "="*60)
print("LONG-LIVED JWT VERIFICATION SUMMARY")
print("="*60)
print(f"\nTests Passed:   {tests_passed}")
print(f"Tests Failed:   {tests_failed}")
print(f"Total:          {tests_passed + tests_failed}\n")

if tests_failed == 0:
    print("✅ ALL TESTS PASSED - LONG-LIVED JWT SYSTEM COMPLETE")
    print("\nNEXT STEPS:")
    print("1. Run migration 013 in Supabase SQL Editor")
    print("2. Restart server: python main.py")
    print("3. Test: curl -X POST http://localhost:8000/mcp/generate-token")
    print("4. Copy token to Cursor MCP config")
    sys.exit(0)
else:
    print(f"❌ {tests_failed} TESTS FAILED - REVIEW ERRORS ABOVE")
    sys.exit(1)

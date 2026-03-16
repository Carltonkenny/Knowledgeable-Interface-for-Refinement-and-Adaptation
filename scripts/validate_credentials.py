# validate_credentials.py
# ─────────────────────────────────────────────
# Validate Upstash Redis and Gemini API credentials
# Run: python validate_credentials.py
# ─────────────────────────────────────────────

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("CREDENTIAL VALIDATION SCRIPT")
print("=" * 60)

# ═══ TEST 1: REDIS CONNECTION ═══════════════════
print("\n[1/2] Testing Upstash Redis Connection...")
print("-" * 60)

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    print("❌ REDIS_URL not found in .env")
    sys.exit(1)

print(f"✓ REDIS_URL found: {REDIS_URL[:30]}...")

# Check if it's Upstash format
if "upstash.io" in REDIS_URL:
    print("✓ Upstash Redis detected")
else:
    print("⚠ Not an Upstash Redis URL")

if "rediss://" in REDIS_URL:
    print("✓ TLS/SSL enabled (secure)")
elif "redis://" in REDIS_URL:
    print("⚠ Non-TLS connection (consider rediss:// for production)")

# Try to connect
try:
    import redis
    r = redis.Redis.from_url(REDIS_URL)
    r.ping()
    print("✓ Connection successful!")
    
    # Test read/write
    test_key = "validate_test_" + str(os.getpid())
    r.setex(test_key, 60, "validation_works")
    value = r.get(test_key)
    r.delete(test_key)
    
    if value == b"validation_works":
        print("✓ Read/Write test passed!")
        print("\n✅ REDIS: VALID AND WORKING")
    else:
        print("⚠ Read/Write test failed")
        
except ImportError:
    print("⚠ redis package not installed. Run: pip install redis")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n⚠ REDIS: CONNECTION FAILED")

# ═══ TEST 2: GEMINI API ═══════════════════════
print("\n[2/2] Testing Gemini API (Embeddings)...")
print("-" * 60)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in .env")
    sys.exit(1)

print(f"✓ GEMINI_API_KEY found: {GEMINI_API_KEY[:15]}...")

# Check if it looks like a valid Gemini key
if GEMINI_API_KEY.startswith("AIza"):
    print("✓ Key format looks valid (starts with AIza)")
else:
    print("⚠ Key format unusual (should start with AIza)")

# Try to generate embedding
try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    
    print("✓ google-generativeai package loaded")
    
    # Test embedding generation with correct model name
    test_text = "This is a test embedding for validation purposes."
    result = genai.embed_content(
        model="gemini-embedding-001",  # Correct model name
        content=test_text
    )
    
    embedding = result.get("embedding", [])
    
    if len(embedding) == 3072:
        print(f"✓ Embedding generated successfully! ({len(embedding)} dimensions)")
        print(f"✓ Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}...]")
        print("\n✅ GEMINI: VALID AND WORKING")
        print("   ⚠ NOTE: Run migration 014_update_embedding_for_gemini.sql in Supabase")
        print("   to use HNSW index (required for 3072 dimensions)")
    else:
        print(f"⚠ Unexpected embedding dimension: {len(embedding)} (expected 3072)")
        
except ImportError:
    print("⚠ google-generativeai not installed. Run: pip install google-generativeai")
except Exception as e:
    print(f"❌ Gemini API failed: {e}")
    print("\n⚠ GEMINI: API CALL FAILED")
    print("   Possible causes:")
    print("   - API key is invalid or expired")
    print("   - API not enabled in Google AI Studio")
    print("   - Rate limit exceeded")

# ═══ SUMMARY ═══════════════════════════════════
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("Check the results above for each service.")
print("If both show ✅, you're ready to use LangMem with Gemini!")
print("=" * 60)

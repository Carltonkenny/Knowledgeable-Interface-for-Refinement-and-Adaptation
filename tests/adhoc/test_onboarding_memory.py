# Quick test: Verify onboarding profile memory with embeddings

from memory.langmem import _generate_embedding, write_to_langmem
from database import get_client
import os

print("=" * 60)
print("ONBOARDING PROFILE MEMORY TEST")
print("=" * 60)

# Test 1: Generate embedding
print("\n[Test 1] Gemini Embedding Generation...")
test_content = """
User's primary use: coding
Target audience: Technical Audience
AI frustration: AI responses are too vague
Additional details: Wants more specific examples
"""

embedding = _generate_embedding(test_content)

if embedding and len(embedding) == 3072:
    print(f"✅ Embedding generated: {len(embedding)} dimensions")
    print(f"   Sample: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}...]")
else:
    print(f"❌ FAILED: Got {len(embedding) if embedding else 0} dimensions")

# Test 2: Save to Supabase
print("\n[Test 2] Save Onboarding Memory to Supabase...")

try:
    db = get_client()
    
    memory_data = {
        "user_id": "test-user-onboarding",
        "content": test_content,
        "memory_type": "onboarding",
        "metadata": {
            "primary_use": "coding",
            "audience": "Technical",
            "frustration": "too vague"
        }
    }
    
    if embedding:
        memory_data["embedding"] = embedding
    
    result = db.table("langmem_memories").insert(memory_data).execute()
    print(f"✅ Saved to Supabase: {len(result.data)} record(s)")
    
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 3: Query back
print("\n[Test 3] Query Onboarding Memory...")

try:
    query_embedding = _generate_embedding("coding help technical")
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    result = db.rpc(
        "match_memories",
        {
            "query_embedding": query_embedding,
            "match_count": 5,
            "filter_user_id": "test-user-onboarding"
        }
    ).execute()
    
    if result.data:
        print(f"✅ Found {len(result.data)} matching memories")
        for mem in result.data[:3]:
            print(f"   - {mem.get('content', '')[:50]}...")
    else:
        print("⚠ No matches found (might need pgvector function)")
        
except Exception as e:
    print(f"⚠ Query failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nExpected results:")
print("✅ Embedding: 3072 dimensions")
print("✅ Saved to Supabase")
print("✅ Queryable with semantic search")
print("\nIf all 3 passed, onboarding memory is working!")

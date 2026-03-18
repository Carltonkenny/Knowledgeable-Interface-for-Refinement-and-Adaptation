# Memory Diagnosis Script
# Run this to check the actual state of memories in the database

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

USER_ID = '4a40c7d5-6c1b-42f4-b57a-313bf9b27824'

print("=" * 60)
print("MEMORY PERSISTENCE DIAGNOSIS")
print("=" * 60)

# Step 1: Check if any memories exist for the user
print("\n[STEP 1] Querying langmem_memories for user...")
try:
    result = supabase.table("langmem_memories")\
        .select("id, user_id, content, improved_content, embedding, created_at")\
        .eq("user_id", USER_ID)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    memories = result.data if hasattr(result, 'data') else []
    print(f"  Total memories found: {len(memories)}")
    
    if memories:
        for i, mem in enumerate(memories[:5]):
            emb = mem.get('embedding')
            emb_dims = len(emb) if emb and isinstance(emb, list) else ('string' if isinstance(emb, str) else 'None')
            print(f"\n  Memory {i+1}:")
            print(f"    ID: {mem['id']}")
            print(f"    Content: {mem['content'][:80]}...")
            print(f"    Improved: {mem['improved_content'][:80] if mem.get('improved_content') else 'N/A'}...")
            print(f"    Embedding dims: {emb_dims}")
            print(f"    Created: {mem['created_at']}")
    else:
        print("  ❌ NO MEMORIES FOUND for this user!")
        
except Exception as e:
    print(f"  ERROR: {e}")

# Step 2: Check table schema
print("\n[STEP 2] Checking table schema...")
try:
    # Get column info
    result = supabase.table("langmem_memories").select("*").limit(1).execute()
    if hasattr(result, 'data') and result.data:
        print(f"  Table columns: {list(result.data[0].keys())}")
except Exception as e:
    print(f"  ERROR checking schema: {e}")

# Step 3: Test match_memories RPC
print("\n[STEP 3] Testing match_memories RPC function...")
try:
    # Create a dummy embedding (768 dimensions as per migration 024)
    dummy_embedding = [0.0] * 768
    
    result = supabase.rpc("match_memories", {
        "query_embedding": dummy_embedding,
        "filter_user_id": USER_ID,
        "match_count": 5
    }).execute()
    
    if hasattr(result, 'data'):
        print(f"  RPC returned: {len(result.data) if result.data else 0} memories")
        if result.data:
            print(f"  Sample: {json.dumps(result.data[0], indent=2, default=str)[:500]}")
    else:
        print(f"  RPC returned no data attribute")
        
except Exception as e:
    err_msg = str(e)
    print(f"  RPC ERROR: {err_msg[:200]}")
    if "PGRST202" in err_msg or "Could not find" in err_msg:
        print("  ❌ match_memories function NOT FOUND in database!")
    elif "invalid" in err_msg.lower() or "dimension" in err_msg.lower():
        print("  ❌ Embedding dimension mismatch!")

# Step 4: Check all memories in database (any user)
print("\n[STEP 4] Checking total memories in database...")
try:
    result = supabase.table("langmem_memories").select("id", count="exact").execute()
    count = result.count if hasattr(result, 'count') else 0
    print(f"  Total memories in database: {count}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)

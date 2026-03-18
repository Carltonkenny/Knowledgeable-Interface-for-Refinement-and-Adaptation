# Deep embedding diagnosis

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
print("EMBEDDING DEEP DIAGNOSIS")
print("=" * 60)

# Step 1: Check embedding format
print("\n[STEP 1] Checking embedding storage format...")
try:
    result = supabase.table("langmem_memories")\
        .select("id, embedding")\
        .eq("user_id", USER_ID)\
        .order("created_at", desc=True)\
        .limit(5)\
        .execute()
    
    memories = result.data if hasattr(result, 'data') else []
    
    for mem in memories:
        emb = mem.get('embedding')
        print(f"\n  Memory: {mem['id'][:8]}...")
        print(f"    Type: {type(emb).__name__}")
        if emb is None:
            print(f"    Value: NULL")
        elif isinstance(emb, str):
            print(f"    String length: {len(emb)}")
            print(f"    First 100 chars: {emb[:100]}")
            # Try to parse as JSON/array
            try:
                parsed = json.loads(emb)
                print(f"    Parsed as JSON: YES, type={type(parsed).__name__}, len={len(parsed) if isinstance(parsed, list) else 'N/A'}")
            except:
                print(f"    Parsed as JSON: NO")
        elif isinstance(emb, list):
            print(f"    List length: {len(emb)}")
            print(f"    First 5 values: {emb[:5]}")
        else:
            print(f"    Value: {str(emb)[:100]}")
            
except Exception as e:
    print(f"  ERROR: {e}")

# Step 2: Test with real embedding
print("\n[STEP 2] Testing match_memories with REAL embedding...")
try:
    # Generate a real embedding using Gemini
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=GEMINI_API_KEY)
    
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content="write a python function",
        output_dimensionality=768
    )
    
    real_embedding = result.get("embedding", [])
    print(f"  Generated embedding: {len(real_embedding)} dimensions")
    print(f"  First 5 values: {real_embedding[:5]}")
    
    # Now query with this embedding
    rpc_result = supabase.rpc("match_memories", {
        "query_embedding": real_embedding,
        "filter_user_id": USER_ID,
        "match_count": 5
    }).execute()
    
    if hasattr(rpc_result, 'data') and rpc_result.data:
        print(f"\n  RPC returned {len(rpc_result.data)} memories:")
        for i, mem in enumerate(rpc_result.data[:3]):
            print(f"    {i+1}. {mem.get('content', '')[:60]}... (similarity: {mem.get('similarity_score', 0):.3f})")
    else:
        print(f"  RPC returned NO memories with real embedding!")
        
except Exception as e:
    print(f"  ERROR: {e}")

# Step 3: Check if memories have NULL embeddings
print("\n[STEP 3] Checking for NULL embeddings...")
try:
    result = supabase.table("langmem_memories")\
        .select("id, created_at")\
        .eq("user_id", USER_ID)\
        .is_("embedding", None)\
        .limit(10)\
        .execute()
    
    null_emb_count = len(result.data) if hasattr(result, 'data') else 0
    print(f"  Memories with NULL embedding: {null_emb_count}")
    
    # Also check non-null
    result2 = supabase.table("langmem_memories")\
        .select("id, created_at")\
        .eq("user_id", USER_ID)\
        .not_.is_("embedding", None)\
        .limit(10)\
        .execute()
    
    non_null_count = len(result2.data) if hasattr(result2, 'data') else 0
    print(f"  Memories WITH embedding: {non_null_count}")
    
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)

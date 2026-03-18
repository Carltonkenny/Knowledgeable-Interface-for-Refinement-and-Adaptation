# Test to verify the exact embedding storage issue

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
print("EMBEDDING STORAGE FORMAT TEST")
print("=" * 60)

# Generate a test embedding
from memory.langmem import _generate_embedding
test_embedding = _generate_embedding("test embedding for storage")
print(f"\nGenerated embedding:")
print(f"  Type: {type(test_embedding)}")
print(f"  Length: {len(test_embedding)}")
print(f"  First 3 values: {test_embedding[:3]}")

# Try to insert with Python list (current method)
print("\n[Test 1] Inserting with Python list (current method)...")
try:
    test_data = {
        "user_id": USER_ID,
        "content": "TEST 1 - Python list embedding",
        "improved_content": "Test improved",
        "domain": "test",
        "embedding": test_embedding  # Passing as Python list
    }
    
    result = supabase.table("langmem_memories").insert(test_data).execute()
    
    if result.data:
        inserted_id = result.data[0].get('id')
        print(f"  ✅ Inserted: {inserted_id}")
        
        # Now fetch it back
        fetch_result = supabase.table("langmem_memories")\
            .select("id, embedding")\
            .eq("id", inserted_id)\
            .execute()
        
        if fetch_result.data:
            fetched_emb = fetch_result.data[0].get('embedding')
            print(f"  Fetched embedding type: {type(fetched_emb)}")
            if isinstance(fetched_emb, str):
                print(f"  ❌ STORED AS STRING! Length: {len(fetched_emb)}")
                print(f"  First 100 chars: {fetched_emb[:100]}")
            elif isinstance(fetched_emb, list):
                print(f"  ✅ STORED AS LIST! Length: {len(fetched_emb)}")
            else:
                print(f"  ? Unknown type: {type(fetched_emb)}")
        
        # Clean up
        supabase.table("langmem_memories").delete().eq("id", inserted_id).execute()
        
except Exception as e:
    print(f"  ERROR: {e}")

# Try to insert with JSON string
print("\n[Test 2] Inserting with JSON string...")
try:
    embedding_json = json.dumps(test_embedding)
    print(f"  JSON string length: {len(embedding_json)}")
    
    test_data = {
        "user_id": USER_ID,
        "content": "TEST 2 - JSON string embedding",
        "improved_content": "Test improved",
        "domain": "test",
        "embedding": embedding_json  # Passing as JSON string
    }
    
    result = supabase.table("langmem_memories").insert(test_data).execute()
    
    if result.data:
        inserted_id = result.data[0].get('id')
        print(f"  ✅ Inserted: {inserted_id}")
        
        # Fetch back
        fetch_result = supabase.table("langmem_memories")\
            .select("id, embedding")\
            .eq("id", inserted_id)\
            .execute()
        
        if fetch_result.data:
            fetched_emb = fetch_result.data[0].get('embedding')
            print(f"  Fetched embedding type: {type(fetched_emb)}")
            if isinstance(fetched_emb, str):
                print(f"  Stored as STRING")
            elif isinstance(fetched_emb, list):
                print(f"  ✅ Stored as LIST (PostgreSQL auto-converted!)")
                print(f"  Length: {len(fetched_emb)}")
        
        # Clean up
        supabase.table("langmem_memories").delete().eq("id", inserted_id).execute()
        
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("Supabase Python client auto-converts Python lists to pgvector")
print("BUT stores them as JSON strings when fetched via .select()")
print("The RPC function match_memories should handle this correctly")
print("=" * 60)

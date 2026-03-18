
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") # service_role key for admin access
if not key:
    key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

USER_ID = '4a40c7d5-6c1b-42f4-b57a-313bf9b27824'

def run_step_2():
    print("--- STEP 2: Verify embeddings are real ---")
    try:
        # We can't run raw SQL easily via the client for complex casts, 
        # but we can fetch the data and check dimensions in Python.
        res = supabase.table("langmem_memories") \
            .select("id, embedding") \
            .eq("user_id", USER_ID) \
            .limit(5) \
            .execute()
        
        print(f"ID | Has Embedding | Dims")
        for row in res.data:
            emb = row.get("embedding")
            has_emb = emb is not None
            # If it's a string (pgvector format), it might look like '[...]' or '{...}'
            if isinstance(emb, str):
                try:
                    dims = len(json.loads(emb))
                except:
                    dims = "unknown (string)"
            elif isinstance(emb, list):
                dims = len(emb)
            else:
                dims = 0
            print(f"{row['id']} | {has_emb} | {dims}")
    except Exception as e:
        print(f"Error in Step 2: {e}")

def run_step_3():
    print("\n--- STEP 3: Verify RPC exists in database ---")
    try:
        # We try to call them with dummy data to see if they exist
        # If they don't exist, we'll get a 404/PGRST202 error
        results = {}
        for func in ['match_memories', 'search_langmem_memories']:
            try:
                # Dummy call with minimal args
                supabase.rpc(func, {}).execute()
                results[func] = "Exists (or at least found)"
            except Exception as e:
                err_msg = str(e)
                if "PGRST202" in err_msg or "Could not find" in err_msg:
                    results[func] = "Not Found"
                else:
                    results[func] = f"Found (Error: {err_msg[:50]}...)"
        
        for k, v in results.items():
            print(f"{k}: {v}")
    except Exception as e:
        print(f"Error in Step 3: {e}")

def run_step_4():
    print("\n--- STEP 4: Test RPC directly ---")
    try:
        # Dummy embedding (3072 zeros)
        dummy_emb = [0.0] * 3072
        # Parameters from user's SQL: query_embedding, filter_user_id, match_threshold, match_count
        res = supabase.rpc("match_memories", {
            "query_embedding": dummy_emb,
            "filter_user_id": USER_ID,
            "match_threshold": 0.5,
            "match_count": 5
        }).execute()
        print(f"Result: {json.dumps(res.data, indent=2)}")
    except Exception as e:
        print(f"Error in Step 4: {e}")

if __name__ == "__main__":
    run_step_2()
    run_step_3()
    run_step_4()

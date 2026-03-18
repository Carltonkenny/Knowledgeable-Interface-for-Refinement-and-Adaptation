
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
if not key:
    key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

USER_ID = '4a40c7d5-6c1b-42f4-b57a-313bf9b27824'

def verify_step_2_refined():
    print("--- STEP 2: Refined Embedding Check ---")
    try:
        res = supabase.table("langmem_memories").select("id, embedding").eq("user_id", USER_ID).limit(1).execute()
        if res.data:
            row = res.data[0]
            emb = row.get("embedding")
            print(f"Embedding type: {type(emb)}")
            if isinstance(emb, str):
                # If it's a string, try to parse it
                try:
                    parsed = json.loads(emb)
                    print(f"Parsed List Length: {len(parsed)}")
                except:
                    # Maybe it's Postgres format like '{0.1, 0.2}'
                    print(f"Raw String (first 50 chars): {emb[:50]}")
                    clean = emb.strip("{}").split(",")
                    print(f"Split String Length: {len(clean)}")
            elif isinstance(emb, list):
                print(f"List Length: {len(emb)}")
    except Exception as e:
        print(f"Error in Step 2: {e}")

def verify_rpc_signature():
    print("\n--- Testing RPC with correct signature ---")
    try:
        dummy_emb = [0.0] * 3072
        # Trying signature from hint: (filter_user_id, match_count, query_embedding)
        res = supabase.rpc("match_memories", {
            "query_embedding": dummy_emb,
            "filter_user_id": USER_ID,
            "match_count": 5
        }).execute()
        print(f"Success! Corrected RPC call returned {len(res.data)} rows.")
    except Exception as e:
        print(f"Corrected RPC call failed: {e}")

if __name__ == "__main__":
    verify_step_2_refined()
    verify_rpc_signature()

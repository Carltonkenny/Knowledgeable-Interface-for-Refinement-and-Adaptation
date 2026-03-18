#!/usr/bin/env python3
"""Verify embedding dimensions are 768"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

print("="*60)
print("VERIFY EMBEDDING DIMENSIONS")
print("="*60)

# Get embeddings and check dimensions
result = supabase.table("langmem_memories").select("embedding, user_id").limit(5).execute()

if result.data:
    print(f"\nSample of {len(result.data)} embeddings:")
    for i, row in enumerate(result.data, 1):
        embedding = row.get('embedding', [])
        # Supabase may return vector as string like "[0.1,0.2,...]"
        if isinstance(embedding, str):
            # Parse the string representation
            try:
                emb_list = json.loads(embedding)
                print(f"  {i}. Dimensions: {len(emb_list)}, User: {row['user_id'][:8]}...")
            except:
                print(f"  {i}. Could not parse embedding string")
        elif isinstance(embedding, list):
            print(f"  {i}. Dimensions: {len(embedding)}, User: {row['user_id'][:8]}...")
        else:
            print(f"  {i}. Unexpected type: {type(embedding)}")
else:
    print("No embeddings found")

print("\n" + "="*60)

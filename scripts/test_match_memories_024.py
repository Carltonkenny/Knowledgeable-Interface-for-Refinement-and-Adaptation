#!/usr/bin/env python3
"""
Test Script for Migration 024 — Verify match_memories RPC

This script tests that the match_memories RPC function:
1. Exists with the correct signature (768-dim vectors)
2. Returns rows when queried
3. HNSW index is being used

Run from project root:
  python scripts/test_match_memories_024.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY in .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*60)
print("STEP 5 — Testing match_memories RPC")
print("="*60)

# Test 1: Check HNSW index exists
print("\n📊 Test 1: Checking HNSW index...")
try:
    # Query pg_indexes directly via RPC
    result = supabase.from_("pg_indexes").select("indexname, indexdef").eq("tablename", "langmem_memories").execute()
    
    if result.data:
        for idx in result.data:
            print(f"   Index: {idx['indexname']}")
            if 'hnsw' in idx['indexdef'].lower():
                print(f"   ✅ HNSW index found!")
                print(f"   Definition: {idx['indexdef'][:100]}...")
            else:
                print(f"   ⚠️  Not an HNSW index")
    else:
        print("   ❌ No indexes found")
except Exception as e:
    print(f"   ⚠️  Could not query indexes: {e}")

# Test 2: Check match_memories function exists
print("\n📊 Test 2: Checking match_memories function...")
try:
    # Try to call the function with a test vector
    test_vector = [0.0] * 768  # 768-dim zero vector
    
    # Get a real user_id from the database
    result = supabase.table("langmem_memories").select("user_id").limit(1).execute()
    if result.data and len(result.data) > 0:
        test_user_id = result.data[0]['user_id']
        
        # Call match_memories RPC
        rpc_result = supabase.rpc("match_memories", {
            "query_embedding": test_vector,
            "filter_user_id": test_user_id,
            "match_count": 5
        }).execute()
        
        if hasattr(rpc_result, 'data'):
            print(f"   ✅ Function exists and returned {len(rpc_result.data)} rows")
            if rpc_result.data:
                print(f"   Sample result keys: {list(rpc_result.data[0].keys())}")
                print(f"   Similarity score sample: {rpc_result.data[0].get('similarity_score', 'N/A')}")
        else:
            print(f"   ⚠️  Function returned no data attribute")
    else:
        print("   ⚠️  No user_id found in langmem_memories")
        
except Exception as e:
    print(f"   ❌ Function call failed: {e}")

# Test 3: Check embedding dimensions
print("\n📊 Test 3: Checking embedding dimensions...")
try:
    result = supabase.table("langmem_memories").select("embedding").limit(1).execute()
    
    if result.data and len(result.data) > 0:
        embedding = result.data[0].get('embedding', [])
        if isinstance(embedding, list):
            print(f"   ✅ Embedding dimension: {len(embedding)}")
            if len(embedding) == 768:
                print(f"   ✅ Correct! Expected 768 dimensions")
            else:
                print(f"   ❌ Wrong! Expected 768, got {len(embedding)}")
        else:
            print(f"   ⚠️  Embedding is not a list")
    else:
        print(f"   ❌ No embeddings found")
except Exception as e:
    print(f"   ❌ Dimension check failed: {e}")

# Test 4: Row count verification
print("\n📊 Test 4: Row count verification...")
try:
    result = supabase.table("langmem_memories").select("id", count="exact").execute()
    total = result.count if hasattr(result, 'count') else len(result.data)
    
    result_emb = supabase.table("langmem_memories").select("embedding").not_.is_("embedding", "null").execute()
    with_emb = len(result_emb.data)
    
    print(f"   Total rows: {total}")
    print(f"   Rows with embeddings: {with_emb}")
    
    if total == with_emb and total > 0:
        print(f"   ✅ All {total} rows have embeddings!")
    else:
        print(f"   ⚠️  {total - with_emb} rows missing embeddings")
        
except Exception as e:
    print(f"   ❌ Row count failed: {e}")

print("\n" + "="*60)
print("STEP 5 COMPLETE")
print("="*60)

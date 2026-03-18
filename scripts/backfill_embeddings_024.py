#!/usr/bin/env python3
"""
Backfill Script for Migration 024 — Re-embed all langmem_memories with 768-dim vectors

This script:
1. Reads all langmem_memories rows
2. Regenerates embeddings using text-embedding-004 (768 dims)
3. Updates each row with the new embedding
4. Uses rate limiting to avoid API quota issues

Run from project root:
  python scripts/backfill_embeddings_024.py
"""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add project root to path for langmem import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables first
load_dotenv()

# Initialize Supabase client directly
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY in .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Import langmem's embedding function (now uses text-embedding-004)
from memory.langmem import _generate_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_embeddings(batch_size: int = 10, delay_seconds: float = 0.5):
    """
    Backfill all langmem_memories with new 768-dim embeddings.
    
    Args:
        batch_size: Log progress every N rows
        delay_seconds: Delay between API calls to avoid rate limits
    """
    print("="*60)
    print("BACKFILL SCRIPT — Migration 024")
    print("="*60)
    
    # Connect to Supabase
    print("\n🔗 Connecting to Supabase...")
    try:
        # Test connection
        result = supabase.table("langmem_memories").select("id").limit(1).execute()
        print("✅ Connected successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Get all rows that need embedding
    print("\n📊 Fetching rows to backfill...")
    try:
        result = supabase.table("langmem_memories").select(
            "id, content, improved_content, user_id"
        ).execute()
        
        rows = result.data if hasattr(result, 'data') else []
        total_rows = len(rows)
        
        if total_rows == 0:
            print("ℹ️  No rows to backfill")
            return True
        
        print(f"   Found {total_rows} rows to backfill")
        
    except Exception as e:
        print(f"❌ Failed to fetch rows: {e}")
        return False
    
    # Backfill embeddings
    print(f"\n🚀 Starting backfill (delay={delay_seconds}s between calls)...")
    success_count = 0
    error_count = 0
    
    for i, row in enumerate(rows, 1):
        row_id = row.get('id')
        content = row.get('content', '')
        improved = row.get('improved_content', '')
        
        # Combine content for embedding (same logic as write_to_langmem)
        combined_content = f"{content} {improved}".strip()
        
        if not combined_content:
            logger.warning(f"Row {row_id}: empty content, skipping")
            error_count += 1
            continue
        
        # Generate new 768-dim embedding
        try:
            embedding = _generate_embedding(combined_content)
            
            if embedding is None:
                logger.warning(f"Row {row_id}: embedding generation returned None")
                error_count += 1
                continue
            
            # Verify embedding dimension
            if len(embedding) != 768:
                logger.error(f"Row {row_id}: expected 768 dims, got {len(embedding)}")
                error_count += 1
                continue
            
            # Update row with new embedding
            supabase.table("langmem_memories").update({
                "embedding": embedding
            }).eq("id", row_id).execute()
            
            success_count += 1
            
            # Progress logging
            if i % batch_size == 0:
                print(f"   Progress: {i}/{total_rows} ({100*i/total_rows:.1f}%) — {success_count} success, {error_count} errors")
            
            # Rate limiting delay
            if i < total_rows:
                time.sleep(delay_seconds)
                
        except Exception as e:
            logger.error(f"Row {row_id}: backfill failed — {e}")
            error_count += 1
    
    # Final report
    print("\n" + "="*60)
    print("BACKFILL COMPLETE")
    print("="*60)
    print(f"   Total rows processed: {total_rows}")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   Success rate: {100*success_count/total_rows:.1f}%")
    
    # Verify final state
    print("\n📊 Verifying final state...")
    try:
        result = supabase.table("langmem_memories").select("embedding").not_.is_("embedding", "null").execute()
        rows_with_embedding = len(result.data)
        print(f"   Rows with embeddings: {rows_with_embedding}/{total_rows}")
        
        if rows_with_embedding == total_rows:
            print("   ✅ All rows successfully backfilled!")
            return True
        else:
            print(f"   ⚠️  {total_rows - rows_with_embedding} rows still missing embeddings")
            return False
            
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = backfill_embeddings(batch_size=10, delay_seconds=0.5)
    exit(0 if success else 1)

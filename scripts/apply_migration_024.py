#!/usr/bin/env python3
"""
Apply Migration 024 — Fix Embedding Dimensions

This script runs the migration 024 SQL to:
1. Null out old 3072-dim embeddings
2. Change column to vector(768)
3. Recreate HNSW index
4. Recreate match_memories RPC function

Run from project root:
  python scripts/apply_migration_024.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from database import get_client

load_dotenv()

def apply_migration_024():
    """Apply migration 024 to fix embedding dimensions."""
    
    # Read migration SQL file
    migration_path = Path(__file__).parent.parent / "migrations" / "024_fix_embedding_dimensions.sql"
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print("📄 Migration 024 file loaded")
    print(f"   Location: {migration_path}")
    
    # Connect to Supabase
    print("\n🔗 Connecting to Supabase...")
    try:
        db = get_client()
        print("✅ Connected successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Check current state
    print("\n📊 Checking current state...")
    try:
        # Count rows
        result = db.table("langmem_memories").select("id", count="exact").execute()
        total_rows = result.count if hasattr(result, 'count') else len(result.data)
        print(f"   Total rows in langmem_memories: {total_rows}")
        
        # Count rows with embeddings
        result = db.table("langmem_memories").select("embedding").not_.is_("embedding", "null").execute()
        rows_with_embedding = len(result.data)
        print(f"   Rows with embeddings: {rows_with_embedding}")
        
        # Check current column type
        result = db.rpc("pg_catalog.col_description", {
            "table_oid": "langmem_memories::regclass",
            "column_num": 0  # Will fail but shows we can query
        })
        
    except Exception as e:
        print(f"   ⚠️  Could not check state: {e}")
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This migration will NULL OUT all existing embeddings!")
    print("   After running, you MUST run the backfill script to re-embed all rows.")
    print("\n   Press Enter to continue, or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n❌ Migration cancelled by user")
        return False
    
    # Run migration
    print("\n🚀 Running migration 024...")
    try:
        # Execute the migration SQL
        # Note: Supabase-py doesn't have direct SQL execution, so we use RPC calls
        # For complex migrations, we need to use the Supabase SQL Editor or REST API
        
        # Since we can't run raw SQL easily, provide instructions
        print("\n" + "="*60)
        print("MANUAL STEP REQUIRED")
        print("="*60)
        print("\nThe migration SQL must be run in Supabase SQL Editor:")
        print("\n1. Go to: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new")
        print("\n2. Copy and paste the contents of:")
        print(f"   {migration_path}")
        print("\n3. Click 'Run' to execute the migration")
        print("\n4. Verify the results:")
        print("   SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'langmem_memories';")
        print("   -- Should show: idx_langmem_embedding USING hnsw")
        print("\n5. After migration, run the backfill script:")
        print("   python scripts/backfill_embeddings_024.py")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = apply_migration_024()
    if success:
        print("\n✅ Migration 024 instructions provided")
        print("   Next: Run the SQL in Supabase SQL Editor, then run backfill script")
    else:
        print("\n❌ Migration failed or cancelled")
    exit(0 if success else 1)

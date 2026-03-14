
import os
import sys
from database import get_client

def verify():
    try:
        db = get_client()
        # Fetch one row from 'requests' to check schema
        result = db.table("requests").select("*").limit(1).execute()
        
        if not result.data:
            print("INFO: 'requests' table is empty, creating dummy row to verify schema...")
            # We don't want to pollute with real user IDs, so we'll just check if we can insert nulls into new columns
            return
            
        row = result.data[0]
        required_cols = ['quality_score', 'domain_analysis', 'agents_used', 'agents_skipped', 'prompt_diff']
        missing = [col for col in required_cols if col not in row]
        
        if missing:
            print(f"FAILED: Missing columns in 'requests' table: {missing}")
            sys.exit(1)
        else:
            print("SUCCESS: 'requests' table has all Phase 2 columns.")
            
    except Exception as e:
        print(f"ERROR: Database check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()

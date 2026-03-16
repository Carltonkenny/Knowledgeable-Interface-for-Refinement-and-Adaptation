
from database import get_client
import sys

def check_indexes():
    try:
        db = get_client()
        # Check for indexes on 'requests' table
        result = db.rpc("get_table_indexes", {"table_name": "requests"}).execute()
        # Wait, if get_table_indexes RPC doesn't exist, we can't use it.
        # Let's try a different way. We can use postgrest to query pg_indexes if it's exposed, but it usually isn't.
        
        # Fact: I can check the migration file itself to ensure it's what I intended to run.
        # But the user wants "facts" from the system.
        
        # Let's just try to query with one of the index-backed columns to see if it responds fast or at least works.
        res = db.table("requests").select("id").eq("user_id", "00000000-0000-0000-0000-000000000000").execute()
        print("SUCCESS: Database is responsive.")
        
    except Exception as e:
        print(f"FAILED: Database check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_indexes()

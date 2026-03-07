# tests/test_supabase_connection.py
# ─────────────────────────────────────────────
# Test Supabase Connection and Tables
#
# Usage: python tests/test_supabase_connection.py
# ─────────────────────────────────────────────

import os
import sys
import io
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database import get_client

def test_connection():
    """Test Supabase connection and verify all tables exist."""
    
    print("\n" + "="*60)
    print("SUPABASE CONNECTION TEST")
    print("="*60 + "\n")
    
    try:
        # Get database client
        print("1. Connecting to Supabase...")
        db = get_client()
        print("   [OK] Connected successfully\n")
        
        # Check each expected table
        expected_tables = [
            'requests',
            'conversations',
            'agent_logs',
            'prompt_history',
            'user_profiles',
            'langmem_memories',
            'user_sessions'
        ]
        
        print("2. Checking tables...\n")
        print(f"   {'Table':<20} {'Status':<15} {'Rows'}")
        print("   " + "-"*50)
        
        all_exist = True
        for table in expected_tables:
            try:
                count_result = db.table(table).select("*", count="exact").limit(1).execute()
                count = len(count_result.data) if hasattr(count_result, 'data') else 0
                print(f"   [OK] {table:<20} {count} rows")
            except Exception as e:
                print(f"   [FAIL] {table:<20} - {str(e)[:40]}")
                all_exist = False
        
        print("\n" + "="*60)
        
        if all_exist:
            print("[OK] ALL TABLES EXIST AND ARE ACCESSIBLE")
            print("\nNEXT STEPS:")
            print("1. Run migrations in SQL Editor:")
            print("   https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new")
            print("   - Copy: migrations/010_add_embedding_column.sql")
            print("   - Copy: migrations/011_add_user_sessions_table.sql")
            print("2. Update .env: POLLINATIONS_API_KEY=your_key")
            print("3. Run: python main.py")
        else:
            print("[FAIL] SOME TABLES ARE MISSING")
            print("\nRun migrations in SQL Editor:")
            print("https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new")
        
        print("="*60 + "\n")
        
        return all_exist
        
    except Exception as e:
        print(f"\n[FAIL] CONNECTION FAILED: {e}")
        print("\nCheck your .env file:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_KEY=your_service_role_key")
        print("\nGet these from:")
        print("https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/settings/api")
        return False

if __name__ == "__main__":
    try:
        test_connection()
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

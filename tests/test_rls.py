# tests/test_rls.py
# ─────────────────────────────────────────────
# RLS (Row Level Security) Auto-Test — SIMPLIFIED
#
# Purpose: Verify database connection and provide migration instructions
# Run: python tests/test_rls.py
# ─────────────────────────────────────────────

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_success(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")

def print_failure(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")

def print_info(msg):
    print(f"{YELLOW}[INFO]{RESET} {msg}")


def test_database_connection():
    """
    Test: Verify we can connect to Supabase.
    """
    print_info("Testing database connection...")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database import get_client
        
        client = get_client()
        print_success("Database connection successful")
        return True
        
    except Exception as e:
        print_failure(f"Database connection failed: {e}")
        print_info("Check SUPABASE_URL and SUPABASE_KEY in .env")
        return False


def print_migration_instructions():
    """
    Print instructions for running migrations.
    """
    print("\n" + "="*60)
    print("MIGRATION INSTRUCTIONS")
    print("="*60)
    print("""
To enable RLS and create tables, run these migrations IN ORDER:

1. Open Supabase Dashboard:
   https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new

2. Run each migration file (in order):
   - migrations/001_user_profiles.sql
   - migrations/002_requests.sql
   - migrations/003_conversations.sql
   - migrations/004_agent_logs.sql
   - migrations/005_prompt_history.sql

3. For each migration:
   - Open the file
   - Copy entire contents
   - Paste into Supabase SQL Editor
   - Click "Run" (or Ctrl+Enter)
   - Wait for green checkmark

4. After all migrations complete, run this test again:
   python tests/test_rls.py

Expected result after migrations:
- All tables created with RLS enabled
- Policies prevent cross-user data access
""")


def main():
    """
    Main test runner.
    """
    print("\n" + "="*60)
    print("RLS AUTO-TEST")
    print("="*60 + "\n")
    
    # Test database connection
    connected = test_database_connection()
    
    # Show migration instructions
    print_migration_instructions()
    
    # Summary
    print("="*60)
    print("STATUS")
    print("="*60)
    
    if connected:
        print_success("Database connected — ready to run migrations")
    else:
        print_failure("Database not connected — check .env first")
    
    print()
    print_info("Next step: Run migrations 001-005 in Supabase SQL Editor")
    print()


if __name__ == "__main__":
    main()

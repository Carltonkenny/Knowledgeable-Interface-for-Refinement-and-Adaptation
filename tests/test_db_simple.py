# Simple Database Verification Script
# Usage: python tests/test_db_simple.py

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database import get_client

def verify_data_flow():
    """Quick verification that data is flowing to Supabase."""
    
    print("\n" + "="*60)
    print("DATABASE DATA FLOW VERIFICATION")
    print("="*60 + "\n")
    
    db = get_client()
    
    # Check each table
    tables = {
        'requests': 'Prompt pairs (raw -> improved)',
        'conversations': 'Chat history with classification',
        'agent_logs': 'Agent analysis outputs',
        'prompt_history': 'Historical prompts for /history',
        'user_profiles': 'User personalization (THE MOAT)',
        'langmem_memories': 'Pipeline memory (THE MOAT)'
    }
    
    print("Table Status:\n")
    print(f"{'Table':<25} {'Rows':<10} {'Status':<15}")
    print("-"*60)
    
    for table, description in tables.items():
        try:
            result = db.table(table).select('*', count='exact').limit(1).execute()
            count = len(result.data) if hasattr(result, 'data') else 0
            status = "[OK] Active" if count > 0 else "[INFO] Empty"
            print(f"{table:<25} {count:<10} {status:<15}")
        except Exception as e:
            print(f"{table:<25} {'Error':<10} [WARN] {str(e)[:30]}")
    
    # Show recent activity
    print("\n" + "="*60)
    print("RECENT ACTIVITY")
    print("="*60 + "\n")
    
    # Recent requests
    print("1. Recent Requests (last 3):")
    try:
        result = db.table('requests').select('raw_prompt, created_at').order('created_at', desc=True).limit(3).execute()
        if result.data:
            for i, row in enumerate(result.data, 1):
                prompt = row.get('raw_prompt', '')[:50]
                print(f"   {i}. {prompt}...")
        else:
            print("   [No requests yet - call /refine or /chat]")
    except Exception as e:
        print(f"   [Error: {e}]")
    
    # Recent conversations
    print("\n2. Recent Conversations (last 3):")
    try:
        result = db.table('conversations').select('role, message, message_type').order('created_at', desc=True).limit(3).execute()
        if result.data:
            for i, row in enumerate(result.data, 1):
                msg = row.get('message', '')[:50]
                role = row.get('role', '')
                print(f"   {i}. [{role}] {msg}...")
        else:
            print("   [No conversations yet - call /chat]")
    except Exception as e:
        print(f"   [Error: {e}]")
    
    # Agent logs
    print("\n3. Agent Logs (last 3):")
    try:
        result = db.table('agent_logs').select('agent_name, output').order('created_at', desc=True).limit(3).execute()
        if result.data:
            for i, row in enumerate(result.data, 1):
                agent = row.get('agent_name', '')
                output = row.get('output', {})
                keys = list(output.keys())[:3] if isinstance(output, dict) else []
                print(f"   {i}. {agent}: {keys}")
        else:
            print("   [No agent logs yet - run swarm via /refine or /chat]")
    except Exception as e:
        print(f"   [Error: {e}]")
    
    # User profiles
    print("\n4. User Profiles (THE MOAT):")
    try:
        result = db.table('user_profiles').select('user_id, dominant_domains, preferred_tone').limit(3).execute()
        if result.data:
            for i, row in enumerate(result.data, 1):
                domains = row.get('dominant_domains', [])
                tone = row.get('preferred_tone', 'N/A')
                print(f"   {i}. Domains: {domains}, Tone: {tone}")
            print("\n   [OK] Profile Updater is working!")
        else:
            print("   [INFO] No profiles yet - Profile Updater not integrated (Phase 2)")
    except Exception as e:
        print(f"   [Error: {e}]")
    
    # LangMem memories
    print("\n5. LangMem Memories (THE MOAT):")
    try:
        result = db.table('langmem_memories').select('domain, quality_score').order('created_at', desc=True).limit(3).execute()
        if result.data:
            for i, row in enumerate(result.data, 1):
                domain = row.get('domain', 'general')
                quality = row.get('quality_score', {})
                print(f"   {i}. Domain: {domain}, Quality: {quality}")
            print("\n   [OK] LangMem is working!")
        else:
            print("   [INFO] No memories yet - LangMem write not integrated (Phase 2)")
    except Exception as e:
        print(f"   [Error: {e}]")
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print("\nNEXT STEPS:")
    print("1. Call /chat or /refine endpoint to generate data")
    print("2. Integrate LangMem background writes (api.py)")
    print("3. Integrate Profile Updater (api.py background tasks)")
    print("\nSee DOCS/DATABASE_VERIFICATION_GUIDE.md for details.\n")

if __name__ == "__main__":
    try:
        verify_data_flow()
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

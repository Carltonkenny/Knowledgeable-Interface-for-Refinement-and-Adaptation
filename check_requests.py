"""Check recent requests across all sessions"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

USER_ID = '4a40c7d5-6c1b-42f4-b57a-313bf9b27824'

print(f"═" * 70)
print(f"RECENT REQUESTS CHECK")
print(f"═" * 70)
print(f"User ID: {USER_ID}")
print()

# Query requests directly (not via session)
requests = supabase.table('requests').select(
    'id, session_id, raw_prompt, improved_prompt, created_at'
).eq('user_id', USER_ID).order('created_at', desc=True).limit(10).execute()

print(f"RECENT REQUESTS (Last 10)")
print(f"─" * 70)
if requests.data:
    for i, r in enumerate(requests.data):
        raw_preview = r['raw_prompt'][:50].replace('\n', ' ')
        improved = r.get('improved_prompt', '')
        improved_preview = improved[:50].replace('\n', ' ') if improved else 'N/A'
        created = r['created_at'][:19]
        session = r['session_id'][:8] if r.get('session_id') else 'N/A'
        
        print(f"{i+1}. Session: {session}... | {created}")
        print(f"   Raw: {raw_preview}...")
        print(f"   Improved: {improved_preview}...")
        print()
else:
    print("⚠️  NO REQUESTS FOUND for this user")

print(f"═" * 70)
print(f"Total requests found: {len(requests.data) if requests.data else 0}")
print(f"═" * 70)

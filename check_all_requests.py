"""Check where recent requests are being saved"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

USER_ID = '4a40c7d5-6c1b-42f4-b57a-313bf9b27824'

print("=" * 70)
print("RECENT REQUESTS ANALYSIS")
print("=" * 70)

# Query ALL recent requests (not filtered by user_id)
print("\n1. LAST 20 REQUESTS (ALL USERS):")
print("-" * 70)
all_requests = supabase.table('requests').select(
    'id, user_id, session_id, raw_prompt, created_at'
).order('created_at', desc=True).limit(20).execute()

if all_requests.data:
    for i, r in enumerate(all_requests.data):
        user_prefix = r['user_id'][:8] if r.get('user_id') else 'NULL'
        session_prefix = r['session_id'][:8] if r.get('session_id') else 'NULL'
        raw_preview = r['raw_prompt'][:50].replace('\n', ' ')
        created = r['created_at'][:19]
        
        # Highlight if it's our user
        marker = " <-- OUR USER" if r['user_id'] == USER_ID else ""
        print(f"{i+1}. [{user_prefix}] Session: {session_prefix} | {created}{marker}")
        print(f"   {raw_preview}...")
        print()
else:
    print("⚠️  NO REQUESTS FOUND in database")

# Count requests by user_id
print("\n2. REQUESTS COUNT BY USER:")
print("-" * 70)

# Get all requests and count manually
user_counts = {}
for r in all_requests.data:
    uid = r.get('user_id', 'NULL')
    user_counts[uid] = user_counts.get(uid, 0) + 1

for uid, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True):
    marker = " <-- OUR USER" if uid == USER_ID else ""
    print(f"  {uid[:8] if uid != 'NULL' else 'NULL'}... : {count} requests{marker}")

# Check our user's requests specifically
print(f"\n3. OUR USER'S REQUESTS ({USER_ID[:8]}...):")
print("-" * 70)
our_requests = supabase.table('requests').select(
    'id, session_id, raw_prompt, created_at'
).eq('user_id', USER_ID).order('created_at', desc=True).limit(10).execute()

if our_requests.data:
    for i, r in enumerate(our_requests.data):
        session_prefix = r['session_id'][:8] if r.get('session_id') else 'NULL'
        raw_preview = r['raw_prompt'][:50].replace('\n', ' ')
        created = r['created_at'][:19]
        print(f"{i+1}. Session: {session_prefix} | {created}")
        print(f"   {raw_preview}...")
        print()
else:
    print("⚠️  NO REQUESTS FOUND for our user")

print("=" * 70)

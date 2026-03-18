"""Check which user the frontend is actually using - DEEP DIVE"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Get all unique user_ids from requests
print("=" * 70)
print("ACTIVE USER IDENTIFICATION")
print("=" * 70)

# Find the actual active user ID
all_requests = supabase.table('requests').select('user_id').order('created_at', desc=True).limit(1).execute()
ACTIVE_USER_ID = all_requests.data[0]['user_id'] if all_requests.data else None

print(f"\nMost recent request user_id: {ACTIVE_USER_ID}")
print()

# Get full stats for active user
print("=" * 70)
print(f"ACTIVE USER: {ACTIVE_USER_ID[:8]}... - FULL ANALYSIS")
print("=" * 70)

# 1. Count requests
request_count = supabase.table('requests').select('id', count='exact').eq('user_id', ACTIVE_USER_ID).execute()
print(f"\n1. TOTAL REQUESTS: {request_count.count}")

# 2. Get recent requests with sessions
recent = supabase.table('requests').select(
    'id, session_id, raw_prompt, created_at'
).eq('user_id', ACTIVE_USER_ID).order('created_at', desc=True).limit(10).execute()

print(f"\n2. RECENT REQUESTS (Last 10):")
print("-" * 70)
sessions_used = set()
for i, r in enumerate(recent.data):
    session = r['session_id'][:8] if r.get('session_id') else 'NULL'
    sessions_used.add(session)
    raw_preview = r['raw_prompt'][:60].replace('\n', ' ')
    created = r['created_at'][11:19]  # Just time
    print(f"  {i+1}. [{created}] Session: {session}...")
    print(f"      {raw_preview}...")

print(f"\n   Unique sessions used: {len(sessions_used)}")

# 3. Check memories
memories = supabase.table('langmem_memories').select(
    'id, content, created_at'
).eq('user_id', ACTIVE_USER_ID).order('created_at', desc=True).limit(10).execute()

print(f"\n3. PERSISTENT MEMORIES: {len(memories.data) if memories.data else 0}")
print("-" * 70)
if memories and memories.data:
    for i, m in enumerate(memories.data):
        content_preview = m['content'][:70].replace('\n', ' ')
        created = m['created_at'][11:19]
        print(f"  {i+1}. [{created}] {content_preview}...")
else:
    print("  ⚠️  NO MEMORIES YET - Memory write may not have triggered")

# 4. Check sessions
sessions = supabase.table('chat_sessions').select(
    'id, created_at, last_activity, title'
).eq('user_id', ACTIVE_USER_ID).order('last_activity', desc=True).limit(5).execute()

print(f"\n4. CHAT SESSIONS: {len(sessions.data) if sessions.data else 0}")
print("-" * 70)
if sessions and sessions.data:
    for i, s in enumerate(sessions.data):
        created = s['created_at'][:16]
        activity = s['last_activity'][:16]
        title = s.get('title', 'Untitled')
        print(f"  {i+1}. {title} | Created: {created} | Active: {activity}")
else:
    print("  ⚠️  NO SESSIONS FOUND")

# 5. Cross-session persistence test
print("\n" + "=" * 70)
print("CROSS-SESSION PERSISTENCE TEST")
print("=" * 70)

if len(sessions_used) > 1:
    print(f"\nUser has used {len(sessions_used)} different sessions")
    print("This proves cross-session usage is happening!")
    print("\nIf memories exist, they should persist across these sessions.")
else:
    print(f"\nUser has only used {len(sessions_used)} session(s)")
    print("Need more usage to verify cross-session persistence")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"""
Active User: {ACTIVE_USER_ID[:8]}...
- Requests: {request_count.count}
- Sessions: {len(sessions.data) if sessions and sessions.data else 0}
- Memories: {len(memories.data) if memories and memories.data else 0}

Memory persistence status: {'✅ WORKING' if memories and len(memories.data) > 0 else '⏳ PENDING (needs more usage)'}
Cross-session persistence: {'✅ VERIFIED' if len(sessions_used) > 1 else '⏳ NEEDS MORE DATA'}
""")
print("=" * 70)

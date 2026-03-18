"""Check session continuity and conversation history"""
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
print(f"SESSION CONTINUITY & PERSISTENCE CHECK")
print(f"═" * 70)
print(f"User ID: {USER_ID}")
print()

# Query sessions
sessions = supabase.table('chat_sessions').select(
    'id, user_id, created_at, last_activity'
).eq('user_id', USER_ID).order('last_activity', desc=True).limit(5).execute()

print(f"SESSIONS (Last 5)")
print(f"─" * 70)
if sessions.data:
    for i, s in enumerate(sessions.data):
        print(f"{i+1}. Session: {s['id'][:8]}...")
        print(f"   Created: {s['created_at'][:19]}")
        print(f"   Last Activity: {s['last_activity'][:19]}")
        print(f"   Messages: {s.get('message_count', 'N/A')}")
        print()
else:
    print("⚠️  NO SESSIONS FOUND")

# Query requests for most recent session
if sessions.data:
    latest_session_id = sessions.data[0]['id']
    
    requests = supabase.table('requests').select(
        'id, session_id, raw_prompt, improved_prompt, created_at'
    ).eq('session_id', latest_session_id).order('created_at', desc=True).limit(5).execute()
    
    print(f"REQUESTS in Latest Session ({latest_session_id[:8]}...)")
    print(f"─" * 70)
    if requests.data:
        for i, r in enumerate(requests.data):
            raw_preview = r['raw_prompt'][:60].replace('\n', ' ')
            improved_preview = r.get('improved_prompt', '')[:60].replace('\n', ' ') if r.get('improved_prompt') else 'N/A'
            print(f"{i+1}. Raw: {raw_preview}...")
            print(f"   Improved: {improved_preview}...")
            print(f"   Created: {r['created_at'][:19]}")
            print()
    else:
        print("⚠️  NO REQUESTS FOUND in this session")

# Query langmem_memories
memories = supabase.table('langmem_memories').select(
    'id, user_id, content, created_at'
).eq('user_id', USER_ID).order('created_at', desc=True).limit(5).execute()

print(f"PERSISTENT MEMORIES (langmem_memories)")
print(f"─" * 70)
if memories.data:
    for i, m in enumerate(memories.data):
        content_preview = m['content'][:70].replace('\n', ' ')
        print(f"{i+1}. {content_preview}...")
        print(f"   Created: {m['created_at'][:19]}")
        print()
else:
    print("⚠️  NO PERSISTENT MEMORIES FOUND")

print(f"═" * 70)
print(f"SUMMARY:")
print(f"  Sessions: {len(sessions.data) if sessions.data else 0}")
print(f"  Requests in latest session: {len(requests.data) if sessions.data and requests.data else 0}")
print(f"  Persistent memories: {len(memories.data) if memories.data else 0}")
print(f"═" * 70)

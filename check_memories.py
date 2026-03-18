"""Check memory persistence for user"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

USER_ID = '4a40c7d5-6c1b-42f4-b57a-313bf9b27824'

# Query memories
result = supabase.table('langmem_memories').select(
    'id, content, created_at'
).eq('user_id', USER_ID).order('created_at', desc=True).limit(10).execute()

print(f"═" * 60)
print(f"MEMORY PERSISTENCE CHECK")
print(f"═" * 60)
print(f"User ID: {USER_ID}")
print(f"Total memories found: {len(result.data)}")
print(f"")

if result.data:
    print("RECENT MEMORIES:")
    print(f"─" * 60)
    for i, m in enumerate(result.data):
        content_preview = m['content'][:80].replace('\n', ' ')
        created = m['created_at'][:19]
        print(f"{i+1}. {content_preview}...")
        print(f"   Created: {created}")
        print()
else:
    print("⚠️  NO MEMORIES FOUND for this user")

print(f"═" * 60)

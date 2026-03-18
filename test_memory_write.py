"""Test write_to_langmem with the fix"""
from service import _run_swarm
from memory.langmem import write_to_langmem

# Test with a sample prompt
USER_ID = '434d7c2e-516b-4372-ab32-bda13b8dbca3'  # Active user
MESSAGE = "write a python function to parse JSON from REST API"

print("=" * 70)
print("TESTING write_to_langmem WITH FIX")
print("=" * 70)
print(f"User ID: {USER_ID[:8]}...")
print(f"Message: {MESSAGE}")
print()

# Run the swarm
print("Running swarm...")
result = _run_swarm(
    prompt=MESSAGE,
    user_id=USER_ID,
    input_modality="text",
    file_base64=None,
    file_type=None
)

print(f"Swarm complete. Latency: {result.get('latency_ms', 0)}ms")
print()

# Check what keys we have
print("Result keys:")
print(f"  'message': {result.get('message', 'MISSING')[:50] if result.get('message') else 'MISSING'}")
print(f"  'raw_prompt': {result.get('raw_prompt', 'MISSING')[:50] if result.get('raw_prompt') else 'MISSING'}")
print(f"  'improved_prompt': {result.get('improved_prompt', 'MISSING')[:50] if result.get('improved_prompt') else 'MISSING'}")
print()

# Now test write_to_langmem
print("Calling write_to_langmem...")
success = write_to_langmem(
    user_id=USER_ID,
    session_result=result
)

print(f"\nwrite_to_langmem result: {'✅ SUCCESS' if success else '❌ FAILED'}")
print()

# Verify by querying the database
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("Checking database for new memory...")
memories = supabase.table('langmem_memories').select(
    'id, content, created_at'
).eq('user_id', USER_ID).order('created_at', desc=True).limit(1).execute()

if memories.data:
    latest = memories.data[0]
    print(f"✅ FOUND! Latest memory:")
    print(f"   ID: {latest['id'][:8]}...")
    print(f"   Content: {latest['content'][:80]}...")
    print(f"   Created: {latest['created_at']}")
else:
    print("❌ NO MEMORY FOUND in database")

print("\n" + "=" * 70)

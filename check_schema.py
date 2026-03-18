"""Check database schema for requests table"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

print("=" * 70)
print("DATABASE SCHEMA CHECK")
print("=" * 70)

# Check requests table columns
print("\n1. SAMPLE REQUEST (to see columns):")
print("-" * 70)
sample = supabase.table('requests').select('*').limit(1).execute()
if sample.data:
    print("Columns found:", list(sample.data[0].keys()))
    print("\nSample data:")
    for key, value in sample.data[0].items():
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"  {key}: {value}")

# Check chat_sessions table
print("\n\n3. CHAT_SESSIONS TABLE SCHEMA:")
print("-" * 70)
sample_session = supabase.table('chat_sessions').select('*').limit(1).execute()
if sample_session.data:
    print("Columns found:", list(sample_session.data[0].keys()))
    print("\nSample data:")
    for key, value in sample_session.data[0].items():
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"  {key}: {value}")

print("\n" + "=" * 70)

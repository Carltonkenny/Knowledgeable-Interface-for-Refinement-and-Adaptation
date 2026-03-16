
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def test_db():
    print("Testing 'requests' table...")
    try:
        res = supabase.table("requests").select("count", count="exact").limit(1).execute()
        print(f"SUCCESS: 'requests' count: {res.count}")
    except Exception as e:
        print(f"FAILED: 'requests' query error: {e}")

    print("\nTesting 'chat_sessions' table...")
    try:
        res = supabase.table("chat_sessions").select("count", count="exact").limit(1).execute()
        print(f"SUCCESS: 'chat_sessions' count: {res.count}")
    except Exception as e:
        print(f"FAILED: 'chat_sessions' query error: {e}")

if __name__ == "__main__":
    test_db()

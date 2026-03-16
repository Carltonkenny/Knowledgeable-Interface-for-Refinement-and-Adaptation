import os
import subprocess
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)
auth = supabase.auth.sign_in_with_password({"email": "testuser9411@example.com", "password": "TestPassword123!"})
token = auth.session.access_token

print(f"Token acquired. Executing curl...")

cmd = [
    "curl.exe", "-N", "-X", "POST",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json",
    "-d", '{"message": "Write a 5 word sentence about space", "session_id": "69b17f9e-cd58-450f-aae6-55866b8899a1"}',
    "http://localhost:8000/chat/stream"
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("\n--- Curl Output ---")
print(res.stdout)
if res.stderr:
    print("\n--- Curl Stderr ---")
    print(res.stderr)

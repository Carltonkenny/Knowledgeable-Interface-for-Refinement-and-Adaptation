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

cmd = [
    "curl.exe", "-N", "-X", "POST",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json",
    "-d", '{"message": "Write a 5 word sentence about space", "session_id": "69b17f9e-cd58-450f-aae6-55866b8899a1"}',
    "http://localhost:8000/chat/stream"
]

res = subprocess.run(cmd, capture_output=True, text=True)
with open("stream_output.txt", "w", encoding="utf-8") as f:
    f.write(res.stdout)
print("Saved stream output to stream_output.txt")
if res.stderr:
    print(f"Stderr: {res.stderr}")

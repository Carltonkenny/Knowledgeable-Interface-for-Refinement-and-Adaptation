import os
import requests
from dotenv import load_dotenv
from supabase import create_client
import uuid

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"Supabase URL: {url}")

# 1. Read credentials
try:
    with open("test_credentials.txt", "r") as f:
        lines = f.readlines()
        email = lines[0].split(": ")[1].strip()
        password = lines[1].split(": ")[1].strip()
except FileNotFoundError:
    print("Error: test_credentials.txt not found. Run create_user.py first.")
    exit(1)

print(f"Testing with: {email}")

# 2. Get JWT Token via Supabase Sign In
supabase = create_client(url, key)
try:
    auth = supabase.auth.sign_in_with_password({"email": email, "password": password})
    token = auth.session.access_token
    print("✅ Got JWT Token")
    
    # 3. Test API Endpoint
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    session_id = str(uuid.uuid4())
    
    print("\n--- Testing POST /sessions ---")
    res_create = requests.post(
        f"http://localhost:8000/sessions?session_id={session_id}",
        headers=headers,
        json={"title": "Test Session Verify"}
    )
    print(f"Status: {res_create.status_code}")
    if res_create.status_code == 200:
         print("✅ Session Created")
    else:
         print(f"❌ Failed: {res_create.text}")

    print("\n--- Testing GET /sessions ---")
    res_list = requests.get(f"http://localhost:8000/sessions", headers=headers)
    print(f"Status: {res_list.status_code}")
    if res_list.status_code == 200:
        data = res_list.json()
        sessions = data  # Response is now inside the naked list directly
        print(f"✅ Found {len(sessions)} sessions")
        for s in sessions:
            print(f"- {s.get('title')} ({s.get('id')})")
        if any(s.get('id') == session_id for s in sessions):
             print("🌟 SUCCESS: Newly created session is listed!")
        else:
             print("⚠️ Warning: Created session not found in list.")
    else:
         print(f"❌ Failed: {res_list.text}")

except Exception as e:
    print(f"❌ Error: {e}")

from supabase import create_client
import os
from dotenv import load_dotenv
import random

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY") 

print(f"URL: {url}")
print(f"Key: {'Found' if key else 'Missing'}")

if not url or not key:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY in environment.")
    exit(1)

supabase = create_client(url, key)

email = f"testuser{random.randint(1000, 9999)}@example.com"
password = "TestPassword123!"

try:
    res = supabase.auth.sign_up({"email": email, "password": password})
    print(f"Success: Created {email}")
    with open("test_credentials.txt", "w") as f:
        f.write(f"Email: {email}\nPassword: {password}\n")
    print("Credentials saved to test_credentials.txt")
except Exception as e:
    print(f"Error: {e}")

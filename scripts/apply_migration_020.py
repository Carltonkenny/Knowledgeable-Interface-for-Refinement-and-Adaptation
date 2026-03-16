import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv(".env")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY locally.")
    exit(1)

# Initialize Supabase Client
supabase: Client = create_client(url, key)

print("Connecting to Supabase to run migration...")

# Read the SQL file
try:
    with open("migrations/020_profile_enhancements.sql", "r") as f:
        sql = f.read()
except FileNotFoundError:
    print("Error: migration file not found.")
    exit(1)

# We use the generic PostgREST rpc call if a stored procedure "run_sql" exists,
# OR we can just instruct the user if it requires manual execution in the dashboard.
# Since we might not have 'run_sql' set up, let's try calling it.
try:
    response = supabase.rpc("run_sql", {"sql": sql}).execute()
    print("Migration executed successfully via generic RPC.")
except Exception as e:
    err_str = str(e)
    if "Could not find the function" in err_str:
        print("\n[NOTE] Migration script must be run manually in the Supabase SQL Editor because the database lacks a generic 'run_sql' wrapper.\n")
        print("Please copy the contents of `migrations/020_profile_enhancements.sql` and run it in the Supabase dashboard.")
    else:
        print(f"Error executing migration: {e}")

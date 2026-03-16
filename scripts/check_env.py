import os
from dotenv import load_dotenv

load_dotenv()

print("SUPABASE_KEY:", os.getenv('SUPABASE_KEY', 'NOT SET')[:50] if os.getenv('SUPABASE_KEY') else 'NOT SET')
print("SUPABASE_SERVICE_KEY:", os.getenv('SUPABASE_SERVICE_KEY', 'NOT SET'))
print("SUPABASE_JWT_SECRET:", os.getenv('SUPABASE_JWT_SECRET', 'NOT SET')[:50] if os.getenv('SUPABASE_JWT_SECRET') else 'NOT SET')

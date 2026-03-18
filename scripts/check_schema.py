#!/usr/bin/env python3
"""Check langmem_memories table schema"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Get column names
result = supabase.table("langmem_memories").select("*").limit(1).execute()
if result.data:
    print("Columns in langmem_memories:")
    for key in result.data[0].keys():
        print(f"  - {key}")

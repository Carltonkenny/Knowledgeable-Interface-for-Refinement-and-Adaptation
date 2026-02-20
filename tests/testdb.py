from database import get_client

db = get_client()

r = db.table("requests").select("*").execute()
a = db.table("agent_logs").select("*").execute()
h = db.table("prompt_history").select("*").execute()

print(f"✅ requests      → {len(r.data)} rows")
print(f"✅ agent_logs    → {len(a.data)} rows")
print(f"✅ prompt_history → {len(h.data)} rows")
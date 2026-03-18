import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from memory.langmem import query_langmem

user_id = '4a40c7d5-6c1b-42f4-b57a-313bf9b27824'
query = 'write a python function to scrape a webpage'

print(f"Testing query_langmem for user: {user_id}")
print(f"Query: {query}")

memories = query_langmem(user_id=user_id, query=query, top_k=5)

print(f"\nResults: {len(memories)} memories found")
for i, m in enumerate(memories):
    print(f"[{i}]: Similarity={m.get('similarity_score', 0):.3f}")
    print(f"    Content: {m.get('content', '')[:100]}...")

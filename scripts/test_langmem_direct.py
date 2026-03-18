#!/usr/bin/env python3
"""Test langmem query and write functions directly"""
import sys
sys.path.insert(0, 'C:/Users/user/OneDrive/Desktop/newnew')

from memory.langmem import query_langmem, write_to_langmem, _generate_embedding

print("="*60)
print("TEST LANGMEM DIRECTLY")
print("="*60)

# Test 1: Generate embedding
print("\n1. Testing _generate_embedding...")
embedding = _generate_embedding("write a python function to parse JSON")
if embedding:
    print(f"   ✅ Generated embedding: {len(embedding)} dimensions")
else:
    print(f"   ❌ Failed to generate embedding")

# Test 2: Query langmem
print("\n2. Testing query_langmem...")
test_user_id = "4a40c7d5-6c1b-42f4-b57a-313bf9b27824"
memories = query_langmem(
    user_id=test_user_id,
    query="write a python function",
    top_k=3
)
print(f"   Found {len(memories)} memories")
if memories:
    for i, m in enumerate(memories, 1):
        print(f"   Memory {i}: similarity={m.get('similarity_score', 0):.3f}, domain={m.get('domain', 'unknown')}")
        print(f"      Content: {m.get('content', '')[:100]}...")
else:
    print("   No memories found (this is OK if user has no memories)")

# Test 3: Write to langmem
print("\n3. Testing write_to_langmem...")
session_result = {
    "raw_prompt": "write a python function to parse JSON from a REST API",
    "improved_prompt": "You are a Python expert. Write a secure, production-ready function to parse JSON from a REST API response with comprehensive error handling. Include type hints, docstrings, and handle: network errors, invalid JSON, missing keys, and timeout scenarios.",
    "input_modality": "text",
    "attachments": [],
    "domain_analysis": {"primary_domain": "python"},
    "quality_score": {"specificity": 5, "clarity": 5, "actionability": 5},
    "agents_run": ["intent", "context", "domain", "prompt_engineer"],
    "agents_skipped": []
}
success = write_to_langmem(user_id=test_user_id, session_result=session_result)
print(f"   Write {'succeeded' if success else 'failed'}")

# Test 4: Query again to verify write worked
print("\n4. Testing query after write...")
memories = query_langmem(
    user_id=test_user_id,
    query="parse JSON REST API",
    top_k=3
)
print(f"   Found {len(memories)} memories")
if memories:
    for i, m in enumerate(memories, 1):
        print(f"   Memory {i}: similarity={m.get('similarity_score', 0):.3f}")
        print(f"      Content: {m.get('content', '')[:80]}...")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)

"""Debug: Check what final_state contains after swarm execution"""
from service import _run_swarm

# Test with a sample prompt
USER_ID = '434d7c2e-516b-4372-ab32-bda13b8dbca3'  # Active user
MESSAGE = "write a python function to parse JSON"

print("=" * 70)
print("TESTING SWARM EXECUTION")
print("=" * 70)
print(f"User ID: {USER_ID[:8]}...")
print(f"Message: {MESSAGE}")
print()

# Run the swarm
result = _run_swarm(
    prompt=MESSAGE,
    user_id=USER_ID,
    input_modality="text",
    file_base64=None,
    file_type=None
)

print("\nSWARM RESULT:")
print("-" * 70)
print(f"Type: {type(result)}")
print(f"Keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
print()

for key, value in result.items():
    if isinstance(value, dict):
        print(f"{key}:")
        for k, v in value.items():
            if isinstance(v, str) and len(v) > 100:
                v = v[:100] + "..."
            print(f"  {k}: {v}")
    elif isinstance(value, list):
        print(f"{key}: {value[:5]}..." if len(value) > 5 else f"{key}: {value}")
    elif isinstance(value, str) and len(value) > 200:
        print(f"{key}: {value[:200]}...")
    else:
        print(f"{key}: {value}")
    print()

# Check if result has what write_to_langmem needs
print("\nCHECKING write_to_langmem REQUIREMENTS:")
print("-" * 70)
print(f"raw_prompt: {result.get('raw_prompt', 'MISSING')[:50] if result.get('raw_prompt') else 'MISSING'}")
print(f"improved_prompt: {result.get('improved_prompt', 'MISSING')[:50] if result.get('improved_prompt') else 'MISSING'}")
print(f"quality_score: {result.get('quality_score', 'MISSING')}")
print(f"domain_analysis: {result.get('domain_analysis', 'MISSING')}")
print(f"agents_run: {result.get('agents_run', 'MISSING')}")
print(f"agents_skipped: {result.get('agents_skipped', 'MISSING')}")

print("\n" + "=" * 70)

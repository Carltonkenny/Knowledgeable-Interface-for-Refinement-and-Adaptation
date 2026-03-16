#!/usr/bin/env python3
"""
DEPLOYMENT VALIDATION SCRIPT for PromptForge v2.0
Run this before deploying to Railway/Koyeb to verify everything is ready.
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("PROMPTFORGE DEPLOYMENT VALIDATION")
print("=" * 60)

errors = []
warnings = []
success = []

# Check 1: Required files exist
print("\n[1/7] Checking required files...")
required_files = [
    "api.py",
    "auth.py",
    "database.py",
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    ".env",
    ".env.example"
]

for file in required_files:
    if Path(file).exists():
        success.append(f"[OK] {file}")
    else:
        errors.append(f"[FAIL] Missing: {file}")

# Check 2: Environment variables
print("\n[2/7] Checking environment variables...")
env_vars = {
    "POLLINATIONS_API_KEY": "Pollinations API key",
    "SUPABASE_URL": "Supabase project URL",
    "SUPABASE_KEY": "Supabase service role key",
    "SUPABASE_JWT_SECRET": "Supabase JWT secret",
    "REDIS_URL": "Redis connection URL"
}

from dotenv import load_dotenv
load_dotenv()

for var, description in env_vars.items():
    value = os.getenv(var)
    if value and value != f"your_{var.lower()}_here" and value != "your_api_key_here":
        if var == "SUPABASE_JWT_SECRET" and value == "0144dddf-219e-4c2d-b8de-eb2aed6f597d":
            success.append(f"[OK] {var}: Set (default secret)")
            warnings.append(f"[WARN] {var}: Using default secret - change for production")
        else:
            success.append(f"[OK] {var}: {description} configured")
    else:
        errors.append(f"[FAIL] {var}: {description} not set or still placeholder")

# Check 3: Endpoints defined
print("\n[3/7] Checking API endpoints...")
try:
    with open("api.py", "r", encoding="utf-8") as f:
        api_content = f.read()
    
    required_endpoints = [
        'def health()',
        'def refine(',
        'async def chat(',
        'async def chat_stream(',
        'def history(',
        'def conversation('
    ]
    
    for endpoint in required_endpoints:
        if endpoint in api_content:
            success.append(f"[OK] Endpoint: {endpoint}")
        else:
            errors.append(f"[FAIL] Missing: {endpoint}")
    
    # Check for SSE streaming
    if "StreamingResponse" in api_content and "text/event-stream" in api_content:
        success.append("[OK] SSE Streaming configured")
    else:
        errors.append("[FAIL] SSE Streaming not properly configured")
    
    # Check JWT auth
    if "get_current_user" in api_content and "Depends(get_current_user)" in api_content:
        success.append("[OK] JWT authentication implemented")
    else:
        errors.append("[FAIL] JWT authentication missing")
    
    # Check CORS
    if "CORSMiddleware" in api_content:
        success.append("[OK] CORS middleware configured")
    else:
        errors.append("[FAIL] CORS middleware missing")
    
    # Check rate limiting
    if "RateLimiterMiddleware" in api_content:
        success.append("[OK] Rate limiting configured")
    else:
        warnings.append("[WARN] Rate limiting not configured")
        
except Exception as e:
    errors.append(f"[FAIL] Error reading api.py: {e}")

# Check 4: Docker configuration
print("\n[4/7] Checking Docker configuration...")
try:
    with open("Dockerfile", "r", encoding="utf-8") as f:
        dockerfile_content = f.read()
    
    if "HEALTHCHECK" in dockerfile_content:
        success.append("[OK] Docker health check configured")
    else:
        warnings.append("[WARN] Docker health check not configured")
    
    if "uvicorn" in dockerfile_content and "api:app" in dockerfile_content:
        success.append("[OK] Docker CMD points to api:app")
    elif "main:app" in dockerfile_content:
        warnings.append("[WARN] Docker CMD points to main:app (api:app recommended)")
    else:
        errors.append("[FAIL] Docker CMD not properly configured")
        
except Exception as e:
    errors.append(f"[FAIL] Error reading Dockerfile: {e}")

# Check 5: Database RLS
print("\n[5/7] Checking database RLS implementation...")
try:
    with open("database.py", "r", encoding="utf-8") as f:
        db_content = f.read()
    
    if "user_id" in db_content and "RLS" in db_content:
        success.append("[OK] RLS user_id filtering implemented")
    else:
        warnings.append("[WARN] RLS implementation may be incomplete")
    
    # Check for user_id in queries
    if '.eq("user_id", user_id)' in db_content or '"user_id": user_id' in db_content:
        success.append("[OK] Database queries filter by user_id")
    else:
        errors.append("[FAIL] Database queries may not filter by user_id (RLS violation)")
        
except Exception as e:
    errors.append(f"[FAIL] Error reading database.py: {e}")

# Check 6: Auth implementation
print("\n[6/7] Checking authentication...")
try:
    with open("auth.py", "r", encoding="utf-8") as f:
        auth_content = f.read()
    
    if "get_current_user" in auth_content and "jwt.decode" in auth_content:
        success.append("[OK] JWT validation implemented")
    else:
        errors.append("[FAIL] JWT validation missing")
    
    if "SUPABASE_JWT_SECRET" in auth_content:
        success.append("[OK] Supabase JWT secret used")
    else:
        errors.append("[FAIL] Supabase JWT secret not referenced")
        
except Exception as e:
    errors.append(f"[FAIL] Error reading auth.py: {e}")

# Check 7: Redis cache
print("\n[7/7] Checking Redis configuration...")
try:
    with open("utils.py", "r", encoding="utf-8") as f:
        utils_content = f.read()
    
    if "redis" in utils_content.lower() and "REDIS_URL" in utils_content:
        success.append("[OK] Redis cache configured")
    else:
        warnings.append("[WARN] Redis cache may not be properly configured")
        
except Exception as e:
    errors.append(f"[FAIL] Error reading utils.py: {e}")

# SUMMARY
print("\n" + "=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)

print(f"\n[OK] Successes: {len(success)}")
for item in success[:10]:  # Show first 10
    print(f"   {item}")
if len(success) > 10:
    print(f"   ... and {len(success) - 10} more")

if warnings:
    print(f"\n[WARN] Warnings: {len(warnings)}")
    for item in warnings:
        print(f"   {item}")

if errors:
    print(f"\n[FAIL] Errors: {len(errors)}")
    for item in errors:
        print(f"   {item}")

print("\n" + "=" * 60)

# Final verdict
if not errors:
    print("\n[RESULT] DEPLOYMENT READY! All critical checks passed.")
    if warnings:
        print(f"[NOTE] Address {len(warnings)} warning(s) before production deployment.")
    print("\nNext steps:")
    print("   1. Run: railway init  (or koyeb login)")
    print("   2. Set environment variables")
    print("   3. Deploy with: railway up")
    print("   4. Test: curl https://your-url.com/health")
    sys.exit(0)
else:
    print("\n[RESULT] NOT READY FOR DEPLOYMENT")
    print(f"\nFix {len(errors)} error(s) before deploying.")
    print("\nCritical issues to address:")
    for error in errors[:5]:  # Show first 5
        print(f"   {error}")
    sys.exit(1)

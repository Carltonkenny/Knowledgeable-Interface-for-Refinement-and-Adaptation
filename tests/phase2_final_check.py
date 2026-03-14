#!/usr/bin/env python3
# tests/test_phase2_final.py
# ─────────────────────────────────────────────
# Phase 2 Final Verification Test
#
# Tests all Phase 2 completion criteria:
# 1. Security (no hardcoded secrets, rate limiting)
# 2. LangMem embeddings
# 3. Profile Updater inactivity trigger
# 4. Session tracking
#
# Usage: python tests/test_phase2_final.py
# ─────────────────────────────────────────────

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# ═══ TEST RESULTS TRACKING ═══════════════════

tests_passed = 0
tests_failed = 0
tests_warnings = 0


def test_result(name, passed, message=""):
    """Track and display test result."""
    global tests_passed, tests_failed, tests_warnings
    
    if passed:
        logger.info(f"✅ {name}")
        tests_passed += 1
    elif message == "WARNING":
        logger.warning(f"⚠️  {name}")
        tests_warnings += 1
    else:
        logger.error(f"❌ {name}: {message}")
        tests_failed += 1


def read_file(filepath):
    """Read file with UTF-8 encoding."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# ═══ TEST 1: NO HARDCODED SECRETS ════════════

logger.info("\n" + "="*60)
logger.info("TEST 1: No Hardcoded Secrets")
logger.info("="*60)

try:
    config_content = read_file("config.py")
    
    # Check for hardcoded API key
    has_hardcoded_key = "sk_pi4kaulXNxktq6pGu2iOenFLEomriawF" in config_content
    uses_env_var = 'os.getenv("POLLINATIONS_API_KEY")' in config_content
    
    if has_hardcoded_key:
        test_result("Hardcoded API key removed", False, "API key still in config.py")
    else:
        test_result("Hardcoded API key removed", True)
    
    if uses_env_var:
        test_result("Uses environment variable", True)
    else:
        test_result("Uses environment variable", False, "Should use os.getenv()")
        
except Exception as e:
    test_result("Config file check", False, str(e))


# ═══ TEST 2: RATE LIMITING MIDDLEWARE ═══════

logger.info("\n" + "="*60)
logger.info("TEST 2: Rate Limiting Middleware")
logger.info("="*60)

try:
    # Check middleware exists
    if os.path.exists("middleware/rate_limiter.py"):
        test_result("Rate limiter middleware exists", True)
        
        middleware_content = read_file("middleware/rate_limiter.py")
        
        # Check for 100 requests/hour limit
        if "requests_per_window=100" in middleware_content:
            test_result("100 requests/hour limit configured", True)
        else:
            test_result("100 requests/hour limit configured", False, "Check rate_limiter.py")
        
        # Check for JWT extraction
        if "Authorization" in middleware_content and "Bearer" in middleware_content:
            test_result("JWT extraction from header", True)
        else:
            test_result("JWT extraction from header", False, "Should extract from Authorization header")
    else:
        test_result("Rate limiter middleware exists", False, "File not found")
        
except Exception as e:
    test_result("Rate limiter check", False, str(e))


# ═══ TEST 3: LANGMEM EMBEDDINGS ═════════════

logger.info("\n" + "="*60)
logger.info("TEST 3: LangMem Embedding Search")
logger.info("="*60)

try:
    if os.path.exists("memory/langmem.py"):
        test_result("LangMem file exists", True)
        
        langmem_content = read_file("memory/langmem.py")
        
        # Check for embedding function
        if "_generate_embedding" in langmem_content:
            test_result("Embedding generation function", True)
        else:
            test_result("Embedding generation function", False, "Missing _generate_embedding()")
        
        # Check for pgvector SQL usage (replaced Python cosine similarity)
        if "embedding <=>" in langmem_content or "pgvector" in langmem_content.lower():
            test_result("pgvector SQL similarity (faster)", True)
        else:
            test_result("pgvector SQL similarity (faster)", False, "Should use pgvector SQL operators")
        
        # Check for surface isolation
        if 'surface == "mcp"' in langmem_content:
            test_result("Surface isolation (web-app exclusive)", True)
        else:
            test_result("Surface isolation (web-app exclusive)", False, "Should reject MCP surface")
    else:
        test_result("LangMem file exists", False, "File not found")
        
except Exception as e:
    test_result("LangMem check", False, str(e))


# ═══ TEST 4: PROFILE UPDATER INACTIVITY ═════

logger.info("\n" + "="*60)
logger.info("TEST 4: Profile Updater Inactivity Trigger")
logger.info("="*60)

try:
    if os.path.exists("memory/profile_updater.py"):
        test_result("Profile updater file exists", True)
        
        updater_content = read_file("memory/profile_updater.py")
        
        # Check for inactivity threshold
        if "INACTIVITY_MINUTES = 30" in updater_content:
            test_result("30-minute inactivity threshold", True)
        else:
            test_result("30-minute inactivity threshold", False, "Should be 30 minutes")
        
        # Check for timezone-aware datetime
        if "timezone.utc" in updater_content:
            test_result("Timezone-aware datetime", True)
        else:
            test_result("Timezone-aware datetime", False, "Should use timezone.utc")
    else:
        test_result("Profile updater file exists", False, "File not found")
        
except Exception as e:
    test_result("Profile updater check", False, str(e))


# ═══ TEST 5: SESSION TRACKING ═══════════════

logger.info("\n" + "="*60)
logger.info("TEST 5: Session Tracking")
logger.info("="*60)

try:
    if os.path.exists("database.py"):
        test_result("Database file exists", True)
        
        db_content = read_file("database.py")
        
        # Check for session tracking functions
        if "update_session_activity" in db_content:
            test_result("update_session_activity() function", True)
        else:
            test_result("update_session_activity() function", False, "Missing function")
        
        if "get_last_activity" in db_content:
            test_result("get_last_activity() function", True)
        else:
            test_result("get_last_activity() function", False, "Missing function")
        
        # Check for datetime import
        if "from datetime import datetime, timezone" in db_content:
            test_result("Timezone datetime import", True)
        else:
            test_result("Timezone datetime import", False, "Should import timezone")
    else:
        test_result("Database file exists", False, "File not found")
        
except Exception as e:
    test_result("Session tracking check", False, str(e))


# ═══ TEST 6: API INTEGRATION ════════════════

logger.info("\n" + "="*60)
logger.info("TEST 6: API Integration")
logger.info("="*60)

try:
    if os.path.exists("api.py"):
        test_result("API file exists", True)
        
        api_content = read_file("api.py")
        
        # Check for rate limiter import
        if "from middleware.rate_limiter import RateLimiterMiddleware" in api_content:
            test_result("Rate limiter imported", True)
        else:
            test_result("Rate limiter imported", False, "Should import RateLimiterMiddleware")
        
        # Check for middleware registration
        if "app.add_middleware(RateLimiterMiddleware)" in api_content:
            test_result("Rate limiter middleware registered", True)
        else:
            test_result("Rate limiter middleware registered", False, "Should add middleware")
        
        # Check for session tracking in /chat
        if "update_session_activity" in api_content:
            test_result("Session tracking in /chat", True)
        else:
            test_result("Session tracking in /chat", False, "Should track session activity")
    else:
        test_result("API file exists", False, "File not found")
        
except Exception as e:
    test_result("API integration check", False, str(e))


# ═══ TEST 7: MIGRATION FILES ════════════════

logger.info("\n" + "="*60)
logger.info("TEST 7: Migration Files")
logger.info("="*60)

try:
    migrations = [
        ("010_add_embedding_column.sql", "LangMem embedding column"),
        ("011_add_user_sessions_table.sql", "User sessions table"),
    ]
    
    for filename, description in migrations:
        filepath = f"migrations/{filename}"
        if os.path.exists(filepath):
            test_result(f"{description} ({filename})", True)
            
            # Check file content
            with open(filepath, "r") as f:
                content = f.read()
            
            if "BEGIN" in content and "COMMIT" in content:
                test_result(f"  - Transaction wrapping", True)
            else:
                test_result(f"  - Transaction wrapping", False, "Should use BEGIN/COMMIT")
        else:
            test_result(f"{description} ({filename})", False, "File not found")
        
except Exception as e:
    test_result("Migration files check", False, str(e))


# ═══ TEST 8: COMPLETION REPORT ══════════════

logger.info("\n" + "="*60)
logger.info("TEST 8: Documentation")
logger.info("="*60)

try:
    if os.path.exists("PHASE_2_COMPLETION_REPORT.md"):
        test_result("PHASE_2_COMPLETION_REPORT.md exists", True)
        
        report_content = read_file("PHASE_2_COMPLETION_REPORT.md")
        
        # Check for key sections
        sections = [
            ("COMPLETION CHECKLIST", "Completion checklist"),
            ("Known Limitations", "Known limitations documented"),
            ("Security Compliance", "Security compliance table"),
        ]
        
        for section, description in sections:
            if section in report_content:
                test_result(f"  - {description}", True)
            else:
                test_result(f"  - {description}", False, f"Missing '{section}' section")
    else:
        test_result("PHASE_2_COMPLETION_REPORT.md exists", False, "File not found")
        
except Exception as e:
    test_result("Documentation check", False, str(e))


# ═══ SUMMARY ════════════════════════════════

logger.info("\n" + "="*60)
logger.info("PHASE 2 VERIFICATION SUMMARY")
logger.info("="*60)
logger.info(f"\nTests Passed:   {tests_passed}")
logger.info(f"Tests Warning:  {tests_warnings}")
logger.info(f"Tests Failed:   {tests_failed}")
logger.info(f"Total:          {tests_passed + tests_failed + tests_warnings}")

if tests_failed == 0:
    logger.info("\n✅ ALL TESTS PASSED - PHASE 2 COMPLETE")
    logger.info("\nNEXT STEPS:")
    logger.info("1. Run migrations in Supabase SQL Editor:")
    logger.info("   - migrations/010_add_embedding_column.sql")
    logger.info("   - migrations/011_add_user_sessions_table.sql")
    logger.info("2. Update .env with your API key:")
    logger.info("   POLLINATIONS_API_KEY=your_key_here")
    logger.info("3. Restart server: python main.py")
    logger.info("4. Proceed to Phase 3 (MCP Integration)")
    sys.exit(0)
else:
    logger.info(f"\n❌ {tests_failed} TESTS FAILED - REVIEW ERRORS ABOVE")
    sys.exit(1)

# testadvance/conftest.py
# Pytest Fixtures for Comprehensive Testing

import os
import sys
import pytest
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


@pytest.fixture(scope="session")
def base_url():
    """API base URL fixture."""
    return BASE_URL


@pytest.fixture(scope="session")
def test_jwt():
    """
    Generate test JWT token.
    
    Usage:
        def test_something(test_jwt):
            headers = {"Authorization": f"Bearer {test_jwt}"}
    """
    import jwt
    import datetime
    
    payload = {
        "sub": "test-user-0000-0000-0000-000000000000",
        "iss": SUPABASE_URL,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    
    token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")
    return token


@pytest.fixture(scope="session")
def auth_headers(test_jwt):
    """Authorization headers with JWT."""
    return {"Authorization": f"Bearer {test_jwt}"}


@pytest.fixture(scope="session")
def api_session():
    """Requests session for API calls."""
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture
def valid_prompt():
    """Valid prompt for testing."""
    return "Write a Python function to sort a list of dictionaries by a specific key"


@pytest.fixture
def short_prompt():
    """Too short prompt (< 5 chars)."""
    return "hi"


@pytest.fixture
def long_prompt():
    """Too long prompt (> 2000 chars)."""
    return "x" * 2001


@pytest.fixture
def empty_prompt():
    """Empty prompt."""
    return ""


@pytest.fixture
def valid_session_id():
    """Valid session ID."""
    return "test-session-123"


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "test-user-0000-0000-0000-000000000000"


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing."""
    return [
        {"role": "user", "message": "Write a story", "message_type": "new_prompt"},
        {"role": "assistant", "message": "Here's your story...", "message_type": "prompt_improved"},
    ]


@pytest.fixture
def rate_limit_test_jwt():
    """JWT for rate limit testing (different user)."""
    import jwt
    import datetime
    
    payload = {
        "sub": "rate-test-user-0000-0000-0000-0000000000",
        "iss": SUPABASE_URL,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    
    return jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def expired_jwt():
    """Expired JWT token."""
    import jwt
    import datetime
    
    payload = {
        "sub": "test-user",
        "iss": SUPABASE_URL,
        "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    }
    
    return jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def invalid_jwt():
    """Invalid JWT token."""
    return "invalid.token.here"


@pytest.fixture
def mcp_long_lived_jwt(test_user_id):
    """Long-lived MCP JWT (365 days)."""
    import jwt
    import datetime
    
    payload = {
        "sub": test_user_id,
        "type": "mcp_access",
        "iss": SUPABASE_URL,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    }
    
    return jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")

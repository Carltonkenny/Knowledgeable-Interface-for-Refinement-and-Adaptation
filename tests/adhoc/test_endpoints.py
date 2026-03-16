
from fastapi.testclient import TestClient
from api import app
from auth import User
import database

# Mock authentication
def mock_get_current_user():
    return User(user_id="00000000-0000-0000-0000-000000000000", email="test@example.com")

from auth import get_current_user
app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

def test_endpoints():
    print("Testing /history/sessions...")
    response = client.get("/history/sessions?limit=5")
    if response.status_code == 200:
        print("SUCCESS: /history/sessions returned 200")
    else:
        print(f"FAILED: /history/sessions returned {response.status_code}: {response.text}")

    print("\nTesting /history/analytics...")
    response = client.get("/history/analytics?days=7")
    if response.status_code == 200:
        print("SUCCESS: /history/analytics returned 200")
    else:
        print(f"FAILED: /history/analytics returned {response.status_code}: {response.text}")

    print("\nTesting /history/search...")
    search_data = {
        "query": "test query",
        "use_rag": False,
        "limit": 5
    }
    response = client.post("/history/search", json=search_data)
    if response.status_code == 200:
        print("SUCCESS: /history/search returned 200")
    else:
        print(f"FAILED: /history/search returned {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_endpoints()

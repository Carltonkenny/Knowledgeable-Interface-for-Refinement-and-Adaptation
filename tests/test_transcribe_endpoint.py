import pytest
from io import BytesIO
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from api import app
from auth import get_current_user, User

client = TestClient(app)

# Mock user for auth
mock_user = User(user_id="test-user-123", email="test@example.com", role="authenticated")

def override_get_current_user():
    return mock_user

class TestTranscribeEndpoint:
    def setup_method(self):
        # Clear any existing overrides
        app.dependency_overrides = {}

    def test_valid_audio_with_jwt_returns_200(self):
        """Test valid audio with working JWT returns 200 and transcript."""
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        audio_data = BytesIO(b"fake webm audio data")
        audio_data.name = "test.webm"
        
        with patch('routes.mcp.transcribe_voice') as mock_transcribe:
            mock_transcribe.return_value = {
                "transcript": "test transcript"
            }
            
            response = client.post(
                "/transcribe",
                files={"audio": ("test.webm", audio_data, "audio/webm")},
                headers={"Authorization": "Bearer fake-jwt-token"}
            )
            
            assert response.status_code == 200
            assert response.json() == {"transcript": "test transcript"}

    def test_valid_audio_no_jwt_returns_401(self):
        """Test valid audio without JWT returns 401."""
        app.dependency_overrides = {}
        
        audio_data = BytesIO(b"fake audio data")
        audio_data.name = "test.webm"
        
        # Don't pass the authorization header
        response = client.post(
            "/transcribe",
            files={"audio": ("test.webm", audio_data, "audio/webm")}
        )
        
        assert response.status_code in [401, 403]
        assert "not authenticated" in response.json()["detail"].lower()

    def test_audio_oversized_returns_400(self):
        """Test oversized audio file returns 400."""
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        oversized_data = BytesIO(b"x" * (26 * 1024 * 1024))
        oversized_data.name = "large.webm"
        
        with patch('routes.mcp.transcribe_voice') as mock_transcribe:
            # Simulate the validation failure in transcribe_voice
            mock_transcribe.side_effect = HTTPException(status_code=400, detail="File too large")
            
            response = client.post(
                "/transcribe",
                files={"audio": ("large.webm", oversized_data, "audio/webm")},
                headers={"Authorization": "Bearer fake-jwt-token"}
            )
            
            assert response.status_code == 400
            assert "large" in response.json()["detail"].lower()

    def test_non_audio_file_returns_400(self):
        """Test non-audio file returns 400."""
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        pdf_data = BytesIO(b"%PDF-1.4 fake pdf content")
        pdf_data.name = "document.pdf"
        
        with patch('routes.mcp.transcribe_voice') as mock_transcribe:
            # Simulate the validation failure in transcribe_voice
            mock_transcribe.side_effect = HTTPException(status_code=400, detail="Unsupported MIME type")
            
            response = client.post(
                "/transcribe",
                files={"audio": ("document.pdf", pdf_data, "application/pdf")},
                headers={"Authorization": "Bearer fake-jwt-token"}
            )
            
            assert response.status_code == 400
            assert "unsupported" in response.json()["detail"].lower()

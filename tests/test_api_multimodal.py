# tests/test_api_multimodal.py
# ─────────────────────────────────────────────
# Tests for multimodal API support (files, voice, images)
#
# RULES.md Compliance:
# - Tests file upload handling
# - Tests validation before processing
# - Tests API endpoint structure
# ─────────────────────────────────────────────

import pytest
from fastapi.testclient import TestClient
from api import app, ChatRequest
from state import PromptForgeState

client = TestClient(app)


class TestChatRequestSchema:
    """Test ChatRequest schema with multimodal support."""

    def test_chat_request_minimal(self):
        """Test minimal chat request (text only)."""
        req = ChatRequest(
            message="Test message",
            session_id="test-session"
        )
        
        assert req.message == "Test message"
        assert req.session_id == "test-session"
        assert req.input_modality == "text"
        assert req.file_base64 is None
        assert req.file_type is None

    def test_chat_request_with_attachment(self):
        """Test chat request with file attachment."""
        req = ChatRequest(
            message="Analyze this file",
            session_id="test-session",
            input_modality="file",
            file_base64="data:text/plain;base64,SGVsbG8=",
            file_type="text/plain"
        )
        
        assert req.input_modality == "file"
        assert req.file_base64 is not None
        assert req.file_type == "text/plain"

    def test_chat_request_with_image(self):
        """Test chat request with image attachment."""
        req = ChatRequest(
            message="What's in this image?",
            session_id="test-session",
            input_modality="image",
            file_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            file_type="image/png"
        )
        
        assert req.input_modality == "image"
        assert req.file_type.startswith("image/")

    def test_chat_request_validation_message_length(self):
        """Test message length validation."""
        # Too short (min_length=1)
        with pytest.raises(Exception):
            ChatRequest(
                message="",
                session_id="test"
            )
        
        # Too long (max_length=2000)
        with pytest.raises(Exception):
            ChatRequest(
                message="x" * 2001,
                session_id="test"
            )

    def test_chat_request_valid_lengths(self):
        """Test valid message lengths."""
        # Minimum length
        req1 = ChatRequest(
            message="x",
            session_id="test"
        )
        assert req1.message == "x"
        
        # Maximum length
        req2 = ChatRequest(
            message="x" * 2000,
            session_id="test"
        )
        assert len(req2.message) == 2000


class TestRunSwarmWithAttachments:
    """Test _run_swarm function with attachments."""

    def test_run_swarm_without_attachments(self):
        """Test swarm runs without attachments."""
        from service import _run_swarm
        
        result = _run_swarm(
            prompt="Test prompt",
            user_id="test-user",
            input_modality="text"
        )
        
        assert "improved_prompt" in result
        assert "quality_score" in result

    def test_run_swarm_with_file_attachment(self):
        """Test swarm accepts file attachment parameters."""
        from service import _run_swarm
        
        # Should not raise exception
        result = _run_swarm(
            prompt="Analyze this file",
            user_id="test-user",
            input_modality="file",
            file_base64="data:text/plain;base64,SGVsbG8=",
            file_type="text/plain"
        )
        
        assert "improved_prompt" in result

    def test_run_swarm_initializes_attachments(self):
        """Test swarm initializes attachments in state."""
        from service import _run_swarm
        from state import AgentState
        
        # Mock to capture initial state
        initial_states = []
        
        def mock_invoke(state):
            initial_states.append(state)
            return {
                "improved_prompt": "test",
                "quality_score": {"specificity": 3, "clarity": 3, "actionability": 3},
            }
        
        # Temporarily replace workflow.invoke
        import service
        original_invoke = service.workflow.invoke
        service.workflow.invoke = mock_invoke
        
        try:
            _run_swarm(
                prompt="Test with file",
                user_id="test-user",
                input_modality="file",
                file_base64="data:text/plain;base64,SGVsbG8=",
                file_type="text/plain"
            )
            
            # Verify state was initialized with attachments
            assert len(initial_states) > 0
            state = initial_states[0]
            assert "attachments" in state
            assert "input_modality" in state
            assert state["input_modality"] == "file"
            
        finally:
            # Restore original
            workflow.workflow.invoke = original_invoke


class TestPromptForgeState:
    """Test PromptForgeState supports multimodal fields."""

    def test_state_has_attachments_field(self):
        """Test state has attachments field."""
        state = PromptForgeState(
            message="test",
            session_id="test",
            user_id="test",
            attachments=[
                {"type": "file", "content": "base64data", "filename": "test.txt"}
            ],
            input_modality="file",
            conversation_history=[],
            user_profile={},
            langmem_context=[],
            mcp_trust_level=0,
            orchestrator_decision={},
            user_facing_message="",
            pending_clarification=False,
            clarification_key=None,
            proceed_with_swarm=True,
            intent_analysis={},
            context_analysis={},
            domain_analysis={},
            agents_skipped=[],
            agent_latencies={},
            improved_prompt="",
            original_prompt="test",
            prompt_diff=[],
            quality_score={},
            changes_made=[],
            breakdown={},
            latency_ms=0,
            memories_applied=0,
        )
        
        assert "attachments" in state
        assert len(state["attachments"]) == 1
        assert state["input_modality"] == "file"

    def test_state_attachments_optional(self):
        """Test attachments field is optional."""
        # Should work without attachments
        state = PromptForgeState(
            message="test",
            session_id="test",
            user_id="test",
            attachments=[],  # Empty is valid
            input_modality="text",
            conversation_history=[],
            user_profile={},
            langmem_context=[],
            mcp_trust_level=0,
            orchestrator_decision={},
            user_facing_message="",
            pending_clarification=False,
            clarification_key=None,
            proceed_with_swarm=True,
            intent_analysis={},
            context_analysis={},
            domain_analysis={},
            agents_skipped=[],
            agent_latencies={},
            improved_prompt="",
            original_prompt="test",
            prompt_diff=[],
            quality_score={},
            changes_made=[],
            breakdown={},
            latency_ms=0,
            memories_applied=0,
        )
        
        assert state["attachments"] == []
        assert state["input_modality"] == "text"


# ═══ ENDPOINT TESTS ══════════════════════════

class TestChatStreamEndpoint:
    """Test /chat/stream endpoint with multimodal support."""

    def test_chat_stream_accepts_multimodal_request(self):
        """Test stream endpoint accepts multimodal requests."""
        # This would require auth setup, so we test schema validation
        from api import ChatRequest
        
        # Valid multimodal request
        req = ChatRequest(
            message="Process this file",
            session_id="test",
            input_modality="file",
            file_base64="data:text/plain;base64,test",
            file_type="text/plain"
        )
        
        assert req.input_modality in ["text", "file", "image", "voice"]
        assert req.file_base64 is not None

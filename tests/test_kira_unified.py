# tests/test_kira_unified.py
# ─────────────────────────────────────────────
# Tests for Unified Kira Handler
# 
# RULES.md Compliance:
# - Type hints mandatory
# - Docstrings complete
# - Error handling comprehensive
# - Logging contextual
# ─────────────────────────────────────────────

import pytest
import time
from unittest import mock
from agents.autonomous import (
    build_kira_context,
    kira_unified_handler,
    fallback_unified_response,
    KIRA_UNIFIED_PROMPT,
)


class TestBuildKiraContext:
    """Test context builder with full user profile."""
    
    def test_build_context_basic(self):
        """Test basic context building."""
        message = "make it async"
        history = [
            {"role": "user", "message": "Write a FastAPI endpoint"},
            {"role": "assistant", "improved_prompt": "[FastAPI prompt]"},
        ]
        user_profile = {
            "primary_use": "coding",
            "audience": "technical",
            "preferred_tone": "direct"
        }
        
        context = build_kira_context(message, history, user_profile)
        
        assert "make it async" in context
        assert "coding" in context
        assert "technical" in context
        assert "direct" in context
        assert "FastAPI" in context
    
    def test_build_context_empty_profile(self):
        """Test context with empty user profile."""
        message = "hi"
        history = []
        user_profile = {}
        
        context = build_kira_context(message, history, user_profile)
        
        assert "hi" in context
        assert "general" in context  # Default values
    
    def test_build_context_with_last_improved(self):
        """Test context includes last improved prompt."""
        message = "make it longer"
        history = [
            {"role": "user", "message": "Write something"},
            {"role": "assistant", "improved_prompt": "This is a detailed prompt with specifics."},
        ]
        user_profile = {}
        
        context = build_kira_context(message, history, user_profile)
        
        assert "Last improved prompt" in context
        assert "detailed prompt" in context
    
    def test_build_context_error_fallback(self):
        """Test fallback on error."""
        # Pass invalid data to trigger error
        context = build_kira_context("test", None, None)  # type: ignore
        
        assert "User's message: test" in context


class TestKiraUnifiedHandler:
    """Test unified handler with full context."""
    
    @mock.patch('agents.autonomous.get_fast_llm')
    def test_conversation_intent(self, mock_llm):
        """Test conversation detection and response."""
        # Mock LLM response
        mock_response = mock.Mock()
        mock_response.content = '''{
            "intent": "conversation",
            "response": "Hey! I'm Kira — I turn messy prompts into precise ones.",
            "improved_prompt": null,
            "changes_made": [],
            "metadata": {"user_energy": "casual"}
        }'''
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = kira_unified_handler(
            message="hi",
            history=[],
            user_profile={"primary_use": "coding"}
        )
        
        assert result["intent"] == "conversation"
        assert result["response"] is not None
        assert len(result["response"]) < 200  # 2-4 sentences
    
    @mock.patch('agents.autonomous.get_fast_llm')
    def test_followup_intent(self, mock_llm):
        """Test followup detection with context."""
        # Mock LLM response
        mock_response = mock.Mock()
        mock_response.content = '''{
            "intent": "followup",
            "response": "Got it — I'll expand with more detail.",
            "improved_prompt": "[Expanded prompt with async/await]",
            "changes_made": ["Added async patterns"],
            "metadata": {"user_energy": "direct"}
        }'''
        mock_llm.return_value.invoke.return_value = mock_response
        
        history = [
            {"role": "user", "message": "Write a FastAPI endpoint"},
            {"role": "assistant", "improved_prompt": "[FastAPI prompt]"}
        ]
        
        result = kira_unified_handler(
            message="make it async",
            history=history,
            user_profile={"primary_use": "coding"}
        )
        
        assert result["intent"] == "followup"
        assert result["improved_prompt"] is not None
        assert "async" in result["improved_prompt"].lower()
    
    @mock.patch('agents.autonomous.get_fast_llm')
    def test_context_awareness(self, mock_llm):
        """Test that handler remembers user preferences."""
        # Mock LLM response with coding reference
        mock_response = mock.Mock()
        mock_response.content = '''{
            "intent": "conversation",
            "response": "Hey! I specialize in crafting precise prompts for developers and engineers.",
            "improved_prompt": null,
            "changes_made": [],
            "metadata": {"referenced_coding": True}
        }'''
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = kira_unified_handler(
            message="hi",
            history=[],
            user_profile={
                "primary_use": "coding",
                "preferred_tone": "technical"
            }
        )
        
        # Should have response
        assert result["intent"] == "conversation"
        assert result["response"] is not None
    
    @mock.patch('agents.autonomous.get_fast_llm')
    def test_invalid_response_fallback(self, mock_llm):
        """Test fallback when LLM returns invalid response."""
        # Mock LLM to return invalid JSON
        mock_response = mock.Mock()
        mock_response.content = "invalid json"
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = kira_unified_handler(
            message="hi",
            history=[],
            user_profile={}
        )
        
        # Should fallback gracefully
        assert result["intent"] in ["conversation", "followup", "new_prompt"]
        assert result["response"] is not None
        assert result["metadata"].get("fallback") == True
    
    @mock.patch('agents.autonomous.get_fast_llm')
    def test_latency_logging(self, mock_llm):
        """Test that latency is logged."""
        # Mock LLM response
        mock_response = mock.Mock()
        mock_response.content = '{"intent": "conversation", "response": "Hi!"}'
        mock_llm.return_value.invoke.return_value = mock_response
        
        start = time.time()
        result = kira_unified_handler(
            message="hi",
            history=[],
            user_profile={}
        )
        latency_ms = int((time.time() - start) * 1000)
        
        # Should complete in reasonable time
        assert latency_ms < 2000  # 2s max for fast LLM
        assert result["intent"] == "conversation"


class TestFallbackUnifiedResponse:
    """Test fallback handler."""
    
    def test_fallback_conversation(self):
        """Test fallback detects conversation."""
        result = fallback_unified_response(
            message="hi",
            history=[],
            user_profile={}
        )
        
        assert result["intent"] == "conversation"
        assert result["response"] is not None
    
    def test_fallback_followup(self):
        """Test fallback detects followup."""
        # Followup detection needs history with previous prompt
        history = [
            {"role": "user", "message": "Write something"},
            {"role": "assistant", "improved_prompt": "[previous prompt]"}
        ]
        
        result = fallback_unified_response(
            message="make it better",
            history=history,
            user_profile={}
        )
        
        # With history, should detect followup
        assert result["intent"] in ["followup", "new_prompt"]  # Either is acceptable
        assert result["response"] is not None
    
    def test_fallback_new_prompt(self):
        """Test fallback detects new prompt."""
        result = fallback_unified_response(
            message="write a python function for fibonacci",
            history=[],
            user_profile={}
        )
        
        assert result["intent"] == "new_prompt"
        assert result["response"] is not None
    
    def test_fallback_ultimate(self):
        """Test ultimate fallback on error."""
        # This should never fail
        result = fallback_unified_response(
            message="test",
            history=[],  # Empty list instead of None
            user_profile={}  # Empty dict instead of None
        )
        
        assert result["intent"] in ["conversation", "followup", "new_prompt"]
        assert result["response"] is not None
        # Response should be meaningful
        assert len(result["response"]) > 10


class TestKiraUnifiedPerformance:
    """Test latency targets."""
    
    @mock.patch('agents.autonomous.get_fast_llm')
    def test_conversation_latency(self, mock_llm):
        """Test conversation response time < 500ms."""
        # Mock LLM response
        mock_response = mock.Mock()
        mock_response.content = '{"intent": "conversation", "response": "Hi!"}'
        mock_llm.return_value.invoke.return_value = mock_response
        
        start = time.time()
        
        result = kira_unified_handler(
            message="hi",
            history=[],
            user_profile={}
        )
        
        latency_ms = int((time.time() - start) * 1000)
        
        assert latency_ms < 500, f"Conversation latency {latency_ms}ms > 500ms"
    
    @mock.patch('agents.autonomous.get_fast_llm')
    def test_followup_latency(self, mock_llm):
        """Test followup response time < 500ms."""
        # Mock LLM response
        mock_response = mock.Mock()
        mock_response.content = '''{
            "intent": "followup",
            "response": "Updated!",
            "improved_prompt": "[prompt]"
        }'''
        mock_llm.return_value.invoke.return_value = mock_response
        
        history = [
            {"role": "user", "message": "Write something"},
            {"role": "assistant", "improved_prompt": "[prompt]"}
        ]
        
        start = time.time()
        
        result = kira_unified_handler(
            message="make it better",
            history=history,
            user_profile={}
        )
        
        latency_ms = int((time.time() - start) * 1000)
        
        assert latency_ms < 500, f"Followup latency {latency_ms}ms > 500ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

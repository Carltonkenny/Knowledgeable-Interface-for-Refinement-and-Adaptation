# tests/test_prompt_engineer.py
# ─────────────────────────────────────────────
# Tests for prompt_engineer agent with diff generation
#
# RULES.md Compliance:
# - Unit tests for individual functions
# - Integration tests for agent workflow
# - Validates agent output structure
# ─────────────────────────────────────────────

import pytest
from agents.prompt_engineer import prompt_engineer_agent, generate_diff, validate_engineer_output
from state import AgentState


class TestGenerateDiff:
    """Test diff generation between original and improved prompts."""

    def test_generate_diff_basic_additions(self):
        """Test diff detects added sentences."""
        original = "Write a story."
        improved = "Write a compelling story. Add characters with depth."
        
        diff = generate_diff(original, improved)
        
        assert isinstance(diff, list)
        assert len(diff) > 0
        # Should detect at least one addition
        additions = [item for item in diff if item['type'] == 'add']
        assert len(additions) > 0

    def test_generate_diff_basic_removals(self):
        """Test diff detects removed sentences."""
        original = "Write a story. Make it long. Add fluff."
        improved = "Write a story."
        
        diff = generate_diff(original, improved)
        
        # Should detect removals
        removals = [item for item in diff if item['type'] == 'remove']
        assert len(removals) > 0

    def test_generate_diff_no_changes(self):
        """Test diff handles identical prompts."""
        original = "Write a story."
        improved = "Write a story."
        
        diff = generate_diff(original, improved)
        
        assert isinstance(diff, list)
        # Should mark as keep when no changes
        keeps = [item for item in diff if item['type'] == 'keep']
        assert len(keeps) > 0

    def test_generate_diff_structure(self):
        """Test diff returns correct structure."""
        original = "Test prompt."
        improved = "Improved test prompt."
        
        diff = generate_diff(original, improved)
        
        # Each item should have type and text
        for item in diff:
            assert 'type' in item
            assert 'text' in item
            assert item['type'] in ['add', 'remove', 'keep']
            assert isinstance(item['text'], str)


class TestPromptEngineerAgent:
    """Test prompt engineer agent functionality."""

    def test_prompt_engineer_returns_required_fields(self):
        """Test agent returns all required fields."""
        state = AgentState(
            message="Write a story",
            intent_analysis={"primary_intent": "creative"},
            context_analysis={"context": "fiction writing"},
            domain_analysis={"primary_domain": "creative"},
            improved_prompt="",
        )
        
        result = prompt_engineer_agent(state)
        
        # Required fields per RULES.md
        assert "improved_prompt" in result
        assert "quality_score" in result
        assert "changes_made" in result
        assert "prompt_diff" in result
        assert "was_skipped" in result
        assert "latency_ms" in result

    def test_prompt_engineer_quality_score_structure(self):
        """Test quality score has correct structure."""
        state = AgentState(
            message="Write a story",
            intent_analysis={"primary_intent": "creative"},
            context_analysis={},
            domain_analysis={},
            improved_prompt="",
        )
        
        result = prompt_engineer_agent(state)
        quality = result["quality_score"]
        
        assert "specificity" in quality
        assert "clarity" in quality
        assert "actionability" in quality
        # Scores should be 1-5
        assert 1 <= quality["specificity"] <= 5
        assert 1 <= quality["clarity"] <= 5
        assert 1 <= quality["actionability"] <= 5

    def test_prompt_engineer_diff_structure(self):
        """Test prompt_diff is correctly structured."""
        state = AgentState(
            message="Write a story",
            intent_analysis={"primary_intent": "creative"},
            context_analysis={},
            domain_analysis={},
            improved_prompt="",
        )
        
        result = prompt_engineer_agent(state)
        
        assert "prompt_diff" in result
        assert isinstance(result["prompt_diff"], list)
        
        # Each diff item should have correct structure
        for item in result["prompt_diff"]:
            assert "type" in item
            assert "text" in item
            assert item["type"] in ["add", "remove", "keep"]

    def test_prompt_engineer_fallback_on_empty_analysis(self):
        """Test agent handles empty upstream analysis gracefully."""
        state = AgentState(
            message="Test prompt",
            intent_analysis={},
            context_analysis={},
            domain_analysis={},
            improved_prompt="",
        )
        
        result = prompt_engineer_agent(state)
        
        # Should still return valid structure
        assert "improved_prompt" in result
        assert "quality_score" in result
        # Quality should be low due to missing analysis
        assert result["quality_score"]["specificity"] <= 2


class TestValidateEngineerOutput:
    """Test validation function for engineer output."""

    def test_validate_passes_good_output(self):
        """Test validation passes quality output."""
        result = {
            "improved_prompt": "This is significantly longer and more detailed than the original.",
            "changes_made": ["Added role", "Added constraints", "Added output format"],
            "quality_score": {
                "specificity": 4,
                "clarity": 4,
                "actionability": 4
            }
        }
        original = "Short prompt"
        
        passes = validate_engineer_output(result, original)
        assert passes is True

    def test_validate_fails_short_output(self):
        """Test validation fails when output too short."""
        result = {
            "improved_prompt": "Short",
            "changes_made": ["Changed one word"],
            "quality_score": {
                "specificity": 2,
                "clarity": 2,
                "actionability": 2
            }
        }
        original = "This is a much longer original prompt that should not be shorter than the output"
        
        passes = validate_engineer_output(result, original)
        assert passes is False

    def test_validate_fails_missing_changes(self):
        """Test validation fails without documented changes."""
        result = {
            "improved_prompt": "This is a good improved prompt with lots of detail",
            "changes_made": ["One change"],
            "quality_score": {
                "specificity": 4,
                "clarity": 4,
                "actionability": 4
            }
        }
        original = "Original prompt"
        
        passes = validate_engineer_output(result, original)
        assert passes is False  # Needs at least 3 changes

    def test_validate_fails_low_quality(self):
        """Test validation fails with low quality scores."""
        result = {
            "improved_prompt": "Improved prompt with good length",
            "changes_made": ["Change 1", "Change 2", "Change 3"],
            "quality_score": {
                "specificity": 1,
                "clarity": 2,
                "actionability": 1
            }
        }
        original = "Original"
        
        passes = validate_engineer_output(result, original)
        assert passes is False  # Average < 3.0


# ═══ INTEGRATION TESTS ═══════════════════════

class TestPromptEngineerIntegration:
    """Integration tests for prompt engineer in workflow context."""

    def test_full_agent_workflow(self):
        """Test complete agent workflow with state."""
        # Simulate state after intent, context, domain agents
        state = AgentState(
            message="Write me a story about a robot",
            intent_analysis={
                "primary_intent": "creative_writing",
                "goal_clarity": 4,
                "missing_info": []
            },
            context_analysis={
                "context": "User wants creative content",
                "tone": "casual"
            },
            domain_analysis={
                "primary_domain": "creative",
                "confidence": 0.95
            },
            improved_prompt="",
            user_id="test-user-123",
            session_id="test-session-456",
        )
        
        # Run prompt engineer
        result = prompt_engineer_agent(state)
        
        # Verify complete output
        assert len(result["improved_prompt"]) > len(state["message"])
        assert len(result["changes_made"]) >= 3
        assert len(result["prompt_diff"]) > 0
        assert result["latency_ms"] > 0
        assert result["was_skipped"] is False

    def test_agent_handles_exception_gracefully(self):
        """Test agent handles exceptions without crashing."""
        # Invalid state to trigger error
        state = AgentState(
            message="Test",
            # Missing required upstream analysis
        )
        
        # Should not raise exception
        result = prompt_engineer_agent(state)
        
        # Should return fallback
        assert "improved_prompt" in result
        assert "prompt_diff" in result
        assert result["was_skipped"] is False

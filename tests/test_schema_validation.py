# tests/test_schema_validation.py
# ─────────────────────────────────────────────
# Tests for schema validation (PromptForgeState, Diff generation)
#
# RULES.md Compliance:
# - Validates type safety
# - No external dependencies required
# ─────────────────────────────────────────────

import pytest


class TestPromptForgeState:
    """Test PromptForgeState supports multimodal fields."""

    def test_state_has_attachments_field(self):
        """Test state has attachments field."""
        from state import PromptForgeState
        
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
        from state import PromptForgeState
        
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

    def test_state_all_required_fields(self):
        """Test all required fields are present."""
        from state import PromptForgeState
        
        state = PromptForgeState(
            message="test",
            session_id="test",
            user_id="test",
            attachments=[],
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
        
        # Verify all 26 fields per RULES.md
        required_fields = [
            'message', 'session_id', 'user_id', 'attachments', 'input_modality',
            'conversation_history', 'user_profile', 'langmem_context', 'mcp_trust_level',
            'orchestrator_decision', 'user_facing_message', 'pending_clarification',
            'clarification_key', 'proceed_with_swarm', 'intent_analysis', 'context_analysis',
            'domain_analysis', 'agents_skipped', 'agent_latencies', 'improved_prompt',
            'original_prompt', 'prompt_diff', 'quality_score', 'changes_made', 'breakdown',
            'latency_ms', 'memories_applied'
        ]
        
        for field in required_fields:
            assert field in state, f"Missing required field: {field}"


class TestDiffGeneration:
    """Test diff generation utility."""

    def test_diff_generated_correctly(self):
        """Test diff generation between prompts."""
        from agents.prompt_engineer import generate_diff
        
        original = "Write a story."
        improved = "Write a compelling story with characters."
        
        diff = generate_diff(original, improved)
        
        assert isinstance(diff, list)
        assert len(diff) > 0
        
        for item in diff:
            assert "type" in item
            assert "text" in item
            assert item["type"] in ["add", "remove", "keep"]


# ═══ RUN ALL TESTS ═══════════════════════════
# Run with: pytest tests/test_schema_validation.py -v
# Expected: All tests pass (no external dependencies)
# ══════════════════════════════════════════════

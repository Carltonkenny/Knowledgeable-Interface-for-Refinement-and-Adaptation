import unittest
from typing import Dict, Any
import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the modules to test
try:
    from memory.memory_extractor import save_core_memories_if_needed, extract_key_learnings
    from agents.enhanced_feedback import generate_processing_feedback, finalize_conversation
    from agents.state_consistency import state_manager
    print("All imports successful")
except ImportError as e:
    print(f"Import error: {e}")

class TestSystemIntegration(unittest.TestCase):
    """Test integration of all system components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_user_id = "test-user-123"
        self.test_session_id = "session-456"
        self.test_session_result = {
            "raw_prompt": "Write about AI",
            "improved_prompt": "Write a comprehensive essay about artificial intelligence and its applications in modern technology",
            "domain_analysis": {"primary_domain": "technology"},
            "quality_score": {"overall": 4.2, "specificity": 4.5, "clarity": 4.0},
            "changes_made": ["Added specificity", "Improved clarity", "Enhanced structure"],
            "agents_used": ["intent", "context", "domain"],
            "agent_latencies": {"intent": 150, "context": 200, "domain": 180, "prompt_engineer": 800}
        }
        self.test_conversation_history = [
            {"role": "user", "message": "Write about AI", "message_type": "prompt"},
            {"role": "assistant", "message": "I'll help with that", "message_type": "response"}
        ]
        self.test_orchestrator_decision = {
            "user_facing_message": "Analyzing your request...",
            "proceed_with_swarm": True,
            "route": "SWARM",
            "agents_to_run": ["intent", "context", "domain"],
            "clarification_needed": False,
            "clarification_question": None,
            "skip_reasons": {},
            "tone_used": "direct",
            "profile_applied": True,
            "ambiguity_score": 0.2
        }
    
    def test_imports_work(self):
        """Test that all modules can be imported"""
        self.assertIsNotNone(save_core_memories_if_needed)
        self.assertIsNotNone(extract_key_learnings)
        self.assertIsNotNone(generate_processing_feedback)
        self.assertIsNotNone(finalize_conversation)
        self.assertIsNotNone(state_manager)
    
    def test_memory_extraction_functions_exist(self):
        """Test that memory extraction functions exist"""
        # Test that functions exist and are callable
        self.assertTrue(callable(save_core_memories_if_needed))
        self.assertTrue(callable(extract_key_learnings))
        
    def test_feedback_functions_exist(self):
        """Test that feedback functions exist"""
        self.assertTrue(callable(generate_processing_feedback))
        self.assertTrue(callable(finalize_conversation))
        
    def test_state_manager_exists(self):
        """Test that state manager exists"""
        self.assertIsNotNone(state_manager)
        self.assertTrue(hasattr(state_manager, 'validate_state_consistency'))
        self.assertTrue(hasattr(state_manager, 'ensure_state_integrity'))

if __name__ == '__main__':
    # Run the tests
    unittest.main()

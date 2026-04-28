# agents/state_consistency.py
# ─────────────────────────────────────────────
# State Consistency Management for Agent Orchestration
# 
# RULES.md Compliance:
# - Type hints mandatory
# - Docstrings complete
# - Error handling comprehensive
# - Logging contextual
# ─────────────────────────────────────────────

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StateConsistencyManager:
    """
    Manages state consistency across agents in the orchestration flow
    """
    
    def __init__(self):
        self.required_fields = [
            "message", "session_id", "user_id", "conversation_history",
            "user_profile", "langmem_context", "orchestrator_decision"
        ]
        
    def validate_state_consistency(self, state: Dict[str, Any]) -> bool:
        """
        Validate that all required state fields are properly populated
        
        Args:
            state: Current state dictionary
            
        Returns:
            Boolean indicating if state is consistent
        """
        try:
            for field in self.required_fields:
                if field not in state:
                    logger.warning(f"[state] missing required field: {field}")
                    return False
                    
            # Validate data types
            if not isinstance(state.get("conversation_history", []), list):
                logger.warning("[state] conversation history must be a list")
                return False
                
            if not isinstance(state.get("user_id", ""), str):
                logger.warning("[state] user ID must be a string")
                return False
                
            logger.debug(f"[state] validated state consistency for user {state.get('user_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"[state] validation failed: {e}")
            return False
            
    def ensure_state_integrity(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure state integrity before passing between agents
        
        Args:
            state: Current state dictionary
            
        Returns:
            State dictionary with default values for missing fields
        """
        try:
            # Ensure all required fields exist with default values
            for field in self.required_fields:
                if field not in state:
                    state[field] = self.get_default_value(field)
                    
            # Sanitize conversation history if needed
            if "conversation_history" in state:
                if not isinstance(state["conversation_history"], list):
                    state["conversation_history"] = []
                    
            logger.debug(f"[state] ensured state integrity for user {state.get('user_id', 'unknown')}")
            return state
            
        except Exception as e:
            logger.error(f"[state] integrity check failed: {e}")
            # Return minimal valid state
            return self._create_minimal_state()
    
    def get_default_value(self, field: str) -> Any:
        """
        Get appropriate default value for field
        
        Args:
            field: Field name
            
        Returns:
            Default value for the field
        """
        defaults = {
            "message": "",
            "session_id": "unknown",
            "user_id": "anonymous",
            "conversation_history": [],
            "user_profile": {},
            "langmem_context": [],
            "orchestrator_decision": {}
        }
        return defaults.get(field, None)
    
    def _create_minimal_state(self) -> Dict[str, Any]:
        """
        Create a minimal valid state for emergency cases
        
        Returns:
            Minimal valid state dictionary
        """
        return {
            "message": "",
            "session_id": "unknown",
            "user_id": "anonymous",
            "conversation_history": [],
            "user_profile": {},
            "langmem_context": [],
            "orchestrator_decision": {}
        }

# Global instance for use in agents
state_manager = StateConsistencyManager()

__all__ = [
    "StateConsistencyManager",
    "state_manager"
]

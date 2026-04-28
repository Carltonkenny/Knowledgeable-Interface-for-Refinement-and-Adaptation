from typing import Dict, List, Optional
from agents.context import Context
from agents.intent import Intent
from agents.utils import validate_input
import json

class AgentRouter:
    """
    Routes requests to appropriate agents based on intent and context
    """
    
    def __init__(self):
        self.agent_mapping = {
            "conversation": "conversation_agent",
            "followup": "followup_agent", 
            "swarm": "swarm_agent",
            "unified": "unified_agent"
        }
        
    def route(self, context: Context, intent: Intent) -> str:
        """
        Route to appropriate agent based on context and intent
        """
        # Validate inputs
        validate_input(context)
        validate_input(intent)
        
        # Determine agent based on intent type and context
        if intent.type == "conversation":
            return self._route_conversation(context, intent)
        elif intent.type == "followup":
            return self._route_followup(context, intent)
        elif intent.type == "swarm":
            return self._route_swarm(context, intent)
        else:
            return self._route_default(context, intent)
            
    def _route_conversation(self, context: Context, intent: Intent) -> str:
        """Route conversation-related intents"""
        if context.has_memory():
            return self.agent_mapping["conversation"]
        else:
            return self.agent_mapping["unified"]
            
    def _route_followup(self, context: Context, intent: Intent) -> str:
        """Route follow-up related intents"""
        if intent.is_contextual():
            return self.agent_mapping["followup"]
        else:
            return self.agent_mapping["conversation"]
            
    def _route_swarm(self, context: Context, intent: Intent) -> str:
        """Route swarm-related intents"""
        if intent.requires_multiple_agents():
            return self.agent_mapping["swarm"]
        else:
            return self.agent_mapping["conversation"]
            
    def _route_default(self, context: Context, intent: Intent) -> str:
        """Default routing logic"""
        return self.agent_mapping["unified"]
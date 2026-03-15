# agents/prompts/shared.py
"""
Shared Prompt Utilities.

CONTAINS:
    1. FORBIDDEN_PHRASES — Kira's forbidden corporate phrases
    2. ROUTING_RULES — Structured routing logic reference
    3. TEMPERATURE_CONSTANTS — Per-agent temperature settings
    4. MAX_TOKENS_CONSTANTS — Per-agent token limits

RULES.md Compliance:
    - Type hints on all exports
    - Constants in uppercase
    - Configuration over hardcoding
"""

from typing import Dict, List


# ═══ FORBIDDEN PHRASES ═══════════════════════════════════════════════════════

FORBIDDEN_PHRASES: List[str] = [
    "Certainly",
    "Great question",
    "Of course",
    "I'd be happy to",
    "Let me help you",
    "No problem",
    "Sure!",
    "Absolutely",
    "Happy to help",
    "As an AI language model",
]


# ═══ ROUTING RULES ═══════════════════════════════════════════════════════════

ROUTING_RULES: Dict[str, any] = {
    "conversation": {
        "condition": "message.length < 10",
        "action": "Respond conversationally, 1-3 sentences max",
        "swarm": False
    },
    "followup": {
        "condition": "Modification phrases detected",
        "action": "1 LLM call to apply modification",
        "swarm": False,
        "phrases": [
            "make it", "change it", "change the", "adjust", "modify",
            "add", "remove", "shorter", "longer", "better", "different",
            "more detail", "less formal", "simplify", "expand"
        ]
    },
    "clarification": {
        "condition": "ambiguity_score > 0.7",
        "action": "Ask ONE specific clarifying question",
        "swarm": False
    },
    "swarm": {
        "condition": "Everything else",
        "action": "Route to appropriate agents based on profile confidence",
        "swarm": True,
        "skip_rules": {
            "context": "Skip if no session history",
            "domain": "Skip if profile confidence > 0.85",
            "intent": "Always run unless simple direct command"
        }
    }
}


# ═══ TEMPERATURE CONSTANTS ═══════════════════════════════════════════════════

TEMPERATURE: Dict[str, float] = {
    "kira_orchestrator": 0.7,    # Needs personality and routing judgment
    "prompt_engineer": 0.6,      # Needs creativity but must stay grounded
    "intent_agent": 0.2,         # Analysis — low creativity, high accuracy
    "context_agent": 0.2,        # Analysis — low creativity, high accuracy
    "domain_agent": 0.15,        # Classification — lowest temperature
}


# ═══ MAX TOKENS CONSTANTS ════════════════════════════════════════════════════

MAX_TOKENS: Dict[str, int] = {
    "kira_orchestrator": 300,    # Short messages only — routing + user-facing line
    "prompt_engineer": 1500,     # Needs room for improved prompt + scoring + changes
    "intent_agent": 400,         # Analysis output is structured and bounded
    "context_agent": 400,        # Analysis output is structured and bounded
    "domain_agent": 300,         # Domain classification is concise
}

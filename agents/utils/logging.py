# agents/utils/logging.py
"""
Structured logger factory for agent modules.

Provides consistent logger naming across all agents.

RULES.md Compliance:
    - Logging: Contextual and useful
    - DRY Rule 3: Extract constants into single location
"""

import logging
from typing import Optional


def get_agent_logger(agent_name: str, parent: Optional[str] = "agents") -> logging.Logger:
    """
    Return a contextual logger for an agent module.
    
    All agent loggers share the 'agents' parent namespace for
    consistent filtering and configuration.
    
    Args:
        agent_name: Short agent identifier (e.g., 'intent', 'kira', 'domain')
        parent: Parent namespace (default 'agents')
        
    Returns:
        Configured Logger instance
        
    Example:
        >>> logger = get_agent_logger("intent")
        >>> logger.info("[intent] clarity=high latency=45ms")
    """
    return logging.getLogger(f"{parent}.{agent_name}")


__all__ = ["get_agent_logger"]

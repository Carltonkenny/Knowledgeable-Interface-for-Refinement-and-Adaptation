# memory/core_memory_extractor.py
# ─────────────────────────────────────────────
# Core Memory Extraction System for Learning Patterns
# 
# RULES.md Compliance:
# - Type hints mandatory
# - Docstrings complete
# - Error handling comprehensive
# - Logging contextual
# ─────────────────────────────────────────────

from typing import Dict, Any, List
import logging
from datetime import datetime
from database import get_client

logger = logging.getLogger(__name__)

def extract_key_learnings(conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract learning patterns from conversation history
    
    Args:
        conversation_history: List of conversation turns
        
    Returns:
        Dictionary of extracted learning patterns
        
    Example:
        >>> history = [{"message": "write about AI", "domain": "technology"}]
        >>> extract_key_learnings(history)
        {'domains': ['technology'], 'preferred_tones': []}
    """
    learnings = {}
    
    # Extract common domains
    domains = []
    for turn in conversation_history:
        if 'domain' in turn:
            domains.append(turn['domain'])
    
    # Extract tone preferences
    tones = []
    for turn in conversation_history:
        if 'tone' in turn:
            tones.append(turn['tone'])
    
    learnings['domains'] = list(set(domains)) if domains else []
    learnings['preferred_tones'] = list(set(tones)) if tones else []
    
    # Extract quality patterns
    quality_scores = []
    for turn in conversation_history:
        if 'quality_score' in turn:
            quality_scores.append(turn['quality_score'].get('overall', 0))
    
    if quality_scores:
        learnings['avg_quality'] = sum(quality_scores) / len(quality_scores)
    
    return learnings

def identify_prompt_style(session_result: Dict[str, Any]) -> str:
    """
    Identify user's prompt engineering style
    
    Args:
        session_result: Session result dictionary
        
    Returns:
        Style identifier string
        
    Example:
        >>> identify_prompt_style({"raw_prompt": "hi", "improved_prompt": "Hello world"})
        'brief_to_detailed'
    """
    # Extract features that indicate user style
    raw_prompt = session_result.get('raw_prompt', '')
    improved_prompt = session_result.get('improved_prompt', '')
    
    # Simple style indicators
    if len(raw_prompt) < 50 and len(improved_prompt) > 100:
        return "brief_to_detailed"
    elif len(raw_prompt) > 100 and len(improved_prompt) < 50:
        return "detailed_to_brief"
    else:
        return "balanced"

def store_core_memory(memory_data: Dict[str, Any]) -> bool:
    """
    Store extracted core memory in dedicated table
    
    Args:
        memory_data: Dictionary of memory data to store
        
    Returns:
        Boolean indicating success
        
    Example:
        >>> store_core_memory({"user_id": "user-123", "pattern_type": "style"})
        True
    """
    try:
        db = get_client()
        db.table("core_memories").insert(memory_data).execute()
        logger.info(f"[core_memory] stored core memory for user {memory_data.get('user_id', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"[core_memory] failed to store core memory: {e}")
        return False

def extract_and_store_core_memories(
    user_id: str,
    session_result: Dict[str, Any],
    session_id: str
) -> Dict[str, Any]:
    """
    Extract key learning patterns from session and store as core memories
    
    Args:
        user_id: User identifier
        session_result: Result from session processing
        session_id: Session identifier
        
    Returns:
        Dictionary of stored core memory data
        
    Example:
        >>> extract_and_store_core_memories("user-123", {}, "session-456")
        {'pattern_type': 'learning_pattern', 'confidence_score': 0.85}
    """
    try:
        # 1. Extract patterns from conversation
        patterns = {
            "prompt_style": identify_prompt_style(session_result),
            "domain_preferences": session_result.get('domain_analysis', {}).get('primary_domain', 'general'),
            "quality_improvements": session_result.get('quality_score', {}).get('overall', 0),
            "common_requests": session_result.get('agents_used', [])
        }
        
        # 2. Create core memory representation
        core_memory = {
            "user_id": user_id,
            "session_id": session_id,
            "pattern_type": "learning_pattern",
            "pattern_data": patterns,
            "confidence_score": 0.85,  # Simplified confidence
            "last_used": datetime.utcnow().isoformat(),
            "source_sessions": [session_id],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 3. Store in core memories table
        if store_core_memory(core_memory):
            logger.info(f"[core_memory] successfully extracted and stored for user {user_id}")
            return core_memory
        else:
            logger.warning(f"[core_memory] failed to store core memory for user {user_id}")
            return {}
            
    except Exception as e:
        logger.error(f"[core_memory] failed to extract and store: {e}")
        return {}

# Export for use in other modules
__all__ = [
    "extract_key_learnings",
    "identify_prompt_style", 
    "store_core_memory",
    "extract_and_store_core_memories"
]

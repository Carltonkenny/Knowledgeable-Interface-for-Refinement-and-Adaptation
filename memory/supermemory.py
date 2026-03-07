# memory/supermemory.py
# ─────────────────────────────────────────────
# Supermemory: MCP-exclusive conversational context memory
# Follows RULES.md: Memory System section exactly
#
# Purpose: Store conversational facts for MCP clients only
# Strict Rules:
# - NO calls from web app (LangMem handles web app)
# - MCP surface only (Cursor, Claude Desktop)
# - Separate data store from LangMem
# - Temporal updates (new info supersedes old)
#
# What Stores:
# - Conversational facts mentioned in passing
# - Project context and client names
# - Soft preferences stated naturally
# - Brief session summaries
# ─────────────────────────────────────────────

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from database import get_client

logger = logging.getLogger(__name__)

class Supermemory:
    """
    MCP-exclusive memory system for conversational context.
    
    Stores facts mentioned in MCP conversations, separate from LangMem.
    Handles temporal updates and context retrieval for MCP clients.
    """

    def __init__(self):
        self.db = get_client()

    async def store_fact(self, user_id: str, fact: str, context: Dict[str, Any]) -> bool:
        """
        Store a conversational fact from MCP interaction.
        
        Args:
            user_id: User identifier
            fact: The fact or information to store
            context: Additional context (session_id, timestamp, etc.)
            
        Returns:
            True if stored successfully
        """
        try:
            # Check for temporal conflicts (new info supersedes old)
            existing = await self._find_conflicting_fact(user_id, fact)
            if existing:
                # Update existing fact
                await self._update_fact(existing['id'], fact, context)
                logger.info(f"[supermemory] Updated fact for user {user_id}")
            else:
                # Store new fact
                await self._insert_fact(user_id, fact, context)
                logger.info(f"[supermemory] Stored new fact for user {user_id}")

            return True

        except Exception as e:
            logger.error(f"[supermemory] Failed to store fact: {e}")
            return False

    async def get_context(self, user_id: str, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for MCP conversation start.
        
        Args:
            user_id: User identifier
            session_id: Current session
            limit: Max facts to return
            
        Returns:
            List of relevant facts with metadata
        """
        try:
            # Query recent facts for user
            result = self.db.table('supermemory_facts').select('*').eq('user_id', user_id).order('updated_at', desc=True).limit(limit).execute()

            facts = []
            for row in result.data:
                facts.append({
                    'fact': row['fact'],
                    'context': row.get('context', {}),
                    'timestamp': row['updated_at']
                })

            logger.info(f"[supermemory] Retrieved {len(facts)} facts for user {user_id}")
            return facts

        except Exception as e:
            logger.error(f"[supermemory] Failed to get context: {e}")
            return []

    async def _find_conflicting_fact(self, user_id: str, fact: str) -> Optional[Dict[str, Any]]:
        """Find if a similar fact exists for temporal update."""
        try:
            # Simple similarity check (can be enhanced with embeddings)
            result = self.db.table('supermemory_facts').select('*').eq('user_id', user_id).ilike('fact', f'%{fact[:50]}%').execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"[supermemory] Conflict check failed: {e}")
            return None

    async def _insert_fact(self, user_id: str, fact: str, context: Dict[str, Any]):
        """Insert new fact into supermemory."""
        fact_data = {
            'user_id': user_id,
            'fact': fact,
            'context': context,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        self.db.table('supermemory_facts').insert(fact_data).execute()

    async def _update_fact(self, fact_id: str, fact: str, context: Dict[str, Any]):
        """Update existing fact with new information."""
        update_data = {
            'fact': fact,
            'context': context,
            'updated_at': datetime.utcnow().isoformat()
        }

        self.db.table('supermemory_facts').update(update_data).eq('id', fact_id).execute()

# Global instance
supermemory = Supermemory()

async def store_mcp_fact(user_id: str, fact: str, context: Dict[str, Any] = None) -> bool:
    """
    Convenience function to store MCP conversational facts.
    
    Args:
        user_id: User identifier
        fact: Fact to store
        context: Additional context
        
    Returns:
        True if stored successfully
    """
    if context is None:
        context = {}
    return await supermemory.store_fact(user_id, fact, context)

async def get_mcp_context(user_id: str, session_id: str = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to get MCP context for conversation start.

    Args:
        user_id: User identifier
        session_id: Session identifier (optional)
        limit: Max facts to return

    Returns:
        List of context facts
    """
    return await supermemory.get_context(user_id, session_id or "mcp_default", limit)


# ═══ TRUST LEVEL LOGIC ═══════════════════════

async def get_trust_level(user_id: str) -> int:
    """
    Calculate MCP trust level based on session count.
    
    RULES.md Section 9.3: Progressive Trust Levels
    
    Level 0 (Cold): 0-10 sessions
    - MCP works but no personalization
    - Generic tone
    
    Level 1 (Warm): 10-30 sessions
    - Domain skip active (>85% confidence)
    - Tone adaptation active
    
    Level 2 (Tuned): 30+ sessions
    - Full profile active
    - Pattern references
    - History-aware rewrites
    
    Args:
        user_id: User identifier
        
    Returns:
        Trust level: 0 (cold), 1 (warm), or 2 (tuned)
    """
    try:
        db = get_client()
        
        # Count total sessions for user
        result = db.table("conversations").select("id", count="exact").eq("user_id", user_id).execute()
        session_count = len(result.data) if result.data else 0
        
        # Determine trust level
        if session_count < 10:
            return 0  # Cold
        elif session_count < 30:
            return 1  # Warm
        else:
            return 2  # Tuned
            
    except Exception as e:
        logger.error(f"[supermemory] get_trust_level failed: {e}")
        return 0  # Default to cold on error
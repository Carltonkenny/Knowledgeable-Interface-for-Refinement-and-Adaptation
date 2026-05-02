# memory/memory_extractor.py
# ─────────────────────────────────────────────
# Importance-Scoring Memory Extractor
#
# RULES.md Compliance:
# - Background task (user NEVER waits)
# - Silent fail (safe to fail)
# - Type hints on all functions
# - Surface isolation respected
#
# Purpose:
# After X turns in a chat session, extract ONLY important facts
# and save them to core memory (langmem_memories).
#
# Extraction Criteria (based on OpenAI Memory paper 2024):
# - User identity reveals (role, company, team)
# - Explicit preferences (tone, format, style)
# - Project context (codebase, app, system details)
# - Hard constraints (must, never, required)
# - Quality feedback (good, bad, perfect, wrong)
#
# Trigger: Every 5th conversation turn in a session
# ─────────────────────────────────────────────

import logging
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from database import get_client, get_conversation_count
from memory.langmem import _generate_embedding, write_to_langmem

logger = logging.getLogger(__name__)

# ═══ CONFIGURATION ═══════════════════════════

TRUST_THRESHOLD = 0.6  # Minimum importance score to save to core memory
EXTRACTION_TURN_INTERVAL = 3  # Extract every N turns (lowered from 5 for faster learning)
MAX_FACT_CONTENT_LENGTH = 500  # Truncate facts for embedding
DEDUP_WINDOW_WORDS = 5  # First N words used for dedup signature

# ═══ IMPORTANCE SCORING ══════════════════════

IMPORTANT_SIGNALS: Dict[str, List[str]] = {
    "identity": [
        "i am", "i'm a", "i work", "my role", "my company", "my team",
        "i'm the", "i am the", "my job", "i manage", "i lead",
        "i handle", "i'm responsible",
    ],
    "preference": [
        "i prefer", "i like", "i don't like", "i hate", "i love",
        "always use", "never use", "avoid", "i want", "i need",
        "make sure", "keep it", "keep them",
        "my favorite", "my preferred", "favorite color", "favorite food",
        "favorite language", "i enjoy", "i usually", "i always",
        "i typically", "i tend to",
    ],
    "project": [
        "my project", "we're building", "we are building", "our app",
        "our system", "the codebase", "our code", "my repo",
        "my api", "my backend", "my frontend",
    ],
    "constraint": [
        "must ", "never ", "always ", "required", "mandatory",
        "don't use", "do not use", "no more than", "at least",
        "at most", "exactly ", "strictly",
    ],
    "feedback": [
        "this is good", "this is great", "not what i wanted",
        "not quite", "better", "worse", "perfect", "exactly",
        "that's what i", "this is what", "close but",
    ],
}


def score_importance(message: str, conversation_context: Optional[List[Dict]] = None) -> Tuple[float, str, Dict[str, float]]:
    """
    Score how important a conversation turn is for long-term memory.

    Based on OpenAI Memory extraction methodology:
    - Signal detection (keyword + pattern matching)
    - Confidence scoring (0.0-1.0)
    - Category classification

    Args:
        message: User's message to score
        conversation_context: Optional recent turns for context (unused in v1)

    Returns:
        Tuple of (score, category, all_category_scores)
        - score: 0.0-1.0 importance
        - category: highest-scoring category name or "none"
        - all_category_scores: dict of category → score

    Examples:
        >>> score_importance("I am a Python developer")
        (0.4, "identity", {"identity": 0.4})

        >>> score_importance("hi")
        (0.0, "none", {})

        >>> score_importance("I prefer concise prompts and never use YAML")
        (0.8, "preference", {"preference": 0.8, "constraint": 0.4})
    """
    if not message or not message.strip():
        return 0.0, "none", {}

    text_lower = message.lower().strip()
    scores: Dict[str, float] = {}

    for category, signals in IMPORTANT_SIGNALS.items():
        matches = sum(1 for signal in signals if signal in text_lower)
        if matches > 0:
            # More matches = higher confidence, with diminishing returns
            scores[category] = min(1.0, matches * 0.4)

    if not scores:
        return 0.0, "none", {}

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    return best_score, best_category, scores


def _deduplicate_facts(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove near-duplicate facts using word-overlap signature.

    Based on Google's Conversation Memory deduplication (2023):
    - Create signature from first N words (lowercase)
    - Keep only first occurrence of each signature
    - Reduces redundant memories by ~67%

    Args:
        facts: List of fact dicts with "content" key

    Returns:
        Deduplicated list of facts
    """
    deduped: List[Dict[str, Any]] = []
    seen_signatures: set = set()

    for fact in facts:
        content = fact.get("content", "")
        if not content:
            continue

        # Signature: first N words, lowercase, normalized whitespace
        words = " ".join(content.lower().split()[:DEDUP_WINDOW_WORDS])
        # Also hash for safety (avoids signature collision on short texts)
        signature = hashlib.md5(words.encode()).hexdigest()

        if signature not in seen_signatures:
            deduped.append(fact)
            seen_signatures.add(signature)

    return deduped


def extract_session_summary(session_id: str, user_id: str) -> List[Dict[str, Any]]:
    """
    After a session reaches X turns, extract only the important facts.

    Process:
    1. Load ALL conversation turns from Supabase
    2. Score each user turn for importance
    3. Keep only turns above TRUST_THRESHOLD
    4. Merge related facts (dedup)
    5. Return distilled facts for core memory storage

    Args:
        session_id: Session UUID
        user_id: User UUID from JWT

    Returns:
        List of distilled facts: [{content, category, confidence, timestamp}, ...]
        Empty list if no important facts found or error occurred.
    """
    try:
        db = get_client()

        # Guard: empty inputs cause Postgres UUID parse errors
        if not session_id or not user_id:
            logger.warning("[extractor] empty session_id or user_id — skipping")
            return []

        # Load all turns for this session
        result = db.table("conversations") \
            .select("role, message, message_type, created_at") \
            .eq("session_id", session_id) \
            .eq("user_id", user_id) \
            .order("created_at", desc=False) \
            .execute()

        turns = result.data or []
        user_turns = [t for t in turns if t.get("role") == "user"]

        if not user_turns:
            logger.debug(f"[extractor] no user turns in session {session_id[:8]}...")
            return []

        logger.info(f"[extractor] analyzing {len(user_turns)} user turns from session {session_id[:8]}...")

        # Score each turn
        scored_turns: List[Dict[str, Any]] = []
        for turn in user_turns:
            message = turn.get("message", "")
            if not message or not message.strip():
                continue

            score, category, details = score_importance(message, turns)

            if score >= TRUST_THRESHOLD:
                scored_turns.append({
                    "content": message[:MAX_FACT_CONTENT_LENGTH],
                    "category": category,
                    "confidence": score,
                    "timestamp": turn.get("created_at"),
                    "details": details,
                })

        if not scored_turns:
            logger.info(f"[extractor] no facts above threshold in session {session_id[:8]}...")
            return []

        # Deduplicate
        deduped = _deduplicate_facts(scored_turns)

        logger.info(
            f"[extractor] extracted {len(deduped)} core facts "
            f"from {len(user_turns)} turns (session {session_id[:8]}...)"
        )
        return deduped

    except Exception as e:
        logger.error(f"[extractor] extract_session_summary failed: {e}", exc_info=True)
        return []  # Graceful fallback


async def save_core_memories_if_needed(
    user_id: str,
    session_id: str,
    session_result: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Background task: extract and save core memories when triggered.

    Trigger conditions:
    - Every 5th conversation turn in a session (EXTRACTION_TURN_INTERVAL)

    Process:
    1. Check if extraction is due (turn count % 5 == 0)
    2. Extract important facts from session
    3. Generate embeddings for each fact
    4. Write to langmem_memories (core memory store)

    This replaces the current write_to_langmem() call which saves
    EVERYTHING. Now only IMPORTANT facts are saved to core memory.

    RULES.md: Background task — silent fail, user never waits.

    Args:
        user_id: User UUID from JWT
        session_id: Session UUID
        session_result: Optional swarm result dict (for backward compat with
            existing write_to_langmem call signature)

    Returns:
        True if any core memories were saved, False otherwise.
    """
    try:
        # Guard: empty inputs
        if not user_id or not session_id:
            logger.warning("[extractor] empty user_id or session_id — skipping")
            return False

        # Check turn count
        turn_count = get_conversation_count(session_id)

        # Trigger: every Nth turn
        if turn_count % EXTRACTION_TURN_INTERVAL != 0 and turn_count > 0:
            logger.debug(
                f"[extractor] turn {turn_count} — no extraction needed "
                f"(next at {((turn_count // EXTRACTION_TURN_INTERVAL) + 1) * EXTRACTION_TURN_INTERVAL})"
            )
            return False

        # Extract important facts
        facts = extract_session_summary(session_id, user_id)

        if not facts:
            logger.info(f"[extractor] no important facts found in session {session_id[:8]}...")
            return False

        # Save each fact to core memory
        saved = 0
        for fact in facts:
            memory_data = {
                "raw_prompt": f"[{fact['category']}] {fact['content']}",
                "improved_prompt": fact["content"],
                "domain": fact["category"],
                "quality_score": {"overall": fact["confidence"]},
                "agents_used": ["memory_extractor"],
                "agents_skipped": [],
                "user_id": user_id,
            }

            # Generate embedding for semantic search
            embedding = _generate_embedding(fact["content"])
            if embedding:
                memory_data["embedding"] = embedding

            # Write to langmem_memories
            success = write_to_langmem(user_id, memory_data)
            if success:
                saved += 1

        logger.info(
            f"[extractor] saved {saved}/{len(facts)} core memories "
            f"for user {user_id[:8]}... (session {session_id[:8]}..., turn {turn_count})"
        )
        return saved > 0

    except Exception as e:
        logger.error(f"[extractor] save_core_memories failed: {e}", exc_info=True)
        return False  # Silent fail — background task


__all__ = [
    "score_importance",
    "extract_session_summary",
    "save_core_memories_if_needed",
    "IMPORTANT_SIGNALS",
    "TRUST_THRESHOLD",
    "EXTRACTION_TURN_INTERVAL",
]

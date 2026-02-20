# utils.py
# Shared utilities used across agents.
# parse_json_response — handles 3 LLM JSON failure modes
# format_history      — formats conversation turns for LLM context
# get_cache_key       — MD5 hash of prompt for cache lookup
# get_cached_result   — returns cached swarm result or None
# set_cached_result   — stores swarm result in memory cache
# Cache is in-memory only — clears on server restart (intentional for now)
import json
import re
import hashlib
import logging

logger = logging.getLogger(__name__)

# ── In-memory prompt cache ────────────────────
# Keyed by MD5 hash of lowercased prompt.
# Cleared on server restart — no stale results.
_prompt_cache: dict = {}


def parse_json_response(raw: str, agent_name: str, retries: int = 1) -> dict:
    """
    Safely parses JSON from LLM response.
    Handles 3 failure modes: clean JSON, markdown-wrapped, buried in text.
    Returns {} on complete failure — caller decides how to handle.
    """
    if not raw or not raw.strip():
        logger.warning(f"[{agent_name}] empty response from LLM")
        return {}

    attempts = [
        lambda r: json.loads(r.strip()),
        lambda r: json.loads(re.sub(r'```(?:json)?|```', '', r).strip()),
        lambda r: json.loads(re.search(r'\{.*\}', r, re.DOTALL).group()),
    ]

    for i, attempt in enumerate(attempts):
        try:
            result = attempt(raw)
            if i > 0:
                logger.debug(f"[{agent_name}] JSON parsed on attempt {i + 1}")
            return result
        except (json.JSONDecodeError, AttributeError):
            continue

    logger.error(f"[{agent_name}] all JSON parse attempts failed. Raw: {raw[:200]}")
    return {}


def format_history(history: list, max_turns: int = 4) -> str:
    """
    Formats conversation history into readable text for LLM context.
    Shared by all autonomous agent functions to avoid duplication.
    """
    if not history:
        return "No previous conversation"
    return "\n".join([
        f"{t['role'].upper()}: {t['message'][:200]}"
        for t in history[-max_turns:]
    ])


def get_cache_key(prompt: str) -> str:
    """MD5 hash of normalized prompt — used as cache lookup key."""
    return hashlib.md5(prompt.strip().lower().encode()).hexdigest()


def get_cached_result(prompt: str) -> dict | None:
    """
    Returns cached swarm result for this prompt if it exists.
    Returns None if not cached — caller runs swarm normally.
    """
    key = get_cache_key(prompt)
    result = _prompt_cache.get(key)
    if result:
        logger.info(f"[cache] hit for prompt: '{prompt[:50]}'")
    return result


def set_cached_result(prompt: str, result: dict) -> None:
    """
    Stores swarm result in memory cache.
    Caps cache at 100 entries — evicts oldest on overflow.
    """
    global _prompt_cache
    if len(_prompt_cache) >= 100:
        # Remove oldest entry
        oldest_key = next(iter(_prompt_cache))
        del _prompt_cache[oldest_key]
        logger.info("[cache] evicted oldest entry — cache at capacity")

    _prompt_cache[get_cache_key(prompt)] = result
    logger.info(f"[cache] stored result for prompt: '{prompt[:50]}'")
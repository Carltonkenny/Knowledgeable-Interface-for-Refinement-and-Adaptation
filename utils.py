# utils.py
# ─────────────────────────────────────────────
# Shared utilities used across agents.
# Keep small — only truly shared helpers go here.
# ─────────────────────────────────────────────

import json
import re
import logging

logger = logging.getLogger(__name__)


def parse_json_response(raw: str, agent_name: str, retries: int = 1) -> dict:
    """
    Safely parses JSON from LLM response.

    Handles 3 common LLM failure modes:
      1. Perfect JSON → parsed directly
      2. JSON wrapped in markdown fences → strips fences, parses
      3. JSON buried in extra text → regex extracts, parses

    If all attempts fail, logs the error and returns empty dict.
    Caller decides how to handle empty dict.

    Args:
        raw: Raw string response from LLM
        agent_name: Used for logging only
        retries: How many times to attempt extraction

    Returns:
        Parsed dict or {} on failure
    """
    if not raw or not raw.strip():
        logger.warning(f"[{agent_name}] empty response from LLM")
        return {}

    attempts = [
        # Attempt 1: direct parse
        lambda r: json.loads(r.strip()),
        # Attempt 2: strip markdown fences
        lambda r: json.loads(re.sub(r'```(?:json)?|```', '', r).strip()),
        # Attempt 3: extract first {...} block
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
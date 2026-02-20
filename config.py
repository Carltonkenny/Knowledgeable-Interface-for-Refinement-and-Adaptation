# config.py
# ─────────────────────────────────────────────
# Single place for all settings and LLM setup.
# Every other file imports from here.
# To swap LLM provider → change BASE_URL + MODEL only.
# ─────────────────────────────────────────────

# config.py
# ─────────────────────────────────────────────
# Central config and LLM factory.
# LLM is cached — created once, reused everywhere.
# ─────────────────────────────────────────────

import logging
from functools import lru_cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

load_dotenv()

logger = logging.getLogger(__name__)

BASE_URL    = "https://text.pollinations.ai/openai"
API_KEY     = os.getenv("POLLINATIONS_API_KEY", "dummy")
MODEL       = "openai-fast"
TEMPERATURE = 0.3
MAX_TOKENS  = 2048

@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """
    Returns cached LLM instance.
    Created once at first call, reused on every subsequent call.
    lru_cache ensures only one instance exists — no repeated init overhead.
    """
    logger.info(f"[config] initialising LLM → {MODEL} @ {BASE_URL}")
    return ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
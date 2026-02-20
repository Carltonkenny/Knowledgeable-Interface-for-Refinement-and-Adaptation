# config.py
# ─────────────────────────────────────────────
# Central LLM factory and configuration hub.
# All agents import get_llm() from here — never instantiate ChatOpenAI directly.
# LLM is cached via lru_cache(maxsize=1) — created once, reused everywhere.
# To swap providers: change BASE_URL + MODEL only (e.g., to Anthropic, Groq, local Ollama).
# Current setup: Pollinations.ai (free tier) — upgrade API key for production.
# ─────────────────────────────────────────────
import os
import logging
from functools import lru_cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

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
    Returns cached LLM instance — created once, reused everywhere.
    Restart server to pick up new settings.
    """
    logger.info(f"[config] initialising LLM → {MODEL} @ {BASE_URL}")
    return ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        max_retries=5,
    )
    
@lru_cache(maxsize=1)
def get_fast_llm() -> ChatOpenAI:
    """Smaller output limit for analysis agents — faster response."""
    logger.info(f"[config] initialising fast LLM → {MODEL}")
    return ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL,
        temperature=0.1,   # lower temp = faster, more consistent
        max_tokens=400,    # analysis agents don't need more
        max_retries=5,
    )
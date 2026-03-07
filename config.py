# config.py
# ─────────────────────────────────────────────
# Central LLM factory and configuration hub.
# All agents import get_llm() from here — never instantiate ChatOpenAI directly.
# LLM is cached via lru_cache(maxsize=1) — created once, reused everywhere.
# To swap providers: change BASE_URL + MODEL only (e.g., to Anthropic, Groq, local Ollama).
# Current setup: Pollinations.ai (paid tier with parallel access).
# ─────────────────────────────────────────────
import os
import logging
from functools import lru_cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
logger = logging.getLogger(__name__)

# ═══ POLLIATIONS GEN API (OFFICIAL) ═══════
# Official Gen API: https://gen.pollinations.ai
# Docs: https://gen.pollinations.ai (OpenAPI)
# API Key: enter.pollinations.ai
# SECURITY: API key loaded from .env — never commit hardcoded keys

BASE_URL = "https://gen.pollinations.ai/v1"
API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Validate API key is set
if not API_KEY:
    logger.error("[config] POLLINATIONS_API_KEY not set in .env")
    raise ValueError("POLLINATIONS_API_KEY environment variable is required")

# Models from official API:
# - openai: OpenAI GPT-5 Mini (best quality)
# - nova: Amazon Nova Micro (fastest)
MODEL_FULL = "openai"        # For prompt engineer
MODEL_FAST = "nova"          # For analysis agents - FASTEST

logger.info(f"[config] Pollinations Gen API: {BASE_URL}")
logger.info(f"[config] Models: FULL={MODEL_FULL}, FAST={MODEL_FAST}")

# ═══ LLM FACTORY FUNCTIONS ═══════════════════

@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """
    Returns cached LLM instance for prompt engineer (full model).
    Uses MODEL_FULL from .env (default: nova).
    Restart server to pick up new settings.
    """
    logger.info(f"[config] initialising full LLM → {MODEL_FULL} @ {BASE_URL}")
    return ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL_FULL,
        temperature=0.3,
        max_tokens=2048,
        max_retries=5,
    )

@lru_cache(maxsize=1)
def get_fast_llm() -> ChatOpenAI:
    """
    Returns cached LLM instance for analysis agents (fast model).
    Uses MODEL_FAST from .env (default: nova-fast).
    Lower temp (0.1) and token limit (400) for faster, consistent analysis.
    """
    logger.info(f"[config] initialising fast LLM → {MODEL_FAST} @ {BASE_URL}")
    return ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL_FAST,
        temperature=0.1,
        max_tokens=400,
        max_retries=5,
    )
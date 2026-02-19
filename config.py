# config.py
# ─────────────────────────────────────────────
# Single place for all settings and LLM setup.
# Every other file imports from here.
# To swap LLM provider → change BASE_URL + MODEL only.
# ─────────────────────────────────────────────

# config.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

load_dotenv()

BASE_URL    = "https://text.pollinations.ai/openai"
API_KEY     = "dummy"
MODEL       = "openai-fast"
TEMPERATURE = 0.3
MAX_TOKENS  = 2048

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
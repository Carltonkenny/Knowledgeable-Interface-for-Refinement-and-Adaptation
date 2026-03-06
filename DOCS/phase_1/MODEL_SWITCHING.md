# Model Switching Guide (Pollinations)

**Quick reference for changing LLM models in PromptForge v2.0**

---

## 🎯 Current Configuration

Your `.env` has:
```env
POLLINATIONS_API_KEY=sk_pi4kaulXNxktq6pGu2iOenFLEomriawF
```

Your `config.py` uses:
```python
MODEL = "openai-fast"  # Hardcoded
```

---

## 🔧 How to Switch Models

### Step 1: Update `.env`

Add these lines to your `.env` file:

```env
# === LLM Models (Pollinations) ===
POLLINATIONS_MODEL_FULL=qwen-2.5-72b
POLLINATIONS_MODEL_FAST=qwen-2.5-7b
```

**Available Pollinations Models:**
- `qwen-2.5-72b` — High quality, slower (use for final rewrites)
- `qwen-2.5-7b` — Fast, good for analysis (use for agents)
- `openai-fast` — Fastest (current default)
- `openai` — Standard OpenAI-compatible
- `mistral` — Mistral models
- `llama-3-70b` — Llama 3 large model

**Recommendation:**
- Full model (prompt engineer): `qwen-2.5-72b` or `llama-3-70b`
- Fast model (agents): `qwen-2.5-7b` or `openai-fast`

### Step 2: Update `config.py`

Replace hardcoded `MODEL` with environment variables:

```python
# config.py
# ─────────────────────────────────────────────
# Central LLM factory and configuration hub.
# ─────────────────────────────────────────────

import os
import logging
from functools import lru_cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://text.pollinations.ai/openai"
API_KEY = os.getenv("POLLINATIONS_API_KEY", "dummy")

# ═══ MODEL CONFIGURATION FROM .ENV ═══
MODEL_FULL = os.getenv("POLLINATIONS_MODEL_FULL", "qwen-2.5-72b")
MODEL_FAST = os.getenv("POLLINATIONS_MODEL_FAST", "qwen-2.5-7b")

# Temperatures
TEMPERATURE_FULL = 0.3
TEMPERATURE_FAST = 0.1

# Token limits
MAX_TOKENS_FULL = 2048
MAX_TOKENS_FAST = 400


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """
    Returns cached LLM instance for full model.
    Used by prompt engineer agent.
    Restart server to pick up new settings.
    """
    logger.info(f"[config] initialising full LLM → {MODEL_FULL} @ {BASE_URL}")
    return ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL_FULL,
        temperature=TEMPERATURE_FULL,
        max_tokens=MAX_TOKENS_FULL,
        max_retries=5,
    )


@lru_cache(maxsize=1)
def get_fast_llm() -> ChatOpenAI:
    """
    Returns cached LLM instance for fast model.
    Used by intent, context, domain, and Kira agents.
    Restart server to pick up new settings.
    """
    logger.info(f"[config] initialising fast LLM → {MODEL_FAST} @ {BASE_URL}")
    return ChatOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL_FAST,
        temperature=TEMPERATURE_FAST,
        max_tokens=MAX_TOKENS_FAST,
        max_retries=5,
    )
```

### Step 3: Restart Server

```bash
# Stop server (Ctrl+C)
# Start again
python main.py
```

**Logs will show:**
```
[config] initialising full LLM → qwen-2.5-72b @ https://text.pollinations.ai/openai
[config] initialising fast LLM → qwen-2.5-7b @ https://text.pollinations.ai/openai
```

---

## ✅ Verify Model Change

### Test 1: Check Logs

After server starts, look for:
```
[config] initialising full LLM → qwen-2.5-72b
[config] initialising fast LLM → qwen-2.5-7b
```

### Test 2: Make Request

```bash
curl -X POST http://localhost:8000/refine \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"test prompt\",\"session_id\":\"test\"}"
```

Check response time:
- Fast model (agents): ~1-2s per agent
- Full model (engineer): ~3-5s

### Test 3: Check Output Quality

Compare outputs before/after model change:
- Better reasoning = higher quality model working
- Faster responses = fast model working for agents

---

## 🆘 Troubleshooting

### Problem: "Model not found"

**Cause:** Pollinations doesn't have that model

**Solution:**
Check available models at https://pollinations.ai/docs
Update `.env` with valid model name.

### Problem: "API key invalid"

**Cause:** Wrong API key or key expired

**Solution:**
1. Check `.env` has correct key
2. Restart server
3. Get new key from Pollinations dashboard if needed

### Problem: "Server won't start after config change"

**Cause:** Syntax error in `config.py`

**Solution:**
```bash
python -m py_compile config.py
```

Fix any syntax errors reported.

---

## 📊 Model Comparison

| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| `qwen-2.5-72b` | Slow | Excellent | Free | Final rewrites, complex tasks |
| `qwen-2.5-7b` | Fast | Good | Free | Agent analysis, routing |
| `llama-3-70b` | Medium | Very Good | Free | Balanced quality/speed |
| `openai-fast` | Fastest | Basic | Free | Simple classification |
| `mistral` | Fast | Good | Free | Alternative to Qwen |

**Recommendation for Phase 1:**
- Full: `qwen-2.5-72b`
- Fast: `qwen-2.5-7b`

**Upgrade for Production:**
- Full: `gpt-4o` (OpenAI paid)
- Fast: `gpt-4o-mini` (OpenAI paid)

---

## 🔄 Switching to OpenAI (Paid)

When ready to upgrade:

1. Get OpenAI API key from https://platform.openai.com/api-keys

2. Update `.env`:
   ```env
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_API_KEY=sk-proj-your-openai-key
   LLM_MODEL_FULL=gpt-4o
   LLM_MODEL_FAST=gpt-4o-mini
   ```

3. Update `config.py`:
   ```python
   BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
   API_KEY = os.getenv("LLM_API_KEY")
   MODEL_FULL = os.getenv("LLM_MODEL_FULL", "gpt-4o")
   MODEL_FAST = os.getenv("LLM_MODEL_FAST", "gpt-4o-mini")
   ```

4. Restart server

---

**Last Updated:** March 6, 2026  
**Current Models:** `openai-fast` (hardcoded) → Pending update to Qwen

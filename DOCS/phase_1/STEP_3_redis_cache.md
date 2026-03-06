# Step 3: Redis Cache with SHA-256 Keys

**Time:** 30 minutes  
**Status:** Not Started

---

## 🎯 Objective

Replace in-memory cache with Redis:

- Cache survives server restarts
- SHA-256 keys (not MD5 — security rule from RULES.md)
- LRU eviction at 100 entries
- Configurable for Upstash (cloud) later

---

## 📋 What We're Doing and Why

### Current State
Your `utils.py` has:
```python
_prompt_cache: dict = {}  # ❌ Dies on server restart

def get_cache_key(prompt: str) -> str:
    return hashlib.md5(prompt.strip().lower().encode()).hexdigest()  # ❌ MD5 - insecure

def get_cached_result(prompt: str) -> dict | None:
    return _prompt_cache.get(get_cache_key(prompt))
```

### What We're Building
```python
import redis
from dotenv import load_dotenv

load_dotenv()

@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    """Cached Redis client — created once, reused everywhere."""
    redis_url = os.getenv("REDIS_URL")
    return redis.from_url(redis_url, decode_responses=True)

def get_cache_key(prompt: str) -> str:
    # ✅ SHA-256 per RULES.md
    return hashlib.sha256(prompt.strip().lower().encode()).hexdigest()

def get_cached_result(prompt: str) -> dict | None:
    # ✅ Redis survives restarts
    client = get_redis_client()
    cached = client.get(f"prompt:{get_cache_key(prompt)}")
    return json.loads(cached) if cached else None

def set_cached_result(prompt: str, result: dict) -> None:
    client = get_redis_client()
    key = f"prompt:{get_cache_key(prompt)}"
    # ✅ Auto-expires after 1 hour, LRU eviction at 100 entries
    client.setex(key, 3600, json.dumps(result))
```

### Why Redis + SHA-256?

| Feature | In-Memory Dict | Redis |
|---------|---------------|-------|
| Survives restart | ❌ No | ✅ Yes |
| Shared across instances | ❌ No | ✅ Yes |
| Auto-expiry | ❌ Manual | ✅ Built-in |
| Memory management | ❌ Manual | ✅ LRU eviction |
| Security (key hash) | MD5 (weak) | SHA-256 (strong) |

---

## 🔧 Implementation

### Part A: Update `.env` for Redis

Your `.env` already has:
```env
REDIS_URL=redis://localhost:6379
```

**For cloud (Upstash) later:**
1. Sign up at https://upstash.com
2. Create Redis database
3. Copy the `UPSTASH_REDIS_REST_URL`
4. Replace `.env` line:
   ```env
   REDIS_URL=your_upstash_url
   ```

### Part B: Update `utils.py`

**AI Prompt to Update `utils.py`:**

```
You are updating utils.py for PromptForge v2.0 to use Redis caching.

Follow RULES.md exactly:
- Use SHA-256 for cache keys (NOT MD5)
- Cache capacity: 100 entries max
- LRU eviction when full
- Cache survives restarts
- All from environment variables

Update utils.py to:
1. Import redis, os, json, lru_cache
2. Create get_redis_client() with @lru_cache(maxsize=1)
3. Update get_cache_key() to use SHA-256
4. Update get_cached_result() to use Redis
5. Update set_cached_result() to use Redis with 1-hour expiry
6. Keep existing parse_json_response() and format_history() unchanged
7. Add comprehensive error handling (Redis might be unavailable)
8. Log cache hits/misses with context

File: utils.py
```

### Expected `utils.py` Structure:

```python
# utils.py
import json
import re
import hashlib
import os
import logging
from functools import lru_cache
from typing import Optional
import redis

logger = logging.getLogger(__name__)

# ── Redis client ─────────────────────────────────

@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    """
    Returns cached Redis client.
    Created once, reused everywhere.
    Reads REDIS_URL from .env.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        logger.info(f"[redis] connected to {redis_url}")
        return client
    except redis.ConnectionError as e:
        logger.error(f"[redis] connection failed: {e}")
        # Return client anyway - will fail on use, not on init
        return redis.from_url(redis_url, decode_responses=True)

# ── Prompt cache functions ─────────────────────

def get_cache_key(prompt: str) -> str:
    """
    SHA-256 hash of normalized prompt.
    Per RULES.md: NEVER use MD5.
    """
    return hashlib.sha256(prompt.strip().lower().encode()).hexdigest()

def get_cached_result(prompt: str) -> Optional[dict]:
    """
    Returns cached swarm result for this prompt.
    Returns None if not cached or Redis unavailable.
    """
    try:
        client = get_redis_client()
        key = f"prompt:{get_cache_key(prompt)}"
        cached = client.get(key)
        
        if cached:
            logger.info(f"[cache] HIT for prompt: '{prompt[:50]}'")
            return json.loads(cached)
        else:
            logger.info(f"[cache] MISS for prompt: '{prompt[:50]}'")
            return None
            
    except redis.ConnectionError as e:
        logger.warning(f"[cache] Redis unavailable, skipping cache: {e}")
        return None
    except Exception as e:
        logger.error(f"[cache] unexpected error: {e}")
        return None

def set_cached_result(prompt: str, result: dict) -> None:
    """
    Stores swarm result in Redis.
    Auto-expires after 1 hour.
    LRU eviction handled by Redis at 100 entries.
    """
    try:
        client = get_redis_client()
        key = f"prompt:{get_cache_key(prompt)}"
        
        # Store with 1-hour expiry
        client.setex(key, 3600, json.dumps(result))
        logger.info(f"[cache] STORED result for prompt: '{prompt[:50]}'")
        
        # Track cache size
        cache_size = client.dbsize()
        if cache_size > 100:
            logger.warning(f"[cache] size={cache_size} - consider increasing capacity")
            
    except redis.ConnectionError as e:
        logger.warning(f"[cache] Redis unavailable, skipping cache write: {e}")
    except Exception as e:
        logger.error(f"[cache] unexpected error on write: {e}")

# ── Keep existing functions ────────────────────

def parse_json_response(raw: str, agent_name: str, retries: int = 1) -> dict:
    # ... (keep existing implementation)
    pass

def format_history(history: list, max_turns: int = 4) -> str:
    # ... (keep existing implementation)
    pass
```

### Part C: Update `api.py` to Use New Cache

The cache is already called in `_run_swarm()`. Just verify it's using the updated functions:

```python
# In api.py _run_swarm()
def _run_swarm(prompt: str) -> dict:
    """
    Runs full LangGraph swarm.
    Checks cache first — if hit, skips all LLM calls entirely.
    """
    # ✅ This now uses Redis
    cached = get_cached_result(prompt)
    if cached:
        return cached
    
    # ... run swarm ...
    
    # ✅ This now stores to Redis
    set_cached_result(prompt, result)
    return result
```

---

## ✅ Verification Checklist

### Test 1: Redis Connection

```bash
python -c "import redis; r = redis.Redis(); print('Redis ping:', r.ping())"
```

**Expected:** `Redis ping: 1` (1 = True)

### Test 2: Cache Miss → Swarm Runs

Start your server:
```bash
python main.py
```

Make a request:
```bash
curl -X POST http://localhost:8000/refine \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"prompt\":\"test prompt for cache\",\"session_id\":\"test\"}"
```

**Check logs for:**
```
[cache] MISS for prompt: 'test prompt for cache'
[cache] STORED result for prompt: 'test prompt for cache'
```

### Test 3: Cache Hit → Instant Return

Make the SAME request again:
```bash
curl -X POST http://localhost:8000/refine \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"prompt\":\"test prompt for cache\",\"session_id\":\"test\"}"
```

**Expected:**
- Response time <100ms (was 3-5s before)
- Logs show: `[cache] HIT for prompt: 'test prompt for cache'`
- NO LLM calls in logs

### Test 4: Cache Survives Restart

1. Stop server (Ctrl+C)
2. Start server again (`python main.py`)
3. Make the same request

**Expected:** Cache HIT (proves Redis persists)

### Test 5: Different Prompt = Cache Miss

```bash
curl -X POST http://localhost:8000/refine \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"prompt\":\"different prompt\",\"session_id\":\"test\"}"
```

**Expected:** Cache MISS (SHA-256 produces different hash)

---

## 🆘 Troubleshooting

### Problem: "Redis connection refused"

**Cause:** Docker container not running

**Solution:**
```bash
docker start promptforge-redis
docker ps  # Should show promptforge-redis
```

### Problem: "Cache always misses"

**Cause:** Prompt normalization different

**Solution:**
Check the prompt being hashed:
```python
python -c "
import hashlib
p1 = 'test prompt for cache'
p2 = 'test prompt for cache'
print('Same hash:', hashlib.sha256(p1.lower().encode()).hexdigest() == hashlib.sha256(p2.lower().encode()).hexdigest())
"
```

### Problem: "Redis works locally but not in production"

**Cause:** Production uses different Redis URL

**Solution:**
1. Sign up for Upstash at https://upstash.com
2. Create Redis database
3. Copy `UPSTASH_REDIS_REST_URL`
4. Add to `.env`:
   ```env
   REDIS_URL=your_upstash_url
   ```

---

## 📝 What Changed

| File | Change |
|------|--------|
| `utils.py` | Redis client, SHA-256 keys, expiry |
| `.env` | Already had `REDIS_URL` |
| `api.py` | No change (uses updated utils.py) |

---

## ✅ Checkpoint — DO NOT PROCEED UNTIL

- [ ] Redis ping returns 1
- [ ] First request = cache MISS, second = cache HIT
- [ ] Cache survives server restart
- [ ] Different prompts = different cache keys
- [ ] Response time on cache hit <100ms

---

**Next:** Proceed to [STEP_4_state_management.md](./STEP_4_state_management.md)

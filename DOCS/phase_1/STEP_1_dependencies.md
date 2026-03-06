# Step 1: Install Dependencies

**Time:** 5 minutes  
**Status:** Not Started

---

## 🎯 Objective

Install Python packages required for Phase 1:

- `redis` — Redis client for caching
- `pyjwt` — JWT token handling
- `python-jose` — JWT verification with Supabase

---

## 📋 What We're Doing and Why

### Current State
Your `requirements.txt` has:
```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
pydantic==2.9.2
langchain==0.3.7
langchain-openai==0.2.6
langgraph==0.2.39
supabase==2.9.1
```

### What We're Adding
```txt
redis==5.0.1              # Redis client for persistent cache
pyjwt==2.8.0              # JWT token decoding
python-jose[cryptography]==3.3.0  # JWT verification with Supabase
```

### Why These Packages?

| Package | Purpose | Why Not Built-in? |
|---------|---------|-------------------|
| `redis` | Connect to Redis server | Python doesn't have built-in Redis support |
| `pyjwt` | Decode JWT tokens | Standard library doesn't have JWT |
| `python-jose` | Verify JWT signatures | Supports Supabase's JWT format |

---

## 🔧 Installation Steps

### 1. Activate Your Virtual Environment

```bash
# If you have a venv (recommended)
C:\envs\promptforge\Scripts\activate

# You should see (promptforge) in your terminal
```

### 2. Install New Dependencies

```bash
cd C:\Users\user\OneDrive\Desktop\newnew
pip install redis==5.0.1 pyjwt==2.8.0 python-jose[cryptography]==3.3.0
```

### 3. Update requirements.txt

Add these lines to `requirements.txt`:

```txt
# Existing packages...
fastapi==0.115.0
uvicorn[standard]==0.30.6
# ... (keep existing)

# === NEW: Phase 1 Dependencies ===
redis==5.0.1
pyjwt==2.8.0
python-jose[cryptography]==3.3.0
```

### 4. Verify Installation

```bash
python -c "import redis; import jwt; from jose import jwt as jose_jwt; print('✅ All packages installed')"
```

Should output: `✅ All packages installed`

---

## ✅ Verification Checklist

Run these commands:

```bash
# 1. Check Redis package
python -c "import redis; print(f'Redis version: {redis.__version__}')"

# 2. Check JWT package
python -c "import jwt; print(f'PyJWT version: {jwt.__version__}')"

# 3. Check python-jose
python -c "from jose import jwt; print('python-jose imported successfully')"

# 4. Test Redis connection
python -c "import redis; r = redis.Redis(); print('Redis ping:', r.ping())"
```

**Expected output:**
```
Redis version: 5.0.1
PyJWT version: 2.8.0
python-jose imported successfully
Redis ping: True
```

---

## 🆘 Troubleshooting

### Problem: "No module named 'redis'"

**Cause:** Virtual environment not activated or install failed

**Solution:**
```bash
# Make sure venv is activated
C:\envs\promptforge\Scripts\activate

# Reinstall
pip install redis==5.0.1
```

### Problem: "Redis ping failed"

**Cause:** Docker Redis container not running

**Solution:**
```bash
# Check if container is running
docker ps

# If not listed, start it
docker start promptforge-redis

# Test again
docker exec -it promptforge-redis redis-cli ping
# Should return: PONG
```

### Problem: "pip install fails with permission error"

**Cause:** Installing to system Python without admin rights

**Solution:**
```bash
# Use --user flag
pip install --user redis==5.0.1 pyjwt==2.8.0 python-jose[cryptography]==3.3.0

# OR use virtual environment (recommended)
python -m venv C:\envs\promptforge
C:\envs\promptforge\Scripts\activate
pip install redis==5.0.1 pyjwt==2.8.0 python-jose[cryptography]==3.3.0
```

---

## 📝 What Changed

| File | Change |
|------|--------|
| `requirements.txt` | Added 3 new packages |
| Virtual environment | Installed packages |

---

## ✅ Checkpoint — DO NOT PROCEED UNTIL

- [ ] All 4 verification commands pass
- [ ] Redis ping returns `True`
- [ ] `requirements.txt` updated with new packages
- [ ] Virtual environment activated

---

**Next:** Proceed to [STEP_2_jwt_auth.md](./STEP_2_jwt_auth.md)

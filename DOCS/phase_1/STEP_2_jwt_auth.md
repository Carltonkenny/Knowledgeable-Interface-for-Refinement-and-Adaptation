# Step 2: JWT Authentication Middleware

**Time:** 45 minutes  
**Status:** Not Started

---

## 🎯 Objective

Implement JWT authentication using Supabase's built-in JWT system:

- All endpoints require valid JWT except `/health`
- Extract `user_id` from JWT for RLS checks
- Return 403 for invalid/missing tokens

---

## 📋 What We're Doing and Why

### Current State
Your `api.py` has:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ INSECURE - allows any website
    allow_methods=["*"],
    allow_headers=["*"],
)

# No JWT validation - anyone can call your API
@app.post("/refine")
def refine(req: RefineRequest):
    # No user authentication
```

### What We're Building
```python
# CORS locked to frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],  # ✅ Locked
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT middleware validates all requests
@app.post("/refine")
async def refine(
    req: RefineRequest,
    user: User = Depends(get_current_user)  # ✅ Auth required
):
    # user_id from JWT used for RLS
```

### Why JWT + Supabase?

| Benefit | Explanation |
|---------|-------------|
| **Single source of truth** | Users stored in Supabase `auth.users` |
| **RLS integration** | `auth.uid()` in policies matches JWT `user_id` |
| **No custom auth logic** | Supabase handles signup/login/password reset |
| **Secure by default** | JWT signed by Supabase, verified by your API |

---

## 🔧 Implementation

### Part A: Update `.env` with Frontend URL

Add this line to your `.env` file:

```env
FRONTEND_URL=http://localhost:9000
```

### Part B: Create JWT Utilities File

Create `auth.py` in your project root:

```bash
# Create file
type nul > C:\Users\user\OneDrive\Desktop\newnew\auth.py
```

**AI Prompt to Generate `auth.py`:**

```
You are implementing JWT authentication for PromptForge v2.0 using Supabase.

Follow RULES.md exactly. Generate production-ready code with:
- Comprehensive error handling
- Type hints on all functions
- Proper logging with context
- Security best practices

Create auth.py with:
1. User Pydantic model with user_id, email, role fields
2. get_current_user() function that:
   - Extracts Bearer token from Authorization header
   - Verifies JWT using Supabase JWT secret from .env
   - Returns User object with user_id extracted from JWT
   - Raises HTTPException(403) if token invalid or missing
3. Optional: create HTTPBearer dependency for FastAPI

Use python-jose for JWT verification.
JWT algorithm: HS256
Issuer: Supabase (from SUPABASE_URL env var)

File: auth.py
```

### Expected `auth.py` Structure:

```python
# auth.py
import os
import logging
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

security = HTTPBearer()

class User(BaseModel):
    user_id: str
    email: Optional[str] = None
    role: str = "authenticated"

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Extracts and validates JWT from request.
    Returns User with user_id from JWT.
    Raises 403 if invalid.
    """
    token = credentials.credentials
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    supabase_url = os.getenv("SUPABASE_URL")
    
    if not jwt_secret:
        logger.error("SUPABASE_JWT_SECRET not set in .env")
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    try:
        # Decode JWT
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            issuer=supabase_url,
            options={"verify_aud": False}
        )
        
        # Extract user_id from Supabase JWT
        user_id = payload.get("sub")  # Supabase puts user_id in "sub" claim
        
        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid token: no user_id")
        
        return User(
            user_id=user_id,
            email=payload.get("email"),
            role=payload.get("role", "authenticated")
        )
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=403, detail="Invalid or expired token")
```

### Part C: Update `api.py` with JWT Middleware

**AI Prompt to Update `api.py`:**

```
You are updating api.py for PromptForge v2.0 to add JWT authentication.

Follow RULES.md exactly. Update api.py to:
1. Import User and get_current_user from auth.py
2. Update CORS middleware to use FRONTEND_URL from .env (not wildcard)
3. Add user: User = Depends(get_current_user) to ALL endpoints except /health
4. Use user.user_id for database operations instead of session_id alone

Current api.py has these endpoints:
- GET /health (NO auth required)
- POST /refine (auth required)
- POST /chat (auth required)
- POST /chat/stream (auth required)
- GET /history (auth required)
- GET /conversation (auth required)

Make sure to:
- Keep existing functionality
- Add proper error handling
- Log authentication events
- Use user.user_id in all database calls
```

### Key Changes to `api.py`:

```python
# At top of api.py
from auth import User, get_current_user

# Update CORS (replace existing CORSMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:9000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update /refine endpoint
@app.post("/refine", response_model=RefineResponse)
async def refine(
    req: RefineRequest,
    user: User = Depends(get_current_user)  # ← Add this
):
    logger.info(f"[api] /refine user_id={user.user_id} session={req.session_id}")
    # Use user.user_id for database operations
    request_id = save_request(
        raw_prompt=final_state["raw_prompt"],
        improved_prompt=final_state.get("improved_prompt", ""),
        session_id=req.session_id,
        user_id=user.user_id  # ← Add this
    )
    # ... rest of existing code
```

---

## ✅ Verification Checklist

### Test 1: Health Endpoint (No Auth Required)

```bash
curl http://localhost:8000/health
```

**Expected:** Returns `{"status":"ok","version":"2.0.0"}`

### Test 2: Protected Endpoint Without Token (Should Fail)

```bash
curl -X POST http://localhost:8000/refine \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"test prompt\",\"session_id\":\"test\"}"
```

**Expected:** Returns `{"detail":"Not authenticated"}` with status 403

### Test 3: Get a Valid JWT Token

**Option A: Via Supabase Dashboard**
1. Go to Supabase dashboard → Authentication → Users
2. Click on your user
3. Copy the user ID (UUID format)

**Option B: Via Supabase Client (Python)**
```python
from supabase import create_client
import os

client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Sign in (if you have email/password)
response = client.auth.sign_in_with_password({
    "email": "your@email.com",
    "password": "your_password"
})

token = response.session.access_token
print(f"Your JWT token: {token}")
```

### Test 4: Protected Endpoint With Valid Token

```bash
curl -X POST http://localhost:8000/refine \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -d "{\"prompt\":\"test prompt\",\"session_id\":\"test\"}"
```

**Expected:** Returns refined prompt (status 200)

---

## 🆘 Troubleshooting

### Problem: "Invalid or expired token"

**Cause:** JWT secret mismatch or token expired

**Solution:**
1. Check `SUPABASE_JWT_SECRET` in `.env` matches Supabase dashboard exactly
2. Supabase JWTs expire after 1 hour — get a fresh token
3. Check issuer URL matches `SUPABASE_URL`

### Problem: "SUPABASE_JWT_SECRET not set"

**Cause:** `.env` not loaded or secret missing

**Solution:**
```bash
# Check .env file has the line
type C:\Users\user\OneDrive\Desktop\newnew\.env | findstr SUPABASE_JWT_SECRET

# Restart server to reload .env
```

### Problem: "CORS error in browser"

**Cause:** Frontend URL not matching

**Solution:**
1. Check `FRONTEND_URL` in `.env` matches your frontend exactly
2. For local dev: `http://localhost:9000`
3. Restart server after changing `.env`

---

## 📝 What Changed

| File | Change |
|------|--------|
| `.env` | Added `FRONTEND_URL` |
| `auth.py` | Created (new file) |
| `api.py` | JWT validation, CORS locked, user extraction |

---

## ✅ Checkpoint — DO NOT PROCEED UNTIL

- [ ] `/health` returns 200 without token
- [ ] `/refine` returns 403 without token
- [ ] `/refine` returns 200 with valid token
- [ ] CORS origins locked to `FRONTEND_URL`
- [ ] User ID extracted from JWT correctly

---

**Next:** Proceed to [STEP_3_redis_cache.md](./STEP_3_redis_cache.md)

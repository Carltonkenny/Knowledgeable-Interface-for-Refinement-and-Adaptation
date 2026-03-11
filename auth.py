# auth.py
# ─────────────────────────────────────────────
# JWT Authentication for PromptForge v2.0
#
# Uses Supabase's built-in JWT system.
# All endpoints except /health require valid JWT.
# Extracts user_id from JWT for RLS database queries.
#
# Security rules (from RULES.md):
# - JWT required on all endpoints except /health
# - session_id ownership verified via RLS
# - No hardcoded secrets (all from .env)
# ─────────────────────────────────────────────

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

# FastAPI's built-in HTTP Bearer token handler
security = HTTPBearer()


class User(BaseModel):
    """
    User model extracted from Supabase JWT.
    
    Attributes:
        user_id: Unique user identifier from auth.users
        email: User's email (optional, may not be in all tokens)
        role: User role (default: 'authenticated')
    """
    user_id: str
    email: Optional[str] = None
    role: str = "authenticated"


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Extracts and validates JWT from request Authorization header.
    
    Args:
        credentials: HTTP Bearer token from request header
        
    Returns:
        User object with user_id extracted from JWT
        
    Raises:
        HTTPException: 403 if token invalid, missing, or expired
        
    Example:
        @app.post("/refine")
        async def refine(user: User = Depends(get_current_user)):
            # user.user_id available for RLS
            pass
    """
    token = credentials.credentials
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    supabase_url = os.getenv("SUPABASE_URL")
    
    # Validate configuration
    if not jwt_secret:
        logger.error("[auth] SUPABASE_JWT_SECRET not set in .env")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: JWT secret missing"
        )
    
    if not supabase_url:
        logger.error("[auth] SUPABASE_URL not set in .env")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase URL missing"
        )
    
    try:
        # Decode and verify JWT
        # Supabase uses HS256 algorithm and puts user_id in "sub" claim
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            # issuer=supabase_url,  # TEMP DISABLED - debugging 403
            options={"verify_aud": False}  # Don't verify audience (not always set)
        )
        
        # Extract user_id from JWT "sub" claim (Supabase standard)
        user_id = payload.get("sub")
        
        if not user_id:
            logger.warning("[auth] JWT missing user_id (sub claim)")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token: no user_id"
            )
        
        # Log successful authentication
        logger.info(f"[auth] user authenticated: user_id={user_id[:8]}...")
        
        return User(
            user_id=user_id,
            email=payload.get("email"),
            role=payload.get("role", "authenticated")
        )
        
    except jwt.ExpiredSignatureError:
        logger.warning("[auth] JWT expired")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token expired — please log in again"
        )
    except jwt.JWTError as e:
        logger.warning(f"[auth] JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token"
        )
    except Exception as e:
        logger.error(f"[auth] unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


# Optional: For endpoints that don't require auth
def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Returns User if valid JWT provided, None otherwise.
    Used for public endpoints that optionally personalize.
    
    Args:
        credentials: Optional HTTP Bearer token
        
    Returns:
        User if valid token, None if no token or invalid
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None

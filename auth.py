# auth.py
# ─────────────────────────────────────────────
# JWT Authentication for PromptForge v2.0
#
# Uses Supabase's built-in JWT system.
# All endpoints except /health require valid JWT.
# Extracts user_id from JWT for RLS database queries.
# ─────────────────────────────────────────────

import os
import logging
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# FastAPI's built-in HTTP Bearer token handler
security = HTTPBearer()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("[auth] Supabase credentials not configured")
    raise RuntimeError("Supabase configuration missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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
    Extracts and validates JWT using Supabase client.

    Args:
        credentials: HTTP Bearer token from request header

    Returns:
        User object with user_id extracted from JWT

    Raises:
        HTTPException: 403 if token invalid, missing, or expired
    """
    token = credentials.credentials

    # Retry once on transient network errors (WinError 10035 on Windows)
    last_error = None
    for attempt in range(2):
        try:
            # Use Supabase client to validate JWT
            # This handles ES256/HS256 automatically
            user_response = supabase.auth.get_user(token)

            if not user_response.user:
                logger.warning("[auth] JWT missing user information")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token: no user info"
                )

            # Log successful authentication
            logger.info(f"[auth] user authenticated: user_id={user_response.user.id[:8]}...")

            return User(
                user_id=user_response.user.id,
                email=user_response.user.email,
                role="authenticated"
            )

        except HTTPException:
            raise  # Don't retry auth failures
        except OSError as e:
            # Transient socket error (WinError 10035: non-blocking socket not ready)
            last_error = e
            if attempt == 0:
                logger.warning(f"[auth] transient network error, retrying: {e}")
                continue
            logger.error(f"[auth] network error persisted after retry: {e}")
        except Exception as e:
            logger.warning(f"[auth] JWT validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired token"
            )

    # Both attempts failed with transient error
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication service temporarily unavailable"
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

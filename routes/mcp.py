# routes/mcp.py
# ─────────────────────────────────────────────
# UNIFIED CLOUD MCP BRIDGE — THE "SUPABASE" WAY
#   - Token Generation & Revocation
#   - Full SSE Protocol Implementation
#   - Integrated Auth & Tool Swarm
# ─────────────────────────────────────────────

import asyncio
import json
import logging
import uuid
import os
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse

from auth import User, get_current_user
from service import _run_swarm
from database import get_client
from utils.error_messages import get_error_message, ErrorType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["MCP"])

# Active connections map: sessionId -> Queue
active_connections: Dict[str, asyncio.Queue] = {}

# ═══ 1. TOKEN FACTORY (Management) ══════════════════════════════

@router.post("/mcp/generate-token")
async def generate_mcp_token(user: User = Depends(get_current_user)):
    """Generate a long-lived (365 days) JWT for Cloud MCP access."""
    from jose import jwt
    logger.info(f"[mcp] generating token for user={user.user_id[:8]}")
    
    try:
        db = get_client()
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        
        payload = {
            "sub": user.user_id,
            "type": "mcp_access",
            "iss": os.getenv("SUPABASE_URL"),
            "exp": expires_at
        }
        
        mcp_secret = os.getenv("MCP_JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET")
        mcp_token = jwt.encode(payload, mcp_secret, algorithm="HS256")
        token_hash = hashlib.sha256(mcp_token.encode()).hexdigest()
        
        db.table("mcp_tokens").insert({
            "user_id": user.user_id,
            "token_hash": token_hash,
            "token_type": "mcp_access",
            "expires_at": expires_at.isoformat(),
            "revoked": False
        }).execute()
        
        return {
            "mcp_token": mcp_token,
            "expires_at": expires_at.isoformat(),
            "status": "ready"
        }
    except Exception as e:
        logger.exception("[mcp] token generation failed")
        raise HTTPException(status_code=500, detail="Failed to generate secure token")

@router.get("/mcp/list-tokens")
async def list_mcp_tokens(user: User = Depends(get_current_user)):
    """List active user tokens."""
    db = get_client()
    result = db.table("mcp_tokens").select("id, expires_at, created_at").eq("user_id", user.user_id).eq("revoked", False).execute()
    return {"tokens": result.data}

@router.post("/mcp/revoke-token/{token_id}")
async def revoke_mcp_token(token_id: str, user: User = Depends(get_current_user)):
    """Immediate revocation of a token."""
    db = get_client()
    db.table("mcp_tokens").update({"revoked": True}).eq("id", token_id).eq("user_id", user.user_id).execute()
    return {"success": True}

# ═══ 2. MCP PROTOCOL (SSE Bridge) ═══════════════════════════════

async def handle_list_tools():
    """Returns the JSON-RPC tool list for the IDE."""
    return {
        "tools": [
            {
                "name": "get_kira_memories",
                "description": "Access Kira's Memory Palace for user-specific identity and tech constraints.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Filter by IDENTITY or TECH STACK"}
                    }
                }
            },
            {
                "name": "engineer_prompt",
                "description": "Trigger the Kira Swarm to transform a raw prompt into a high-fidelity output.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"}
                    },
                    "required": ["prompt"]
                }
            }
        ]
    }

async def handle_call_tool(name: str, arguments: Dict[str, Any], user: User):
    """Executes tools natively in Python without network overhead."""
    if name == "get_kira_memories":
        db = get_client()
        result = db.table("core_memories").select("*").eq("user_id", user.user_id).execute()
        memories = result.data if result.data else []
        text = "\n".join([f"[{m['category']}] {m['content']}" for m in memories])
        return {"content": [{"type": "text", "text": text or "No memories found."}]}

    elif name == "engineer_prompt":
        final_state = _run_swarm(prompt=arguments["prompt"], user_id=user.user_id)
        return {"content": [{"type": "text", "text": final_state.get("improved_prompt", "Analysis failed.")}]}

    raise HTTPException(status_code=404, detail="Tool not found")

@router.get("/mcp/sse")
async def mcp_sse_handshake(request: Request, user: User = Depends(get_current_user)):
    """Cloud MCP Handshake (SSE)."""
    session_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    active_connections[session_id] = queue

    async def event_generator():
        try:
            # Protocol Start: Tell IDE where to send POST messages
            yield f"event: endpoint\ndata: /mcp/messages?sessionId={session_id}\n\n"
            while True:
                if await request.is_disconnected(): break
                message = await queue.get()
                yield f"event: message\ndata: {json.dumps(message)}\n\n"
        finally:
            if session_id in active_connections: del active_connections[session_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/mcp/messages")
async def mcp_message_handler(request: Request, sessionId: str, user: User = Depends(get_current_user)):
    """Cloud MCP Message Router."""
    payload = await request.json()
    method, msg_id = payload.get("method"), payload.get("id")
    response_data = {"jsonrpc": "2.0", "id": msg_id}

    if method == "initialize":
        response_data["result"] = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "Kira-Cloud", "version": "1.0.0"}}
    elif method == "tools/list":
        response_data["result"] = await handle_list_tools()
    elif method == "tools/call":
        params = payload.get("params", {})
        response_data["result"] = await handle_call_tool(params.get("name"), params.get("arguments", {}), user)

    if sessionId in active_connections:
        await active_connections[sessionId].put(response_data)
        return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Invalid Session")

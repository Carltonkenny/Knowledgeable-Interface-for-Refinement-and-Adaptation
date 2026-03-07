# mcp/__main__.py
# ─────────────────────────────────────────────
# MCP stdio transport for Cursor/Claude Desktop
# RULES.md Compliance:
# - Reads JSON-RPC messages from stdin
# - Writes JSON-RPC responses to stdout
# - Authentication via environment variable (MCP_USER_JWT)
# ─────────────────────────────────────────────

import asyncio
import sys
import os
import logging
import json
from typing import Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from mcp.server import handle_mcp_message, validate_mcp_jwt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr  # Log to stderr so stdout stays clean for JSON-RPC
)
logger = logging.getLogger("mcp")

# Authentication
MCP_USER_JWT = os.getenv("MCP_USER_JWT")
USER_ID = None  # Will extract from JWT


async def main():
    """
    Main MCP stdio transport loop.
    
    Reads JSON-RPC messages from stdin (one per line).
    Writes JSON-RPC responses to stdout.
    Logs to stderr.
    """
    logger.info("[mcp] Starting MCP stdio transport")
    
    # Extract and validate user_id from JWT at startup
    user_id = None
    if MCP_USER_JWT:
        user_id = await validate_mcp_jwt(MCP_USER_JWT)
        if user_id:
            logger.info(f"[mcp] Authenticated user: {user_id[:8]}...")
        else:
            logger.error("[mcp] JWT validation failed - MCP server will run without auth")
    else:
        logger.warning("[mcp] No MCP_USER_JWT provided - running without authentication")
    
    # Main message loop
    line_number = 0
    while True:
        try:
            # Read line from stdin
            line = await sys.stdin.readline()
            
            # Empty line = EOF (client disconnected)
            if not line:
                logger.info("[mcp] EOF received, shutting down")
                break
            
            line_number += 1
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Log incoming message (truncated)
            logger.debug(f"[mcp] <<< {line[:200]}...")
            
            # Process message
            response = await handle_mcp_message(line, user_id)
            
            # Write response to stdout
            print(response, flush=True)
            
            # Log outgoing response
            logger.debug(f"[mcp] >>> {response[:200]}...")
            
        except asyncio.CancelledError:
            logger.info("[mcp] Task cancelled, shutting down")
            break
        except KeyboardInterrupt:
            logger.info("[mcp] Interrupted, shutting down")
            break
        except Exception as e:
            logger.error(f"[mcp] Error processing message {line_number}: {e}")
            # Send error response
            error_response = json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32000,
                    "message": f"Internal error: {str(e)}"
                }
            })
            print(error_response, flush=True)
    
    logger.info("[mcp] MCP stdio transport stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"[mcp] Fatal error: {e}")
        sys.exit(1)

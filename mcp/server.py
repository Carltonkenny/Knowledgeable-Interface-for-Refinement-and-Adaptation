# mcp/server.py
# ─────────────────────────────────────────────
# Native MCP server implementation for Cursor/Claude Desktop
# RULES.md Compliance:
# - Surface isolation: LangMem NEVER on MCP, Supermemory NEVER on web app
# - Tool definitions: forge_refine, forge_chat (maps to API endpoints)
# - Trust levels: 0 (cold) → 1 (warm) → 2 (tuned)
# - Context injection: Supermemory at conversation start
# ─────────────────────────────────────────────

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from jose import jwt, JWTError

from config import get_llm, get_fast_llm
from database import get_client
from memory.supermemory import get_mcp_context, store_mcp_fact, get_trust_level
from langchain_core.messages import SystemMessage, HumanMessage
from utils import parse_json_response

logger = logging.getLogger(__name__)

# MCP Protocol Constants
MCP_VERSION = "2024-11-05"
SUPPORTED_PROTOCOLS = ["2024-11-05"]

# JWT Configuration
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")


async def validate_mcp_jwt(token: str) -> Optional[str]:
    """
    Validate long-lived MCP JWT (365 days).
    
    RULES.md Section 9: JWT authentication for MCP surface.
    
    Args:
        token: JWT token string
        
    Returns:
        user_id if valid, None if invalid/expired/revoked
    """
    try:
        from jose import jwt
        import hashlib
        from database import get_client
        
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            issuer=SUPABASE_URL,
            options={"verify_aud": False}
        )
        
        # Check token type (must be mcp_access)
        token_type = payload.get("type")
        if token_type != "mcp_access":
            logger.warning(f"[mcp] Wrong token type: {token_type}")
            return None
        
        # Check not revoked (query database)
        user_id = payload.get("sub")
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        db = get_client()
        result = db.table("mcp_tokens").select("id").eq(
            "token_hash", token_hash
        ).eq("revoked", False).execute()
        
        if not result.data:
            logger.warning("[mcp] Token revoked or not found")
            return None
        
        logger.debug(f"[mcp] JWT validated for user {user_id[:8] if user_id else 'unknown'}...")
        return user_id
        
    except jwt.ExpiredSignatureError:
        logger.warning("[mcp] JWT expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"[mcp] JWT validation error: {e}")
        return None
    except Exception as e:
        logger.error(f"[mcp] JWT validation failed: {e}")
        return None


class MCPServer:
    """
    Native MCP server implementation.
    
    RULES.md: Surface isolation — LangMem NEVER called from MCP.
    Uses Supermemory exclusively for MCP context.
    """

    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize MCP server.
        
        Args:
            user_id: Optional user ID for authentication (from JWT)
        """
        self.user_id = user_id
        self.tools = {}
        self.db = get_client()
        self._register_tools()

    def _register_tools(self):
        """Register MCP tools following RULES.md specifications."""
        self.tools = {
            "forge_refine": {
                "name": "forge_refine",
                "description": "Improve a prompt through 4-agent AI swarm analysis. Adds role, context, constraints, and quality gates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt to improve (5-2000 characters)"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Unique session identifier for tracking"
                        }
                    },
                    "required": ["prompt", "session_id"]
                }
            },
            "forge_chat": {
                "name": "forge_chat",
                "description": "Conversational prompt improvement with memory. Classifies message → routes to appropriate handler.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "User message for improvement (1-2000 characters)"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Unique session identifier for tracking"
                        }
                    },
                    "required": ["message", "session_id"]
                }
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main request handler for MCP protocol.
        
        Args:
            request: JSON-RPC 2.0 request dict
            
        Returns:
            JSON-RPC 2.0 response dict
        """
        try:
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                return await self._handle_initialize(params)
            elif method == "tools/call":
                return await self._handle_tool_call(params)
            elif method == "shutdown":
                return await self._handle_shutdown()
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }

        except Exception as e:
            logger.error(f"[mcp] Request handling failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32000,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP initialization handshake with context injection.
        
        RULES.md: Inject Supermemory context at conversation start.
        """
        client_info = params.get("clientInfo", {})
        
        # Get trust level for personalization
        trust_level = 0
        context = []
        
        if self.user_id:
            trust_level = await get_trust_level(self.user_id)
            context = await get_mcp_context(self.user_id, limit=3)
        
        logger.info(f"[mcp] Initialize from {client_info.get('name', 'unknown')} (trust_level={trust_level})")

        # Build context message based on trust level
        context_message = self._build_context_message(context, trust_level)

        return {
            "jsonrpc": "2.0",
            "id": request.get("id") if request else None,
            "result": {
                "protocolVersion": MCP_VERSION,
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "PromptForge",
                    "version": "2.0.0"
                },
                "metadata": {
                    "trust_level": trust_level,
                    "context": context_message,
                    "message": self._get_trust_message(trust_level)
                }
            }
        }

    def _build_context_message(self, context: List[Dict], trust_level: int) -> str:
        """
        Build context message from Supermemory for MCP client.
        
        RULES.md: Context injection at conversation start.
        """
        if not context:
            return "No previous context available."
        
        facts = [f"- {c.get('fact', '')}" for c in context]
        return "Previous context:\n" + "\n".join(facts)

    def _get_trust_message(self, trust_level: int) -> str:
        """
        Get trust-level-appropriate message.
        
        RULES.md Section 9.3: Progressive trust levels.
        """
        messages = {
            0: "Use me via the web app more — I'll get sharper.",
            1: "I'm learning your style. Domain skip and tone adaptation active.",
            2: "Full profile active. I know your preferences and patterns."
        }
        return messages.get(trust_level, messages[0])

    async def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tool execution requests.
        
        Args:
            params: Tool call parameters
            
        Returns:
            Tool execution result
        """
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})

        if tool_name not in self.tools:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Tool '{tool_name}' not found"
                }
            }

        # Validate authentication
        if not self.user_id:
            logger.warning("[mcp] Tool call without authentication")
            return {
                "error": {
                    "code": -32003,
                    "message": "Authentication required. Please provide JWT token."
                }
            }

        # Get MCP context from Supermemory (MCP surface only)
        session_id = tool_params.get("session_id", "mcp_default")
        context = await get_mcp_context(self.user_id, session_id)

        # Execute appropriate tool
        if tool_name == "forge_refine":
            result = await self._execute_forge_refine(tool_params, context)
        elif tool_name == "forge_chat":
            result = await self._execute_forge_chat(tool_params, context)
        else:
            result = {"error": "Tool not implemented"}

        # Store result to Supermemory (background, user doesn't wait)
        await self._store_to_supermemory(tool_name, tool_params, result)

        return {"result": result}

    async def _execute_forge_refine(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute forge_refine tool by calling existing swarm logic.
        
        RULES.md: Maps to POST /refine endpoint logic.
        
        Args:
            params: {"prompt": str, "session_id": str}
            context: Supermemory context (not used for refine)
            
        Returns:
            {"improved_prompt": str, "quality_score": dict, "breakdown": dict}
        """
        prompt = params.get("prompt", "")
        session_id = params.get("session_id", "mcp_default")
        
        logger.info(f"[mcp] forge_refine: prompt='{prompt[:50]}...' session={session_id}")
        
        # Validate input
        if not prompt or len(prompt) < 5:
            return {"error": "Prompt must be at least 5 characters"}
        if len(prompt) > 2000:
            return {"error": "Prompt must be less than 2000 characters"}
        
        try:
            # Call existing swarm logic from workflow.py
            from workflow import workflow as swarm_workflow
            from state import PromptForgeState
            
            # Initialize state for swarm
            initial_state = PromptForgeState(
                message=prompt,
                session_id=session_id,
                user_id=self.user_id,
                attachments=[],
                input_modality="text",
                conversation_history=[],
                user_profile={},
                langmem_context=[],  # RULES.md: LangMem NEVER on MCP
                mcp_trust_level=await get_trust_level(self.user_id),
                orchestrator_decision={},
                user_facing_message="",
                pending_clarification=False,
                clarification_key=None,
                proceed_with_swarm=True,
                intent_analysis={},
                context_analysis={},
                domain_analysis={},
                agents_skipped=[],
                agent_latencies={},
                improved_prompt="",
                original_prompt=prompt,
                prompt_diff=[],
                quality_score={},
                changes_made=[],
                breakdown={},
            )
            
            # Run swarm
            final_state = swarm_workflow.invoke(initial_state)
            
            # Extract results
            improved_prompt = final_state.get("improved_prompt", "")
            quality_score = final_state.get("quality_score", {})
            breakdown = {
                "intent": final_state.get("intent_analysis", {}),
                "context": final_state.get("context_analysis", {}),
                "domain": final_state.get("domain_analysis", {}),
            }
            
            logger.info(f"[mcp] forge_refine complete: {len(improved_prompt)} chars")
            
            return {
                "improved_prompt": improved_prompt,
                "quality_score": quality_score,
                "breakdown": breakdown,
                "original_prompt": prompt,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"[mcp] forge_refine failed: {e}", exc_info=True)
            return {"error": f"Refinement failed: {str(e)}"}

    async def _execute_forge_chat(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute forge_chat tool with classification and routing.
        
        RULES.md: Maps to POST /chat endpoint logic.
        
        Args:
            params: {"message": str, "session_id": str}
            context: Supermemory context for personalization
            
        Returns:
            {"type": str, "reply": str, "improved_prompt": str, "breakdown": dict}
        """
        message = params.get("message", "")
        session_id = params.get("session_id", "mcp_default")
        
        logger.info(f"[mcp] forge_chat: message='{message[:50]}...' session={session_id}")
        
        # Validate input
        if not message or len(message) < 1:
            return {"error": "Message cannot be empty"}
        if len(message) > 2000:
            return {"error": "Message must be less than 2000 characters"}
        
        try:
            # Get conversation history for classification
            history = self._get_conversation_history(session_id, limit=6)
            
            # Classify message
            classification = self._classify_message(message, history)
            
            # Route based on classification
            if classification == "CONVERSATION":
                reply = self._handle_conversation(message, history)
                return {
                    "type": "conversation",
                    "reply": reply,
                    "improved_prompt": None,
                    "breakdown": None,
                    "session_id": session_id
                }
            
            elif classification == "FOLLOWUP":
                result = self._handle_followup(message, history)
                if result:
                    return {
                        "type": "followup_refined",
                        "reply": "Updated! Here's your refined prompt ✨\n\nWant any more tweaks?",
                        "improved_prompt": result.get("improved_prompt", ""),
                        "breakdown": None,
                        "session_id": session_id
                    }
                # Fall back to NEW_PROMPT if followup fails
            
            # NEW_PROMPT: Run full swarm
            from workflow import workflow as swarm_workflow
            from state import PromptForgeState
            
            initial_state = PromptForgeState(
                message=message,
                session_id=session_id,
                user_id=self.user_id,
                attachments=[],
                input_modality="text",
                conversation_history=history,
                user_profile={},
                langmem_context=[],  # RULES.md: LangMem NEVER on MCP
                mcp_trust_level=await get_trust_level(self.user_id),
                orchestrator_decision={},
                user_facing_message="",
                pending_clarification=False,
                clarification_key=None,
                proceed_with_swarm=True,
                intent_analysis={},
                context_analysis={},
                domain_analysis={},
                agents_skipped=[],
                agent_latencies={},
                improved_prompt="",
                original_prompt=message,
                prompt_diff=[],
                quality_score={},
                changes_made=[],
                breakdown={},
            )
            
            final_state = swarm_workflow.invoke(initial_state)
            
            improved_prompt = final_state.get("improved_prompt", "")
            breakdown = {
                "intent": final_state.get("intent_analysis", {}),
                "context": final_state.get("context_analysis", {}),
                "domain": final_state.get("domain_analysis", {}),
            }
            
            logger.info(f"[mcp] forge_chat complete: type=prompt_improved")
            
            return {
                "type": "prompt_improved",
                "reply": "Here's your supercharged prompt 🚀\n\nWant me to refine it further?",
                "improved_prompt": improved_prompt,
                "breakdown": breakdown,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"[mcp] forge_chat failed: {e}", exc_info=True)
            return {"error": f"Chat failed: {str(e)}"}

    def _get_conversation_history(self, session_id: str, limit: int = 6) -> List[Dict]:
        """Get conversation history from database."""
        try:
            result = self.db.table("conversations").select(
                "role, message, message_type, improved_prompt"
            ).eq("session_id", session_id).eq("user_id", self.user_id).order(
                "created_at", desc=True
            ).limit(limit).execute()
            
            history = list(reversed(result.data)) if result.data else []
            return history
        except Exception as e:
            logger.error(f"[mcp] Failed to get history: {e}")
            return []

    def _classify_message(self, message: str, history: List[Dict]) -> str:
        """
        Classify message as CONVERSATION, FOLLOWUP, or NEW_PROMPT.
        
        RULES.md: Same classification logic as web app.
        """
        message_lower = message.lower().strip()
        
        # Short messages → CONVERSATION
        if len(message_lower) < 10:
            return "CONVERSATION"
        
        # Greeting/thanks → CONVERSATION
        conversation_triggers = ["hi", "hello", "thanks", "ok", "cool", "great", "nice", "perfect", "awesome", "got it"]
        if any(trigger in message_lower for trigger in conversation_triggers):
            return "CONVERSATION"
        
        # Modification phrases → FOLLOWUP
        followup_triggers = ["make it", "change it", "change the", "adjust", "modify", "add", "remove", 
                           "shorter", "longer", "better", "different", "more detail", "less formal", 
                           "more formal", "simplify", "expand"]
        if any(trigger in message_lower for trigger in followup_triggers):
            return "FOLLOWUP"
        
        # Default → NEW_PROMPT
        return "NEW_PROMPT"

    def _handle_conversation(self, message: str, history: List[Dict]) -> str:
        """Handle casual conversation with personality."""
        # Simple personality-driven responses
        responses = {
            "hi": "Hey! I'm PromptForge — I turn messy prompts into precise ones. Got something you want supercharged?",
            "thanks": "Glad it helped! Come back whenever you need another prompt tuned up.",
            "hello": "Hi! Think of me as your prompt engineer — I take whatever you throw at me and make it dramatically better. What are you working on?",
        }
        
        message_lower = message.lower().strip()
        for key, response in responses.items():
            if key in message_lower:
                return response
        
        # Default response
        return "Hey! I specialize in one thing: making your prompts actually work. What would you like to improve today?"

    def _handle_followup(self, message: str, history: List[Dict]) -> Optional[Dict]:
        """Handle followup modification request."""
        # Find last improved prompt
        last_improved = None
        for turn in reversed(history):
            if turn.get("improved_prompt"):
                last_improved = turn["improved_prompt"]
                break
        
        if not last_improved:
            return None
        
        # Use fast LLM to refine based on modification request
        try:
            llm = get_fast_llm()
            
            context = f"""Previously improved prompt:
{last_improved}

User's modification request: {message}

Apply the changes and return the complete updated prompt."""
            
            response = llm.invoke([
                SystemMessage(content="You are refining a prompt based on user feedback. Return ONLY the refined prompt."),
                HumanMessage(content=context)
            ])
            
            return {"improved_prompt": response.content.strip()}
            
        except Exception as e:
            logger.error(f"[mcp] followup failed: {e}")
            return None

    async def _store_to_supermemory(self, tool_name: str, params: Dict, result: Dict) -> None:
        """
        Store tool execution result to Supermemory.
        
        RULES.md: Background write — user never waits.
        """
        try:
            if tool_name == "forge_refine":
                fact = f"Refined prompt: {params.get('prompt', '')[:100]}..."
                context = {
                    "tool": tool_name,
                    "domain": result.get("breakdown", {}).get("domain", {}).get("primary_domain", "general"),
                    "quality_score": result.get("quality_score", {})
                }
            elif tool_name == "forge_chat":
                fact = f"Chat: {params.get('message', '')[:100]}..."
                context = {
                    "tool": tool_name,
                    "type": result.get("type", "unknown")
                }
            else:
                return
            
            await store_mcp_fact(self.user_id, fact, context)
            logger.debug(f"[mcp] Stored to Supermemory: {fact[:50]}...")
            
        except Exception as e:
            logger.error(f"[mcp] Failed to store to Supermemory: {e}")

    async def _handle_shutdown(self) -> Dict[str, Any]:
        """Handle graceful shutdown."""
        logger.info("[mcp] Shutdown requested")
        return {
            "jsonrpc": "2.0",
            "result": {"message": "Shutting down gracefully"}
        }


# Global MCP server instance (created per-request with user_id)
def create_mcp_server(user_id: str) -> MCPServer:
    """
    Create MCP server instance with user authentication.
    
    Args:
        user_id: Authenticated user ID from JWT
        
    Returns:
        Authenticated MCPServer instance
    """
    return MCPServer(user_id=user_id)


async def handle_mcp_message(message: str, user_id: Optional[str] = None) -> str:
    """
    Entry point for MCP message handling.
    
    Args:
        message: JSON-RPC message string
        user_id: Optional authenticated user ID
        
    Returns:
        JSON-RPC response string
    """
    try:
        request = json.loads(message)
        server = create_mcp_server(user_id) if user_id else MCPServer()
        response = await server.handle_request(request)
        return json.dumps(response)
        
    except json.JSONDecodeError:
        return json.dumps({
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        })
    except Exception as e:
        logger.error(f"[mcp] Message handling failed: {e}")
        return json.dumps({
            "jsonrpc": "2.0",
            "error": {
                "code": -32000,
                "message": f"Internal error: {str(e)}"
            }
        })

# MCP package for PromptForge v2.0
# Native MCP server implementation for Cursor/Claude Desktop

from .server import MCPServer, create_mcp_server, handle_mcp_message

__all__ = ["MCPServer", "create_mcp_server", "handle_mcp_message"]

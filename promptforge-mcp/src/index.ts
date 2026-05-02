#!/usr/bin/env node
// promptforge-mcp/src/index.ts
// ─────────────────────────────────────────────
// PromptForge MCP Server — Entrypoint
//
// This is the main server that Cursor, Claude Desktop,
// Windsurf, and any MCP-compatible tool will spawn.
//
// Architecture:
//   IDE spawns this process → communicates over stdio →
//   this server validates inputs → forwards to Railway backend →
//   returns structured results to IDE
//
// Security:
//   - PROMPTFORGE_MCP_TOKEN must be set in environment
//   - All inputs validated with zod before forwarding
//   - No secrets, no DB access, no LLM keys in this package
//
// Industry Reference:
//   - Stripe MCP Server: https://github.com/stripe/agent-toolkit
//   - Supabase MCP Server: https://github.com/supabase-community/supabase-mcp
//   - Cloudflare MCP: https://github.com/cloudflare/mcp-server-cloudflare
// ─────────────────────────────────────────────

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

// Tool modules
import * as memories from "./tools/memories.js";
import * as engineer from "./tools/engineer.js";
import * as preferences from "./tools/preferences.js";

// ═══ SERVER INITIALIZATION ══════════════════════════════════════════════════

const server = new McpServer({
  name: "promptforge",
  version: "1.0.0",
});

// ═══ TOOL REGISTRATION ═════════════════════════════════════════════════════
// Each tool is registered with its name, description, input schema, and handler.
// The MCP SDK handles all protocol communication — we just define the tools.

// Tool 1: Get Core Memories
server.tool(
  memories.TOOL_NAME,
  memories.TOOL_DESCRIPTION,
  {
    category: memories.inputSchema.shape.category,
    limit: memories.inputSchema.shape.limit,
  },
  async (args) => {
    try {
      const input = memories.inputSchema.parse(args);
      const result = await memories.execute(input);
      return { content: [{ type: "text" as const, text: result }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      return {
        content: [{ type: "text" as const, text: `Error: ${message}` }],
        isError: true,
      };
    }
  }
);

// Tool 2: Engineer Prompt
server.tool(
  engineer.TOOL_NAME,
  engineer.TOOL_DESCRIPTION,
  {
    prompt: engineer.inputSchema.shape.prompt,
    session_id: engineer.inputSchema.shape.session_id,
  },
  async (args) => {
    try {
      const input = engineer.inputSchema.parse(args);
      const result = await engineer.execute(input);
      return { content: [{ type: "text" as const, text: result }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      return {
        content: [{ type: "text" as const, text: `Error: ${message}` }],
        isError: true,
      };
    }
  }
);

// Tool 3: Get Domain Expertise
server.tool(
  preferences.DOMAIN_TOOL_NAME,
  preferences.DOMAIN_TOOL_DESCRIPTION,
  {},
  async () => {
    try {
      const result = await preferences.executeDomain();
      return { content: [{ type: "text" as const, text: result }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      return {
        content: [{ type: "text" as const, text: `Error: ${message}` }],
        isError: true,
      };
    }
  }
);

// Tool 4: Get Quality Trend
server.tool(
  preferences.TREND_TOOL_NAME,
  preferences.TREND_TOOL_DESCRIPTION,
  {},
  async () => {
    try {
      const result = await preferences.executeTrend();
      return { content: [{ type: "text" as const, text: result }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      return {
        content: [{ type: "text" as const, text: `Error: ${message}` }],
        isError: true,
      };
    }
  }
);

// Tool 5: Save Preference
server.tool(
  preferences.SAVE_TOOL_NAME,
  preferences.SAVE_TOOL_DESCRIPTION,
  {
    content: preferences.saveInputSchema.shape.content,
    category: preferences.saveInputSchema.shape.category,
  },
  async (args) => {
    try {
      const input = preferences.saveInputSchema.parse(args);
      const result = await preferences.executeSave(input);
      return { content: [{ type: "text" as const, text: result }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      return {
        content: [{ type: "text" as const, text: `Error: ${message}` }],
        isError: true,
      };
    }
  }
);

// ═══ START SERVER ═══════════════════════════════════════════════════════════

async function main() {
  // Validate token exists before starting
  if (!process.env.PROMPTFORGE_MCP_TOKEN) {
    console.error(
      "ERROR: PROMPTFORGE_MCP_TOKEN environment variable is required.\n" +
      "Generate a token at your PromptForge Profile page → MCP Integration section.\n" +
      "Then add it to your IDE's MCP server environment variables."
    );
    process.exit(1);
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log to stderr (stdout is reserved for MCP protocol)
  console.error("PromptForge MCP Server v1.0.0 — Connected");
  console.error(`Tools registered: ${[
    memories.TOOL_NAME,
    engineer.TOOL_NAME,
    preferences.DOMAIN_TOOL_NAME,
    preferences.TREND_TOOL_NAME,
    preferences.SAVE_TOOL_NAME,
  ].join(", ")}`);
}

main().catch((error) => {
  console.error("Fatal error starting PromptForge MCP Server:", error);
  process.exit(1);
});

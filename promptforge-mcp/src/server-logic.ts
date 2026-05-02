// promptforge-mcp/src/server-logic.ts
// ─────────────────────────────────────────────
// Shared Tool Registration Logic
// ─────────────────────────────────────────────

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import * as memories from "./tools/memories.js";
import * as engineer from "./tools/engineer.js";
import * as preferences from "./tools/preferences.js";

export function createPromptForgeServer() {
  const server = new McpServer({
    name: "promptforge",
    version: "1.0.0",
  });

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

  return server;
}

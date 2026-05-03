#!/usr/bin/env node
// promptforge-mcp/src/index.ts
// ─────────────────────────────────────────────
// PromptForge MCP Server — Universal Entrypoint
// ─────────────────────────────────────────────

import express from "express";
import cors from "cors";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { createPromptForgeServer } from "./server-logic.js";

async function main() {
  const server = createPromptForgeServer();

  // Mode Detection: SSE (Remote) vs Stdio (Local)
  // We trigger SSE mode if PORT or MCP_TRANSPORT is set
  const isSse = process.env.PORT || process.env.MCP_TRANSPORT === "sse";

  if (isSse) {
    // ── SSE (REMOTE) MODE ───────────────────────────────────────────────────
    const app = express();
    app.use(cors());
    app.use(express.json()); // Essential for /messages POST parsing

    const port = parseInt(process.env.PORT || "3000", 10);
    
    // Multi-connection management
    const activeTransports = new Map<string, SSEServerTransport>();

    // Standard MCP SSE route
    app.get("/sse", async (req, res) => {
      const sessionId = Math.random().toString(36).substring(2);
      console.error(`[SSE] New connection: session=${sessionId}`);
      
      const transport = new SSEServerTransport("/messages", res);
      activeTransports.set(sessionId, transport);
      
      // Clean up when connection closes
      res.on("close", () => {
        console.error(`[SSE] Connection closed: session=${sessionId}`);
        activeTransports.delete(sessionId);
      });

      await server.connect(transport);
    });

    // Message handler route
    app.post("/messages", async (req, res) => {
      const sessionId = req.query.sessionId as string;
      const transport = activeTransports.get(sessionId);

      if (transport) {
        await transport.handlePostMessage(req, res);
      } else {
        // Fallback: If no sessionId in query, try the first active transport (for single-user mode)
        const firstTransport = activeTransports.values().next().value;
        if (firstTransport) {
          await firstTransport.handlePostMessage(req, res);
        } else {
          res.status(400).send("No active transport for session");
        }
      }
    });

    app.listen(port, () => {
      console.error(`PromptForge MCP Server (SSE) running on port ${port}`);
      console.error(`Endpoint: http://localhost:${port}/sse`);
    });

  } else {
    // ── STDIO (LOCAL) MODE ──────────────────────────────────────────────────
    // Validate token exists in local mode (essential for security)
    if (!process.env.PROMPTFORGE_MCP_TOKEN) {
      console.error(
        "ERROR: PROMPTFORGE_MCP_TOKEN environment variable is required.\n" +
        "Generate a token at your PromptForge Profile page → MCP Integration section."
      );
      process.exit(1);
    }

    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("PromptForge MCP Server (Stdio) — Connected");
  }
}

main().catch((error) => {
  console.error("Fatal error starting PromptForge MCP Server:", error);
  process.exit(1);
});

// promptforge-mcp/src/tools/memories.ts
// ─────────────────────────────────────────────
// MCP Tool: get_kira_memories
//
// Lets the IDE read the developer's style preferences,
// constraints, and project context from PromptForge's
// core memory system BEFORE generating code.
//
// Industry Pattern: "Context Injection"
// Used by: GitHub Copilot (repo context), Cursor (codebase indexing)
// Our version: User personality + preference injection
// ─────────────────────────────────────────────

import { z } from "zod";
import { apiFetch } from "../api/client.js";

/**
 * Tool name registered with the MCP server.
 */
export const TOOL_NAME = "get_kira_memories";
export const TOOL_NAME_DELETE = "forget_kira_memory";

/**
 * Tool description shown to the IDE's AI model.
 * This is what Claude/GPT reads to decide WHEN to use this tool.
 */
export const TOOL_DESCRIPTION =
  "Retrieve the user's PromptForge core memories — their coding style preferences, " +
  "constraints, project context, and feedback patterns. Use this BEFORE writing code " +
  "to respect the user's established rules (e.g., 'always use TypeScript', " +
  "'prefer functional components', 'never use Tailwind').";

export const TOOL_DESCRIPTION_DELETE =
  "Permanently remove a core memory from the user's PromptForge profile. " +
  "Use this ONLY when the user explicitly says a preference is outdated, " +
  "incorrect, or no longer applies. Requires the memory ID.";

/**
 * Input schema — validated with zod before sending to backend.
 * Currently takes an optional category filter.
 */
export const inputSchema = z.object({
  category: z
    .enum(["identity", "preference", "project", "constraint", "feedback", "all"])
    .optional()
    .default("all")
    .describe("Filter memories by category. Use 'all' to get everything."),
  limit: z
    .number()
    .min(1)
    .max(50)
    .optional()
    .default(20)
    .describe("Maximum number of memories to return."),
});

export const deleteSchema = z.object({
  id: z.string().describe("The UUID of the memory to forget."),
});

export type MemoriesInput = z.infer<typeof inputSchema>;
export type DeleteInput = z.infer<typeof deleteSchema>;

/**
 * Memory item returned from the backend.
 */
interface MemoryItem {
  id: string;
  content: string;
  category: string;
  quality_score: number;
  created_at: string;
}

/**
 * Execute the get_kira_memories tool.
 *
 * @param input - Validated input from the IDE
 * @returns Formatted memory list for the AI model to consume
 */
export async function execute(input: MemoriesInput): Promise<string> {
  const response = await apiFetch<{ memories: MemoryItem[] }>(
    "/user/memories"
  );

  let memories = response.memories || [];

  // Filter by category if specified
  if (input.category !== "all") {
    memories = memories.filter((m) => m.category === input.category);
  }

  // Apply limit
  memories = memories.slice(0, input.limit);

  if (memories.length === 0) {
    return "No core memories found. The user hasn't established any preferences yet. Proceed with sensible defaults.";
  }

  // Format for the AI model to read
  const formatted = memories
    .map(
      (m) =>
        `[${m.category.toUpperCase()}] ${m.content} (confidence: ${m.quality_score})`
    )
    .join("\n");

  return `## User's PromptForge Core Memories (${memories.length} active rules)\n\n${formatted}\n\n---\nRespect these preferences when generating code or responses.`;
}

/**
 * Execute the forget_kira_memory tool.
 */
export async function executeDelete(input: DeleteInput): Promise<string> {
  await apiFetch(`/memory/${input.id}`, {
    method: "DELETE",
  });

  return `Memory ${input.id} has been successfully forgotten. It will no longer influence AI responses.`;
}

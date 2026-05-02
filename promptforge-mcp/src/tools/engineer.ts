// promptforge-mcp/src/tools/engineer.ts
// ─────────────────────────────────────────────
// MCP Tool: engineer_prompt
//
// Sends a raw, messy prompt to the PromptForge 4-agent swarm
// and returns the optimized version. This is the core value prop.
//
// Industry Pattern: "Prompt Middleware"
// The IDE intercepts a vague user instruction, sends it to Kira,
// gets a precision-engineered prompt back, and THEN executes it.
// ─────────────────────────────────────────────

import { z } from "zod";
import { apiFetch } from "../api/client.js";

export const TOOL_NAME = "engineer_prompt";

export const TOOL_DESCRIPTION =
  "Send a raw prompt to PromptForge's Kira AI swarm for optimization. " +
  "Use this when the user gives a vague or underspecified instruction. " +
  "Kira's 4-agent swarm (Intent, Context, Domain, Prompt Engineer) will " +
  "analyze and rewrite it into a precise, high-quality prompt. " +
  "Returns the improved prompt, quality scores, and what changed.";

export const inputSchema = z.object({
  prompt: z
    .string()
    .min(1)
    .max(5000)
    .describe("The raw prompt to optimize. Can be vague or detailed."),
  session_id: z
    .string()
    .optional()
    .describe("Optional session ID for conversation continuity."),
});

export type EngineerInput = z.infer<typeof inputSchema>;

interface SwarmResponse {
  type: string;
  reply: string;
  improved_prompt?: string;
  quality_score?: {
    specificity: number;
    clarity: number;
    actionability: number;
    overall: number;
  };
  kira_message?: string;
  agents_run?: string[];
  latency_ms?: number;
}

/**
 * Execute the engineer_prompt tool.
 *
 * Sends the raw prompt to the /chat/stream endpoint (non-streaming mode)
 * and returns the engineered result.
 *
 * @param input - Validated input containing the raw prompt
 * @returns Formatted engineering result for the AI model
 */
export async function execute(input: EngineerInput): Promise<string> {
  const response = await apiFetch<SwarmResponse>("/chat/stream", {
    method: "POST",
    body: JSON.stringify({
      message: input.prompt,
      session_id: input.session_id || undefined,
    }),
  });

  const improved = response.improved_prompt;
  const scores = response.quality_score;
  const kiraMsg = response.kira_message || response.reply;
  const agents = response.agents_run || [];

  if (!improved) {
    // Kira responded conversationally (not a prompt engineering task)
    return `Kira says: ${kiraMsg}`;
  }

  // Build formatted output
  let output = `## Kira's Engineered Prompt\n\n${improved}\n\n`;

  if (scores) {
    output += `### Quality Scores\n`;
    output += `- Specificity: ${scores.specificity}/5\n`;
    output += `- Clarity: ${scores.clarity}/5\n`;
    output += `- Actionability: ${scores.actionability}/5\n`;
    output += `- Overall: ${scores.overall}/5\n\n`;
  }

  if (kiraMsg) {
    output += `### Kira's Note\n${kiraMsg}\n\n`;
  }

  if (agents.length > 0) {
    output += `### Agents Used\n${agents.join(", ")}\n`;
  }

  return output;
}

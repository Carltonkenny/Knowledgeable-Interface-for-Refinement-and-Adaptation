// promptforge-mcp/src/tools/preferences.ts
// ─────────────────────────────────────────────
// MCP Tools: get_domain_expertise, get_quality_trend, save_preference
//
// Extended tools that let the IDE deeply integrate with
// PromptForge's digital twin system.
// ─────────────────────────────────────────────

import { z } from "zod";
import { apiFetch } from "../api/client.js";

// ═══ TOOL 1: get_domain_expertise ═══════════════════════════════════════════

export const DOMAIN_TOOL_NAME = "get_domain_expertise";

export const DOMAIN_TOOL_DESCRIPTION =
  "Get the user's dominant expertise domains and confidence levels from PromptForge. " +
  "Use this to calibrate response complexity — skip basic explanations for experts, " +
  "provide more guidance for beginners. Example: if domain_confidence for 'coding' " +
  "is 0.91, the user is a senior developer.";

export const domainInputSchema = z.object({});

interface ProfileInfo {
  dominant_domains: string[];
  preferred_tone: string;
  domain_confidence: number;
  prompt_quality_trend: string;
  xp_total: number;
  loyalty_tier: string;
}

export async function executeDomain(): Promise<string> {
  const profile = await apiFetch<ProfileInfo>("/user/profile-info");

  const domains = profile.dominant_domains || [];
  const confidence = profile.domain_confidence || 0;
  const tone = profile.preferred_tone || "direct";
  const tier = profile.loyalty_tier || "Bronze";
  const xp = profile.xp_total || 0;

  let output = `## User's PromptForge Profile\n\n`;
  output += `- **Expertise Domains:** ${domains.length > 0 ? domains.join(", ") : "Not yet established"}\n`;
  output += `- **Domain Confidence:** ${(confidence * 100).toFixed(0)}%\n`;
  output += `- **Preferred Tone:** ${tone}\n`;
  output += `- **Loyalty Tier:** ${tier} (${xp} XP)\n\n`;

  if (confidence > 0.85) {
    output += `> This user is highly experienced. Skip introductory explanations.\n`;
  } else if (confidence > 0.5) {
    output += `> This user has moderate experience. Provide concise context when needed.\n`;
  } else {
    output += `> This user is relatively new. Include helpful explanations.\n`;
  }

  return output;
}

// ═══ TOOL 2: get_quality_trend ══════════════════════════════════════════════

export const TREND_TOOL_NAME = "get_quality_trend";

export const TREND_TOOL_DESCRIPTION =
  "Get the user's prompt quality trend from PromptForge. " +
  "Shows whether their prompting skills are improving, stable, or declining. " +
  "Use this to adapt your output complexity accordingly.";

export const trendInputSchema = z.object({});

interface QualityTrend {
  trend: { date: string; score: number }[];
}

export async function executeTrend(): Promise<string> {
  const data = await apiFetch<QualityTrend>("/user/quality-trend");

  const trend = data.trend || [];

  if (trend.length === 0) {
    return "No quality trend data available yet. The user hasn't forged enough prompts.";
  }

  const recent = trend.slice(-5);
  const avg = recent.reduce((sum, t) => sum + t.score, 0) / recent.length;
  const direction =
    recent.length >= 2
      ? recent[recent.length - 1].score > recent[0].score
        ? "improving"
        : recent[recent.length - 1].score < recent[0].score
        ? "declining"
        : "stable"
      : "insufficient data";

  let output = `## Prompt Quality Trend\n\n`;
  output += `- **Average Score (last 5):** ${avg.toFixed(1)}/5\n`;
  output += `- **Direction:** ${direction}\n`;
  output += `- **Data Points:** ${trend.length} total\n`;

  return output;
}

// ═══ TOOL 3: save_preference ════════════════════════════════════════════════

export const SAVE_TOOL_NAME = "save_preference";

export const SAVE_TOOL_DESCRIPTION =
  "Save a new preference or constraint to the user's PromptForge core memory. " +
  "Use this when the user explicitly states a coding rule or style preference " +
  "in the IDE (e.g., 'always use arrow functions', 'I prefer Tailwind over vanilla CSS'). " +
  "This teaches Kira their preferences for future sessions.";

export const saveInputSchema = z.object({
  content: z
    .string()
    .min(5)
    .max(500)
    .describe("The preference or constraint to save (e.g., 'Always use TypeScript strict mode')."),
  category: z
    .enum(["identity", "preference", "project", "constraint", "feedback"])
    .describe("The category of this memory."),
});

export type SaveInput = z.infer<typeof saveInputSchema>;

export async function executeSave(input: SaveInput): Promise<string> {
  // We use the chat endpoint with a specially formatted message
  // that triggers the memory extraction pipeline
  await apiFetch("/chat/stream", {
    method: "POST",
    body: JSON.stringify({
      message: `[MCP_PREFERENCE] [${input.category}] ${input.content}`,
    }),
  });

  return `Preference saved to PromptForge core memory: "${input.content}" (category: ${input.category})`;
}

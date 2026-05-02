// promptforge-mcp/src/api/client.ts
// ─────────────────────────────────────────────
// Secure API Client — Dumb Proxy Pattern
//
// RULES:
// - Zero business logic in this file
// - Zero Supabase/DB imports
// - All requests go through Railway backend
// - Token is injected from environment variable
// - All responses are validated before returning
// ─────────────────────────────────────────────

const DEFAULT_API_URL = "https://promptforge-production.up.railway.app";

/**
 * Get the PromptForge API base URL.
 * Reads from PROMPTFORGE_API_URL env var, falls back to production Railway URL.
 */
function getApiUrl(): string {
  return process.env.PROMPTFORGE_API_URL || DEFAULT_API_URL;
}

/**
 * Get the MCP token from environment.
 * Fails fast if not set — the IDE must provide this.
 */
function getToken(): string {
  const token = process.env.PROMPTFORGE_MCP_TOKEN;
  if (!token) {
    throw new Error(
      "PROMPTFORGE_MCP_TOKEN is not set. " +
      "Generate a token at your PromptForge Profile page and add it to your IDE's MCP environment variables."
    );
  }
  return token;
}

/**
 * Authenticated fetch wrapper for the PromptForge API.
 *
 * Security:
 * - Attaches MCP token as Bearer auth
 * - 15-second timeout to prevent hanging
 * - No secrets hardcoded
 *
 * @param path - API path (e.g. "/user/memories")
 * @param options - Additional fetch options
 * @returns Parsed JSON response
 * @throws Error if request fails or returns non-200
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${getApiUrl()}${path}`;
  const token = getToken();

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15_000);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        "X-MCP-Client": "@promptforge/mcp-server",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorBody = await response.text().catch(() => "Unknown error");
      throw new Error(
        `PromptForge API error (${response.status}): ${errorBody}`
      );
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("PromptForge API request timed out after 15 seconds.");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

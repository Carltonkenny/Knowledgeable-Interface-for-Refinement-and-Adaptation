// lib/env.ts
// Validates all required environment variables on startup.
// Fails loudly with a clear message rather than cryptic undefined errors later.

const REQUIRED_VARS = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_DEMO_API_URL',
] as const

export function validateEnv(): void {
  const missing: string[] = []
  for (const key of REQUIRED_VARS) {
    if (!process.env[key]) missing.push(key)
  }
  if (missing.length > 0) {
    throw new Error(
      `[PromptForge] Missing required environment variables:\n${missing.map(k => `  - ${k}`).join('\n')}\n\nCheck promptforge-web/.env.local`
    )
  }
}

// Typed env access — never use process.env directly in components
export const ENV = {
  SUPABASE_URL:    process.env.NEXT_PUBLIC_SUPABASE_URL!,
  SUPABASE_ANON:   process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  API_URL:         process.env.NEXT_PUBLIC_API_URL!,
  DEMO_API_URL:    process.env.NEXT_PUBLIC_DEMO_API_URL!,
  USE_MOCKS:       process.env.NEXT_PUBLIC_USE_MOCKS === 'true',
} as const

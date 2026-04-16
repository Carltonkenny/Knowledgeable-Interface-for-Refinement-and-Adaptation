// lib/env.ts
// Typed env access — never use process.env directly in components
export const ENV = {
  SUPABASE_URL:    process.env.NEXT_PUBLIC_SUPABASE_URL!,
  SUPABASE_ANON:   process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  API_URL:         process.env.NEXT_PUBLIC_API_URL!,
  DEMO_API_URL:    process.env.NEXT_PUBLIC_DEMO_API_URL!,
  USE_MOCKS:       process.env.NEXT_PUBLIC_USE_MOCKS === 'true',
  // ElevenLabs TTS voice preferences
  ELEVENLABS_VOICE_ID: process.env.NEXT_PUBLIC_ELEVENLABS_VOICE_ID || 'pNInz6obpgDQGcFmaJgB',
  // Voice production hardening config (items #5, #8)
  TTS_PROVIDER: process.env.TTS_PROVIDER || 'pollinations',
  VOICE_MONTHLY_BUDGET_USD: parseFloat(process.env.VOICE_MONTHLY_BUDGET_USD || '10'),
  VOICE_BROWSER_FALLBACK_ENABLED: process.env.NEXT_PUBLIC_VOICE_BROWSER_FALLBACK !== 'false',
} as const

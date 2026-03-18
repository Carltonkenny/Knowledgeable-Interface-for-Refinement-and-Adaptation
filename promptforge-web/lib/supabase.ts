// lib/supabase.ts
// Supabase browser client (singleton)
// RULES.md: JWT auto-refresh via onAuthStateChange listener

import { createBrowserClient } from '@supabase/ssr'
import type { Session } from '@supabase/supabase-js'

let client: ReturnType<typeof createBrowserClient> | null = null

export function getSupabaseClient() {
  if (!client) {
    client = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  }
  return client
}

export async function getSession() {
  const supabase = getSupabaseClient()
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

export async function getAccessToken(): Promise<string | null> {
  const session = await getSession()
  return session?.access_token ?? null
}

export async function signOut() {
  const supabase = getSupabaseClient()
  await supabase.auth.signOut()
}

/**
 * Subscribe to auth state changes (token refresh, sign-in, sign-out).
 * Components holding cached tokens should listen and update.
 *
 * Returns an unsubscribe function for cleanup in useEffect.
 */
export function onAuthStateChange(
  callback: (event: string, session: Session | null) => void
): () => void {
  const supabase = getSupabaseClient()
  const { data: { subscription } } = supabase.auth.onAuthStateChange(
    (event, session) => {
      callback(event, session)
    }
  )
  return () => subscription.unsubscribe()
}

// lib/supabase.ts
// Supabase browser client (singleton)

import { createBrowserClient } from '@supabase/ssr'

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

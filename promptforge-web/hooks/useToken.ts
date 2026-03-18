// hooks/useToken.ts
// Client component hook — Get current user's access token
// Uses @supabase/ssr for session management
// 'use client' — uses Supabase auth state listener

'use client'

import { useState, useEffect } from 'react'
import { createBrowserClient } from '@supabase/ssr'
import { logger } from '@/lib/logger'

/**
 * Get current access token with automatic refresh on auth state changes
 * 
 * @returns JWT token string or null if not authenticated
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const token = useToken()
 *   
 *   useEffect(() => {
 *     if (token) {
 *       // Make authenticated API calls
 *       fetch('/api/protected', {
 *         headers: { 'Authorization': `Bearer ${token}` }
 *       })
 *     }
 *   }, [token])
 * }
 * ```
 */
export function useToken(): string | null {
  const [token, setToken] = useState<string | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setToken(session?.access_token ?? null)
      setIsInitializing(false)
    })

    // Listen for auth state changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      logger.debug('Auth state changed', { event, hasToken: !!session?.access_token })
      setToken(session?.access_token ?? null)
    })

    // Cleanup subscription on unmount
    return () => {
      subscription.unsubscribe()
    }
  }, [])

  return isInitializing ? null : token
}

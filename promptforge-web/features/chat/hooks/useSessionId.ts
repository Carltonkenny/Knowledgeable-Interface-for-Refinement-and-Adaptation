// features/chat/hooks/useSessionId.ts
// Client component hook — Session ID management
// 'use client' — uses sessionStorage

'use client'

import { useRef } from 'react'

const SESSION_STORAGE_KEY = 'pf_session_id'

/**
 * Generate or retrieve session ID
 * Same tab = same session, new tab = new session
 */
export function useSessionId() {
  const sessionIdRef = useRef<string | null>(null)

  // Get or create session ID (persistent across tabs/sessions)
  if (!sessionIdRef.current) {
    // Try to get from localStorage (persistent)
    const stored = localStorage.getItem(SESSION_STORAGE_KEY)

    if (stored) {
      sessionIdRef.current = stored
    } else {
      // Generate new UUID
      sessionIdRef.current = crypto.randomUUID?.() ?? generateUUID()
      localStorage.setItem(SESSION_STORAGE_KEY, sessionIdRef.current)
    }
  }

  return sessionIdRef.current!
}

// Fallback UUID generator for browsers without crypto.randomUUID()
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

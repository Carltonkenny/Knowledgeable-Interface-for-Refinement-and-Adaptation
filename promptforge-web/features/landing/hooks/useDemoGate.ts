// features/landing/hooks/useDemoGate.ts
// localStorage demo use counter (3 uses max)
// Gates anonymous users after LIMITS.DEMO_MAX_USES

'use client'

import { useState, useEffect, useCallback } from 'react'
import { LIMITS } from '@/lib/constants'

export function useDemoGate() {
  const [usesRemaining, setUsesRemaining] = useState<number>(LIMITS.DEMO_MAX_USES)
  const [isLoaded, setIsLoaded] = useState(false)

  // Load from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return

    try {
      const stored = localStorage.getItem(LIMITS.DEMO_STORAGE_KEY)
      if (stored) {
        const parsed = parseInt(stored, 10)
        if (!isNaN(parsed)) {
          setUsesRemaining(Math.max(0, LIMITS.DEMO_MAX_USES - parsed))
        }
      }
    } catch {
      // localStorage unavailable — keep default (unlimited in memory)
    }
    setIsLoaded(true)
  }, [])

  // Record a demo use (call AFTER successful demo result)
  const recordUse = useCallback(() => {
    if (typeof window === 'undefined') return

    try {
      const stored = localStorage.getItem(LIMITS.DEMO_STORAGE_KEY)
      const current = stored ? parseInt(stored, 10) : 0
      const newValue = current + 1
      localStorage.setItem(LIMITS.DEMO_STORAGE_KEY, String(newValue))
      setUsesRemaining(prev => Math.max(0, prev - 1))
    } catch {
      // localStorage unavailable — don't gate
    }
  }, [])

  const isGated = usesRemaining <= 0

  return { usesRemaining, isGated, recordUse, isLoaded }
}

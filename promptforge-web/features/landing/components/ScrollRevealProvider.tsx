// features/landing/components/ScrollRevealProvider.tsx
// Client component wrapper for useScrollReveal hook
// Used in server component pages to enable scroll reveals

'use client'

import { useEffect } from 'react'
import { useScrollReveal } from '../hooks/useScrollReveal'

export function ScrollRevealProvider() {
  useScrollReveal()
  return null
}

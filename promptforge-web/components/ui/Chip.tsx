// components/ui/Chip.tsx
// Chip component for status indicators
// 'use client' — interactive component

'use client'

import { HTMLAttributes, forwardRef } from 'react'

export type ChipVariant = 'kira' | 'intent' | 'context' | 'domain' | 'engineer' | 'memory' | 'mcp' | 'teal' | 'success' | 'done'

interface ChipProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: ChipVariant
  active?: boolean
  skipped?: boolean
}

export const Chip = forwardRef<HTMLSpanElement, ChipProps>(
  ({ className = '', variant = 'kira', active = false, skipped = false, children, ...props }, ref) => {
    const variantStyles = {
      kira: 'border-kira text-kira bg-[var(--kira-dim)]',
      intent: 'border-intent text-intent bg-[var(--intent-dim)]',
      context: 'border-context text-context bg-[var(--context-dim)]',
      domain: 'border-domain text-domain bg-[var(--domain-dim)]',
      engineer: 'border-engineer text-engineer bg-[var(--engineer-dim)]',
      memory: 'border-memory text-memory bg-[var(--memory-dim)]',
      mcp: 'border-mcp text-mcp bg-[var(--mcp-dim)]',
      teal: 'border-teal text-teal bg-[var(--teal-dim)]',
      success: 'border-success text-success bg-[var(--success-dim)]',
      done: 'border-success text-success bg-[var(--success-dim)] opacity-50',
    }

    const activeStyles = active ? 'animate-chip-pulse' : ''
    const skippedStyles = skipped ? 'opacity-40 grayscale' : ''

    return (
      <span
        ref={ref}
        className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-mono border ${variantStyles[variant]} ${activeStyles} ${skippedStyles} ${className}`}
        {...props}
      >
        {children}
      </span>
    )
  }
)

Chip.displayName = 'Chip'

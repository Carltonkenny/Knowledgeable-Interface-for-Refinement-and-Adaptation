'use client'

/**
 * Boneyard — Unified skeleton loading system for PromptForge.
 *
 * Replaces scattered animate-pulse loading divs with a single,
 * consistent, and customizable component.
 *
 * Usage:
 *   <Boneyard />                          → single line skeleton
 *   <Boneyard variant="card" />           → card-shaped skeleton
 *   <Boneyard variant="avatar" />         → circular avatar skeleton
 *   <Boneyard variant="list" count={3} /> → 3 list item skeletons
 *   <Boneyard variant="text" count={4} /> → 4 text line skeletons
 *   <Boneyard variant="kira" />           → Kira brand loading indicator
 */

interface BoneyardProps {
  /** Shape variant */
  variant?: 'line' | 'card' | 'avatar' | 'list' | 'text' | 'kira'
  /** Number of skeleton items to render (for list/text variants) */
  count?: number
  /** Custom height (CSS class, e.g. "h-40") */
  height?: string
  /** Custom width (CSS class, e.g. "w-48") */
  width?: string
  /** Additional CSS classes */
  className?: string
}

export default function Boneyard({
  variant = 'line',
  count = 3,
  height,
  width,
  className = '',
}: BoneyardProps) {
  const pulse = 'animate-pulse'

  if (variant === 'kira') {
    return (
      <div className={`flex items-center justify-center ${className}`}>
        <div className={`w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center ${pulse} shadow-[0_0_20px_rgba(var(--color-kira),0.2)]`}>
          <span className="text-kira font-bold font-mono text-xl">K</span>
        </div>
      </div>
    )
  }

  if (variant === 'avatar') {
    return (
      <div className={`rounded-full bg-layer3 ${pulse} ${height || 'h-10'} ${width || 'w-10'} ${className}`} />
    )
  }

  if (variant === 'card') {
    return (
      <div className={`bg-layer2 rounded-xl p-5 border border-border-subtle ${pulse} ${height || 'h-48'} ${className}`}>
        <div className={`${height ? '' : 'h-6'} ${width || 'w-48'} bg-layer3 rounded-md mb-6`} />
        <div className="space-y-3">
          {Array.from({ length: count }).map((_, i) => (
            <div key={i} className="h-4 w-full bg-layer3 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  if (variant === 'list') {
    return (
      <div className={`space-y-3 ${className}`}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className={`bg-layer3 rounded-lg ${pulse} ${height || 'h-12'}`} />
        ))}
      </div>
    )
  }

  if (variant === 'text') {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={`bg-layer3 rounded ${pulse} h-3`}
            style={{ width: i === count - 1 ? '60%' : '100%' }}
          />
        ))}
      </div>
    )
  }

  // Default: single line skeleton
  return (
    <div className={`bg-layer3 rounded ${pulse} ${height || 'h-4'} ${width || 'w-full'} ${className}`} />
  )
}

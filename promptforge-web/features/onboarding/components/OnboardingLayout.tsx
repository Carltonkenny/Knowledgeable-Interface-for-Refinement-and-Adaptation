// features/onboarding/components/OnboardingLayout.tsx
// Client component — Full-screen centered layout for onboarding
// 'use client' — contains state and handlers

'use client'

import { useRouter } from 'next/navigation'
import OnboardingProgress from './OnboardingProgress'

interface OnboardingLayoutProps {
  children: React.ReactNode
  step: number
  onSkip: () => void
}

export default function OnboardingLayout({
  children,
  step,
  onSkip,
}: OnboardingLayoutProps) {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-6 relative"
      style={{
        background: 'radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.06) 0%, transparent 60%)',
      }}
    >
      {/* Skip button */}
      <button
        onClick={onSkip}
        className="absolute top-6 right-6 font-mono text-[10px] tracking-wider text-text-dim hover:text-text-bright transition-colors"
      >
        Skip →
      </button>

      {/* Progress indicator */}
      <div className="mb-8">
        <OnboardingProgress step={step} />
      </div>

      {/* Kira avatar */}
      <div className="w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center mb-6">
        <span className="text-kira font-bold font-mono text-xl">K</span>
      </div>

      {/* Content */}
      <div className="w-full max-w-lg">
        {children}
      </div>
    </div>
  )
}

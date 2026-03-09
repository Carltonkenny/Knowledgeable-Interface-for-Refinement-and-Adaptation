// features/onboarding/components/OnboardingProgress.tsx
// Client component — 3-dot progress indicator
// 'use client' — contains state

'use client'

interface OnboardingProgressProps {
  step: number
  total?: number
}

export default function OnboardingProgress({ step, total = 3 }: OnboardingProgressProps) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: total }).map((_, index) => {
        const isPast = index < step
        const isCurrent = index === step

        return (
          <div
            key={index}
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              isPast || isCurrent
                ? 'bg-kira opacity-100'
                : 'bg-border-strong'
            } ${
              isCurrent ? 'shadow-kira scale-125' : ''
            }`}
          />
        )
      })}
    </div>
  )
}

// app/onboarding/page.tsx
// Client component — Assembles onboarding flow
// 'use client' — needs session check and hooks

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getSession } from '@/lib/supabase'
import { ROUTES } from '@/lib/constants'
import OnboardingLayout from '@/features/onboarding/components/OnboardingLayout'
import OnboardingStep from '@/features/onboarding/components/OnboardingStep'
import { useOnboarding } from '@/features/onboarding/hooks/useOnboarding'

export default function OnboardingPage() {
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const {
    step,
    answers,
    textAnswers,
    selectOption,
    setTextAnswer,
    canProceed,
    goNext,
    skip,
    isSubmitting,
    isLastStep,
    currentQuestion,
  } = useOnboarding()

  // Session check on mount
  useEffect(() => {
    async function checkSession() {
      try {
        const session = await getSession()
        
        if (!session) {
          // No session — redirect to login
          router.push(ROUTES.LOGIN)
          return
        }

        // Session exists — continue
        setLoading(false)
      } catch (error) {
        console.error('[Onboarding] Session check failed', error)
        router.push(ROUTES.LOGIN)
      }
    }

    checkSession()
  }, [router])

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <div className="w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center animate-pulse">
          <span className="text-kira font-bold font-mono text-xl">K</span>
        </div>
      </div>
    )
  }

  return (
    <OnboardingLayout step={step} onSkip={skip}>
      <OnboardingStep
        question={currentQuestion}
        selectedValues={answers[currentQuestion.id] || []}
        onSelect={selectOption}
        onTextChange={setTextAnswer}
        textValue={textAnswers[currentQuestion.id]}
        onNext={goNext}
        isLastStep={isLastStep}
        isLoading={isSubmitting}
      />
    </OnboardingLayout>
  )
}

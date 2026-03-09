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
import { getSupabaseClient } from '@/lib/supabase'

export default function OnboardingPage() {
  const [loading, setLoading] = useState(true)
  const [hasProfile, setHasProfile] = useState(false)
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

  // Session + profile check on mount
  useEffect(() => {
    async function checkSessionAndProfile() {
      try {
        const session = await getSession()
        
        if (!session) {
          // No session — redirect to login
          router.push(ROUTES.LOGIN)
          return
        }

        // Check if user already has a profile
        const supabase = getSupabaseClient()
        const { data: profile } = await supabase
          .from('user_profiles')
          .select('user_id')
          .eq('user_id', session.user.id)
          .single()

        if (profile) {
          // Profile exists — redirect to app
          router.push(ROUTES.APP)
          return
        }

        // No profile — show onboarding
        setLoading(false)
      } catch (error) {
        console.error('[Onboarding] Session/profile check failed', error)
        router.push(ROUTES.LOGIN)
      }
    }

    checkSessionAndProfile()
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

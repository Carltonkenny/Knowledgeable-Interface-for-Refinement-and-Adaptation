// app/onboarding/page.tsx
// Onboarding page - T&C + 3-step wizard

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getSession, hasAcceptedTerms, hasCompletedOnboarding, acceptTerms, completeOnboarding, saveOnboardingProfile } from '@/lib/auth'
import TermsAndConditions from '@/features/auth/components/TermsAndConditions'
import OnboardingWizard from '@/features/onboarding/components/OnboardingWizard'

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState<'loading' | 'terms' | 'onboarding' | 'done'>('loading')
  const [token, setToken] = useState<string>('')

  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    const session = await getSession()
    
    if (!session) {
      // Not logged in - redirect to login
      router.push('/auth/login')
      return
    }

    setToken(session.access_token)

    // Check if terms accepted
    const termsAccepted = await hasAcceptedTerms()
    if (!termsAccepted) {
      setStep('terms')
      return
    }

    // Check if onboarding completed
    const onboardingCompleted = await hasCompletedOnboarding()
    if (!onboardingCompleted) {
      setStep('onboarding')
      return
    }

    // Already completed - redirect to app
    router.push('/app')
  }

  const handleTermsAccept = async () => {
    try {
      await acceptTerms()
      setStep('onboarding')
    } catch (error) {
      console.error('Failed to accept terms:', error)
    }
  }

  const handleTermsDecline = async () => {
    const { signOut } = await import('@/lib/auth')
    await signOut()
    router.push('/auth/login')
  }

  const handleOnboardingComplete = async (profile: {
    primary_use: string
    audience: string
    ai_frustration: string
    frustration_detail?: string
  }) => {
    try {
      // Save profile to Supabase
      await saveOnboardingProfile(profile)
      
      // Mark onboarding complete
      await completeOnboarding()
      
      // Redirect to app
      router.push('/app')
    } catch (error) {
      console.error('Failed to complete onboarding:', error)
    }
  }

  // Loading state
  if (step === 'loading') {
    return (
      <div className="min-h-screen bg-layer1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-kira border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-text-dim">Loading...</p>
        </div>
      </div>
    )
  }

  // Terms & Conditions
  if (step === 'terms') {
    return (
      <TermsAndConditions
        onAccept={handleTermsAccept}
        onDecline={handleTermsDecline}
      />
    )
  }

  // Onboarding Wizard
  if (step === 'onboarding') {
    return (
      <OnboardingWizard
        token={token}
        apiUrl={process.env.NEXT_PUBLIC_API_URL!}
        onComplete={handleOnboardingComplete}
      />
    )
  }

  // Done - redirecting
  return (
    <div className="min-h-screen bg-layer1 flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-kira border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-text-dim">Redirecting to app...</p>
      </div>
    </div>
  )
}

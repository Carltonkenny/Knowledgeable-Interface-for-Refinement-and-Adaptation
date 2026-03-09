// features/onboarding/hooks/useOnboarding.ts
// Client component hook — Step state, answers, submit
// 'use client' — contains state and navigation

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ONBOARDING_QUESTIONS, ROUTES, type OnboardingQuestion } from '@/lib/constants'
import { logger } from '@/lib/logger'
import { apiSaveProfile, type UserProfile } from '@/lib/api'
import { getAccessToken } from '@/lib/supabase'

type OnboardingAnswers = Record<string, string[]>
type OnboardingTextAnswers = Record<string, string>

/**
 * Onboarding state management hook
 * Handles 3-question flow and profile save
 */
export function useOnboarding() {
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<OnboardingAnswers>({})
  const [textAnswers, setTextAnswers] = useState<OnboardingTextAnswers>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const currentQuestion = ONBOARDING_QUESTIONS[step]
  const isLastStep = step === ONBOARDING_QUESTIONS.length - 1

  /**
   * Select an option for current question
   */
  function selectOption(value: string) {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: [...(prev[currentQuestion.id] || []), value],
    }))
  }

  /**
   * Set text answer for current question
   */
  function setTextAnswer(value: string) {
    setTextAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: value,
    }))
  }

  /**
   * Check if current question has answer
   */
  const currentQ = ONBOARDING_QUESTIONS[step] as OnboardingQuestion
  const canProceed = 
    (answers[currentQ.id]?.length ?? 0) > 0 ||
    ('hasTextFallback' in currentQ && (textAnswers[currentQ.id]?.length ?? 0) > 0)

  /**
   * Advance to next step or submit if last
   */
  async function goNext() {
    if (!canProceed) return

    if (isLastStep) {
      // Submit profile
      setIsSubmitting(true)
      setError(null)

      try {
        // Construct profile from answers
        const profile: UserProfile = {
          primary_use: answers.primary_use?.[0] ?? 'other',
          audience: answers.audience?.[0] ?? 'both',
          ai_frustration: answers.ai_frustration?.join(', ') ?? '',
          frustration_detail: textAnswers.ai_frustration ?? '',
        }

        // Get auth token
        const token = await getAccessToken()
        
        if (!token) {
          logger.warn('No auth token for profile save')
          throw new Error('No auth token')
        }

        // Save profile (non-fatal — still navigate on error)
        await apiSaveProfile(profile, token)
        
        logger.info('Profile saved', { profile })
      } catch (err) {
        // Profile save failed — still navigate (non-fatal)
        logger.warn('Profile save failed, continuing anyway', { err })
        setError('Profile save failed, but you can continue.')
      } finally {
        setIsSubmitting(false)
        // Always navigate to app
        router.push(ROUTES.APP)
      }
    } else {
      // Advance to next step
      setStep(prev => prev + 1)
    }
  }

  /**
   * Skip onboarding entirely
   */
  function skip() {
    router.push(ROUTES.APP)
  }

  return {
    step,
    answers,
    textAnswers,
    selectOption,
    setTextAnswer,
    canProceed,
    goNext,
    skip,
    isSubmitting,
    error,
    isLastStep,
    currentQuestion,
  }
}

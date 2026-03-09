// features/onboarding/hooks/useAuth.ts
// Client component hook — Auth actions (login, signup, Google OAuth)
// Uses @supabase/ssr for all auth operations

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createBrowserClient } from '@supabase/ssr'
import { ROUTES } from '@/lib/constants'
import { logger } from '@/lib/logger'

/**
 * Auth actions hook
 * Provides login, signup, and Google OAuth functions
 */
export function useAuth() {
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )

  /**
   * Sign in with Google OAuth
   * Redirects to Google consent screen, then to /onboarding
   */
  async function signInWithGoogle(): Promise<void> {
    setIsLoading(true)
    
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/onboarding`,
        },
      })

      if (error) {
        logger.error('Google OAuth failed', { error: error.message })
        throw new Error('Failed to sign in with Google')
      }
      // Redirect happens automatically via Supabase
    } catch (error) {
      logger.error('Google OAuth error', { error })
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Sign in with email and password
   * @param email - User's email
   * @param password - User's password
   * @returns { error: string | null } - Error message or null on success
   */
  async function signInWithEmail(
    email: string,
    password: string
  ): Promise<{ error: string | null }> {
    setIsLoading(true)

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        logger.error('Email sign in failed', { error: error.message })

        // Map Supabase errors to Kira-voiced messages
        if (error.message.includes('Invalid login credentials')) {
          return { error: "That email or password isn't right. Try again." }
        }
        if (error.message.includes('Email not confirmed')) {
          return { error: "Check your email — you've got a confirmation waiting." }
        }
        return { error: "Something went wrong. Sign back in and we'll pick up where you left off." }
      }

      // Success — redirect to onboarding
      router.push(ROUTES.ONBOARDING)
      return { error: null }
    } catch (error) {
      logger.error('Sign in error', { error })
      return { error: 'Something went wrong. Please try again.' }
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Sign up with email and password
   * @param email - User's email
   * @param password - User's password (min 8 chars)
   * @returns { error: string | null } - Error message or null on success
   */
  async function signUpWithEmail(
    email: string,
    password: string
  ): Promise<{ error: string | null }> {
    setIsLoading(true)

    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/onboarding`,
        },
      })

      if (error) {
        logger.error('Sign up failed', { error: error.message })

        // Map Supabase errors to Kira-voiced messages
        if (error.message.includes('User already registered')) {
          return { error: 'An account with this email already exists.' }
        }
        if (error.message.includes('password') && error.message.includes('less than')) {
          return { error: 'Password must be at least 8 characters.' }
        }
        if (error.message.includes('Invalid email')) {
          return { error: 'Please enter a valid email address.' }
        }
        return { error: 'Something went wrong. Try again or sign in instead.' }
      }

      // Success — redirect to onboarding
      router.push(ROUTES.ONBOARDING)
      return { error: null }
    } catch (error) {
      logger.error('Sign up error', { error })
      return { error: 'Something went wrong. Please try again.' }
    } finally {
      setIsLoading(false)
    }
  }

  return {
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    isLoading,
  }
}

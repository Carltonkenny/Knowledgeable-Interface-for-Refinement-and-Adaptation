// lib/auth.ts
// Auth helpers used by both auth forms and onboarding
// Uses @supabase/ssr for all auth operations

import { createBrowserClient } from '@supabase/ssr'
import { ROUTES } from './constants'
import { logger } from './logger'

/**
 * Initialize Supabase client for auth operations
 * Uses the same client pattern as lib/supabase.ts
 */
function getSupabaseAuthClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}

/**
 * Sign in with Google OAuth
 * Redirects to Google consent screen, then to /onboarding
 */
export async function signInWithGoogle(): Promise<void> {
  const supabase = getSupabaseAuthClient()
  
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${typeof window !== 'undefined' ? window.location.origin : ''}/onboarding`,
    },
  })
  
  if (error) {
    logger.error('Google OAuth sign in failed', { error: error.message })
    throw new Error('Failed to sign in with Google')
  }
  // Redirect happens automatically via Supabase
}

/**
 * Sign in with email and password
 * @param email - User's email address
 * @param password - User's password
 * @returns { error: string | null } - Error message or null on success
 */
export async function signInWithEmail(
  email: string,
  password: string
): Promise<{ error: string | null }> {
  const supabase = getSupabaseAuthClient()
  
  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  
  if (error) {
    logger.error('Email sign in failed', { error: error.message })
    
    // Map Supabase errors to user-friendly messages
    if (error.message.includes('Invalid login credentials')) {
      return { error: "That email or password isn't right. Try again." }
    }
    if (error.message.includes('Email not confirmed')) {
      return { error: "Check your email — you've got a confirmation waiting." }
    }
    return { error: "Something went wrong. Sign back in and we'll pick up where you left off." }
  }
  
  return { error: null }
}

/**
 * Sign up with email and password
 * @param email - User's email address
 * @param password - User's password (min 8 chars)
 * @returns { error: string | null } - Error message or null on success
 */
export async function signUpWithEmail(
  email: string,
  password: string
): Promise<{ error: string | null }> {
  const supabase = getSupabaseAuthClient()
  
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: `${typeof window !== 'undefined' ? window.location.origin : ''}/onboarding`,
    },
  })
  
  if (error) {
    logger.error('Email sign up failed', { error: error.message })
    
    // Map Supabase errors to user-friendly messages
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
  
  return { error: null }
}

/**
 * Get current session (for server components)
 * @returns Session object or null if not authenticated
 */
export async function getSession() {
  const supabase = getSupabaseAuthClient()
  
  try {
    const { data: { session } } = await supabase.auth.getSession()
    return session
  } catch (error) {
    logger.error('Failed to get session', { error })
    return null
  }
}

/**
 * Require authentication - redirect if not logged in
 * Use in server components to protect routes
 * @param redirectTo - Path to redirect to (default: /login)
 * @returns Session object if authenticated, throws redirect if not
 */
export async function requireAuth(redirectTo: string = ROUTES.LOGIN) {
  const session = await getSession()
  
  if (!session) {
    // In server components, this would throw to trigger redirect
    // In client components, use router.push instead
    throw new Error(`AUTH_REDIRECT:${redirectTo}`)
  }
  
  return session
}

/**
 * Get session or redirect helper
 * Wraps requireAuth with try/catch for easier use
 */
export async function getSessionOrRedirect(redirectTo: string = ROUTES.LOGIN): Promise<{
  session: Awaited<ReturnType<typeof getSession>> | null
  shouldRedirect: boolean
  redirectUrl: string | null
}> {
  try {
    const session = await requireAuth(redirectTo)
    return {
      session,
      shouldRedirect: false,
      redirectUrl: null,
    }
  } catch (error) {
    if (error instanceof Error && error.message.startsWith('AUTH_REDIRECT:')) {
      const redirectUrl = error.message.replace('AUTH_REDIRECT:', '')
      return {
        session: null,
        shouldRedirect: true,
        redirectUrl,
      }
    }
    // Unexpected error
    logger.error('getSessionOrRedirect failed', { error })
    return {
      session: null,
      shouldRedirect: true,
      redirectUrl: ROUTES.LOGIN,
    }
  }
}

/**
 * Sign out current user
 * Clears session and redirects to login
 */
export async function signOut(): Promise<void> {
  const supabase = getSupabaseAuthClient()
  
  const { error } = await supabase.auth.signOut()
  
  if (error) {
    logger.error('Sign out failed', { error: error.message })
    throw new Error('Failed to sign out')
  }
  // Redirect handled by caller
}

/**
 * Get current user's access token
 * Used for API calls to backend
 * @returns JWT token string or null
 */
export async function getAccessToken(): Promise<string | null> {
  const session = await getSession()
  return session?.access_token ?? null
}

/**
 * Check if user has accepted terms and conditions
 * @returns true if accepted, false otherwise
 */
export async function hasAcceptedTerms(): Promise<boolean> {
  const session = await getSession()
  if (!session) return false
  
  // Check user metadata for terms acceptance
  const userMetadata = session.user?.user_metadata as { terms_accepted?: boolean }
  return userMetadata?.terms_accepted === true
}

/**
 * Mark user as having accepted terms and conditions
 */
export async function acceptTerms(): Promise<void> {
  const supabase = getSupabaseAuthClient()
  
  const { error } = await supabase.auth.updateUser({
    data: { terms_accepted: true, terms_accepted_at: new Date().toISOString() }
  })
  
  if (error) {
    throw new Error('Failed to record terms acceptance')
  }
}

/**
 * Check if user has completed onboarding
 * @returns true if completed, false otherwise
 */
export async function hasCompletedOnboarding(): Promise<boolean> {
  const session = await getSession()
  if (!session) return false
  
  const userMetadata = session.user?.user_metadata as { onboarding_completed?: boolean }
  return userMetadata?.onboarding_completed === true
}

/**
 * Mark user as having completed onboarding
 */
export async function completeOnboarding(): Promise<void> {
  const supabase = getSupabaseAuthClient()
  
  const { error } = await supabase.auth.updateUser({
    data: { onboarding_completed: true, onboarding_completed_at: new Date().toISOString() }
  })
  
  if (error) {
    throw new Error('Failed to record onboarding completion')
  }
}

/**
 * Save onboarding profile data to Supabase
 * This saves to user_metadata AND creates LangMem memories with embeddings
 */
export async function saveOnboardingProfile(profile: {
  primary_use: string
  audience: string
  ai_frustration: string
  frustration_detail?: string
}): Promise<void> {
  const supabase = getSupabaseAuthClient()
  
  // Save to user metadata
  const { error } = await supabase.auth.updateUser({
    data: { 
      onboarding_profile: profile,
      onboarding_profile_set_at: new Date().toISOString()
    }
  })
  
  if (error) {
    throw new Error('Failed to save onboarding profile')
  }
  
  // Also save as LangMem memory with embedding (for semantic search)
  try {
    const profileContent = `
      User's primary use: ${profile.primary_use}
      Target audience: ${profile.audience}
      AI frustration: ${profile.ai_frustration}
      Additional details: ${profile.frustration_detail || 'none'}
    `
    
    // This will be picked up by backend LangMem system
    // The backend will generate Gemini embedding and store in Supabase
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/memory/onboarding`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: profileContent,
        profile_type: 'onboarding',
        metadata: profile
      })
    })
  } catch (error) {
    // Non-critical - profile saved even if memory fails
    console.warn('Failed to create LangMem memory for onboarding:', error)
  }
}

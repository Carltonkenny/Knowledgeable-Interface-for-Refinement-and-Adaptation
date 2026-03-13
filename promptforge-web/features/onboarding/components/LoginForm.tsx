// features/onboarding/components/LoginForm.tsx
// Client component — Login form with Google + email/password
// 'use client' — contains hooks and form state

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button, Input } from '@/components/ui'
import { ROUTES } from '@/lib/constants'
import { useAuth } from '../hooks/useAuth'
import { getSession, hasCompletedOnboarding } from '@/lib/auth'

export default function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isChecking, setIsChecking] = useState(true)
  const router = useRouter()
  const { signInWithGoogle, signInWithEmail, isLoading } = useAuth()

  // Check if returning user - redirect to app
  useEffect(() => {
    checkReturningUser()
  }, [])

  async function checkReturningUser() {
    const session = await getSession()
    if (session) {
      const onboardingComplete = await hasCompletedOnboarding()
      if (onboardingComplete) {
        router.push('/app')
        return
      }
    }
    setIsChecking(false)
  }

  async function handleGoogleSignIn() {
    try {
      setError(null)
      await signInWithGoogle()
      // Redirect happens automatically via OAuth flow
    } catch (err) {
      setError('Failed to sign in with Google. Please try again.')
    }
  }

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!email || !password) {
      setError('Please fill in all fields.')
      return
    }

    const result = await signInWithEmail(email, password)

    if (result.error) {
      setError(result.error)
    }
    // On success, redirect based on onboarding status
    // (handled by useEffect check or onboarding page)
  }

  // Show loading while checking returning user
  if (isChecking) {
    return (
      <div className="min-h-screen bg-layer1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-kira border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-text-dim">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-bright mb-2">
          Sign in to PromptForge
        </h1>
        <p className="text-text-dim text-sm">
          Welcome back! Kira remembers your preferences.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleEmailSubmit} className="space-y-4">
        {/* Google Sign In */}
        <Button
          type="button"
          variant="primary"
          size="lg"
          onClick={handleGoogleSignIn}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 bg-layer2 border border-border-strong hover:border-border-bright"
        >
          {/* Google "G" SVG */}
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Continue with Google
        </Button>

        {/* Divider */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border-subtle" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-bg px-2 text-text-dim font-mono">OR</span>
          </div>
        </div>

        {/* Email Input */}
        <Input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isLoading}
          autoComplete="email"
        />

        {/* Password Input */}
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
          autoComplete="current-password"
        />

        {/* Error Display */}
        {error && (
          <div className="text-intent text-sm font-mono bg-intent/5 border border-intent/20 rounded-md p-2">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'Signing in...' : 'Sign in →'}
        </Button>
      </form>

      {/* Footer */}
      <p className="mt-6 text-center text-sm text-text-dim">
        Don't have an account?{' '}
        <button
          onClick={() => router.push(ROUTES.SIGNUP)}
          className="text-kira hover:underline font-medium"
        >
          Sign up
        </button>
      </p>
    </div>
  )
}

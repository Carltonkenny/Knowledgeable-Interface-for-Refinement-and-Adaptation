// app/auth/callback/route.ts
// OAuth callback handler for Google Sign-In
// Required for Supabase Auth to complete the OAuth flow

import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')

  // If no code, redirect to login with error
  if (!code) {
    return NextResponse.redirect(
      new URL('/login?error=oauth_failed', request.url)
    )
  }

  try {
    // Create initial response - will be updated after onboarding check
    let response = NextResponse.redirect(
      new URL('/onboarding', request.url)
    )

    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return request.cookies.getAll()
          },
          setAll(cookiesToSet: { name: string; value: string }[]) {
            cookiesToSet.forEach(({ name, value }: { name: string; value: string }) => {
              response.cookies.set(name, value)
            })
          },
        },
      }
    )

    // Exchange the code for a session
    const { error } = await supabase.auth.exchangeCodeForSession(code)

    if (error) {
      // Log the error for debugging
      console.error('[OAuth Callback] Session exchange failed:', error.message)

      // Redirect to login with error
      return NextResponse.redirect(
        new URL('/login?error=oauth_failed', request.url)
      )
    }

    // Get the session to check onboarding status
    const { data: { session } } = await supabase.auth.getSession()

    // Determine redirect based on onboarding completion
    const userMetadata = session?.user?.user_metadata as {
      terms_accepted?: boolean
      onboarding_completed?: boolean
    }

    if (userMetadata?.onboarding_completed === true) {
      // Returning user - skip onboarding, go to app
      response = NextResponse.redirect(new URL('/app', request.url))
    } else if (userMetadata?.terms_accepted === true) {
      // Terms accepted but onboarding not complete
      response = NextResponse.redirect(new URL('/onboarding', request.url))
    } else {
      // New user - start with onboarding (includes T&C)
      response = NextResponse.redirect(new URL('/onboarding', request.url))
    }

    // Success - redirect to appropriate page
    return response
  } catch (error) {
    // Unexpected error
    console.error('[OAuth Callback] Unexpected error:', error)

    return NextResponse.redirect(
      new URL('/login?error=oauth_failed', request.url)
    )
  }
}

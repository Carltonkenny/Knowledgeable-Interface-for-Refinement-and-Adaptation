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
  
  const response = NextResponse.redirect(
    new URL('/onboarding', request.url)
  )
  
  try {
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
    
    // Success - redirect to onboarding
    // The user's session is now set in cookies
    return response
  } catch (error) {
    // Unexpected error
    console.error('[OAuth Callback] Unexpected error:', error)
    
    return NextResponse.redirect(
      new URL('/login?error=oauth_failed', request.url)
    )
  }
}

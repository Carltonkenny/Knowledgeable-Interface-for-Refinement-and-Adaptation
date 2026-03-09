// app/(auth)/signup/page.tsx
// Server component — Signup page shell
// NO 'use client' — imports client component SignupForm

import SignupForm from '@/features/onboarding/components/SignupForm'

export default function SignupPage() {
  return <SignupForm />
}

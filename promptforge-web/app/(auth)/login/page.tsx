// app/(auth)/login/page.tsx
// Server component — Login page shell
// NO 'use client' — imports client component LoginForm

import LoginForm from '@/features/onboarding/components/LoginForm'

export default function LoginPage() {
  return <LoginForm />
}

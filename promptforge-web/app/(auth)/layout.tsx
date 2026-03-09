// app/(auth)/layout.tsx
// Server component — two-column layout for login and signup
// NO 'use client' — this is a server component

import AuthLeftPanel from '@/features/onboarding/components/AuthLeftPanel'

interface AuthLayoutProps {
  children: React.ReactNode
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  // Note: We use "signup" as default since most traffic will be new users
  // For login-specific copy, create app/(auth)/login/layout.tsx
  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      {/* Left Panel — Kira quote + branding */}
      <AuthLeftPanel variant="signup" />

      {/* Right Panel — Form content */}
      <div className="flex items-center justify-center p-8 bg-bg">
        <div className="w-full max-w-md">
          {children}
        </div>
      </div>
    </div>
  )
}

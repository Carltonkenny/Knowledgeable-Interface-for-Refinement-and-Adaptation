// app/app/layout.tsx
// Auth-gated layout with app nav
// 'use client' — needs session check

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getSession } from '@/lib/supabase'
import { ROUTES } from '@/lib/constants'

interface AppLayoutProps {
  children: React.ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    async function checkSession() {
      const session = await getSession()
      
      if (!session) {
        router.push(ROUTES.LOGIN)
        return
      }

      setLoading(false)
    }

    checkSession()
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <div className="w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center animate-pulse">
          <span className="text-kira font-bold font-mono text-xl">K</span>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      {/* Top nav */}
      <nav className="border-b border-border-subtle bg-bg/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center">
              <span className="text-kira font-bold font-mono">⬡</span>
            </div>
            <span className="font-bold text-text-bright">PromptForge</span>
          </div>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            <a href="/app" className="px-3 py-1.5 rounded-md text-sm text-text-bright bg-layer2">
              Chat
            </a>
            <a href="/app/history" className="px-3 py-1.5 rounded-md text-sm text-text-dim hover:text-text-bright">
              History
            </a>
            <a href="/app/profile" className="px-3 py-1.5 rounded-md text-sm text-text-dim hover:text-text-bright">
              Profile
            </a>
          </div>

          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-kira flex items-center justify-center text-white text-sm font-bold">
            U
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}

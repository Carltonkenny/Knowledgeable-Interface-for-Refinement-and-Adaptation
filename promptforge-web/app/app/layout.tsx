// app/app/layout.tsx
// Auth-gated layout with app nav
// 'use client' — needs session check

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getSession } from '@/lib/supabase'
import { ROUTES } from '@/lib/constants'
import ChatSidebar from '@/features/chat/components/ChatSidebar'
import VersionHistoryOverlay from '@/features/history/components/VersionHistoryOverlay'
import Boneyard from '@/components/ui/Boneyard'
import { usePathname } from 'next/navigation'

interface AppLayoutProps {
  children: React.ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState<string | null>(null)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isOffline, setIsOffline] = useState(false)
  const router = useRouter()
  const pathname = usePathname()

  const isHistoryMode = pathname === '/app/history'

  useEffect(() => {
    async function checkSession() {
      const { data: { session } } = await (await import('@/lib/supabase')).getSupabaseClient().auth.getSession()

      if (!session) {
        router.push(ROUTES.LOGIN)
        return
      }

      setToken(session.access_token)
      setUserEmail(session.user?.email ?? null)
      setLoading(false)
    }

    checkSession()
  }, [router])

  // Offline detection
  useEffect(() => {
    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)

    setIsOffline(!navigator.onLine)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (loading || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <Boneyard variant="kira" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      {/* Offline Banner */}
      {isOffline && (
        <div className="bg-intent/20 border-b border-intent/40 px-4 py-2 text-center text-xs text-intent font-mono">
          ⚠️ You're offline — changes will sync when reconnected
        </div>
      )}
      {/* Top nav */}
      <nav className="border-b border-border-subtle bg-bg/90 backdrop-blur-md sticky top-0 z-50">
        <div className="mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center">
                <span className="text-kira font-bold font-mono">⬡</span>
              </div>
              <span className="font-bold text-text-bright tracking-tight">PromptForge</span>
            </div>

            {/* Nav links */}
            <div className="flex items-center gap-1" role="navigation" aria-label="Main navigation">
              <Link href="/app" className={`px-3 py-1.5 rounded-md text-sm ${pathname.startsWith('/app/chat') || pathname === '/app' ? 'text-text-bright bg-layer2' : 'text-text-dim hover:text-text-bright'}`} aria-current={pathname.startsWith('/app/chat') || pathname === '/app' ? 'page' : undefined}>
                Chat
              </Link>
              <Link href="/app/history" className={`px-3 py-1.5 rounded-md text-sm ${pathname === '/app/history' ? 'text-text-bright bg-layer2' : 'text-text-dim hover:text-text-bright'}`} aria-current={pathname === '/app/history' ? 'page' : undefined}>
                History
              </Link>
              <Link href="/app/profile" className={`px-3 py-1.5 rounded-md text-sm ${pathname === '/app/profile' ? 'text-text-bright bg-layer2' : 'text-text-dim hover:text-text-bright'} transition-colors`} aria-current={pathname === '/app/profile' ? 'page' : undefined}>
                Profile
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="px-2 py-1 rounded border border-border-subtle bg-layer1 text-[10px] text-text-dim font-mono uppercase tracking-widest hidden sm:block">
              Ver 2.0.0-rc1
            </div>
            {/* Avatar */}
            <button
              className="w-8 h-8 rounded-full bg-kira flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-kira/20 hover:scale-105 transition-transform"
              title={userEmail || 'User'}
              aria-label={`User menu: ${userEmail || 'User'}`}
            >
              {(userEmail || 'U')[0].toUpperCase()}
            </button>
          </div>
        </div>
      </nav>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <ChatSidebar token={token} mode={isHistoryMode ? 'history' : 'chat'} />

        {/* Content */}
        <main className="flex-1 relative overflow-y-auto custom-scrollbar">
          {children}
        </main>
      </div>

      {/* Version Control Overlay */}
      <VersionHistoryOverlay token={token} />
    </div>
  )
}

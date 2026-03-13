// app/app/page.tsx
// Chat page — main app interface

'use client'

import { useState, useEffect } from 'react'
import { getAccessToken } from '@/lib/supabase'
import { getSession } from '@/lib/auth'
import ChatContainer from '@/features/chat/components/ChatContainer'
import { useRouter } from 'next/navigation'

export default function ChatPage() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)
  const [sessionCount, setSessionCount] = useState(0)

  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    const session = await getSession()
    
    if (!session) {
      // Not logged in - redirect to login
      router.push('/auth/login')
      return
    }

    const accessToken = session.access_token
    setToken(accessToken)
  }

  if (!token) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center animate-pulse">
          <span className="text-kira font-bold font-mono text-xl">K</span>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-64px)]">
      <ChatContainer
        token={token}
        apiUrl={process.env.NEXT_PUBLIC_API_URL!}
        sessionCount={sessionCount}
      />
    </div>
  )
}

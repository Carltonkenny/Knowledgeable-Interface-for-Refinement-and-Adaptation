// app/app/chat/[sessionId]/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getSession } from '@/lib/supabase'
import ChatContainer from '@/features/chat/components/ChatContainer'

export default function SessionChatPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params?.sessionId as string
  
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    async function checkAuth() {
      const session = await getSession()
      if (!session) {
        router.push('/login')
        return
      }
      setToken(session.access_token)
    }
    checkAuth()
  }, [router])

  if (!token || !sessionId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-10 h-10 rounded-lg border border-kira bg-kira-dim animate-pulse flex items-center justify-center">
          <span className="text-kira font-mono">⬡</span>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full">
      <ChatContainer
        token={token}
        apiUrl={process.env.NEXT_PUBLIC_API_URL!}
        sessionId={sessionId}
      />
    </div>
  )
}

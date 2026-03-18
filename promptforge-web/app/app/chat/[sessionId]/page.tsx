// app/app/chat/[sessionId]/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getSession } from '@/lib/supabase'
import { apiConversation } from '@/lib/api'
import { logger } from '@/lib/logger'
import ChatContainer from '@/features/chat/components/ChatContainer'

export default function SessionChatPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params?.sessionId as string

  const [token, setToken] = useState<string | null>(null)
  const [isValidating, setIsValidating] = useState(true)

  useEffect(() => {
    async function checkAuth() {
      const session = await getSession()
      if (!session) {
        router.push('/auth/login')
        return
      }
      
      const accessToken = session.access_token
      setToken(accessToken)

      // Validate session exists (handle deleted/invalid stored session)
      if (sessionId) {
        try {
          // Try to fetch conversation - will 404 if session doesn't exist
          await apiConversation(accessToken, sessionId)
          setIsValidating(false)
        } catch (err) {
          // Session not found (404) - clear localStorage and redirect
          if (typeof window !== 'undefined') {
            localStorage.removeItem('pf_last_session')
          }
          logger.warn('Stored session not found, redirecting to new chat', { sessionId, err })
          router.push('/app')
        }
      } else {
        setIsValidating(false)
      }
    }
    checkAuth()
  }, [router, sessionId])

  if (!token || !sessionId || isValidating) {
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

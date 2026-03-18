// app/app/page.tsx
// Chat page — main app interface

'use client'

import { useState, useEffect } from 'react'
import { getSession } from '@/lib/auth'
import { apiListSessions, apiCreateSession } from '@/lib/api'
import { useRouter } from 'next/navigation'

export default function ChatPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function initChat() {
      const session = await getSession()

      if (!session) {
        router.push('/auth/login')
        return
      }

      const token = session.access_token

      try {
        // Check localStorage for last session (persistence across refresh)
        const lastSessionId = typeof window !== 'undefined' 
          ? localStorage.getItem('pf_last_session') 
          : null

        if (lastSessionId) {
          // Try to redirect to last session
          router.push(`/app/chat/${lastSessionId}`)
          return
        }

        // No stored session — fetch sessions to see if we have any
        const sessions = await apiListSessions(token)

        if (sessions.length > 0) {
          // Redirect to the most recent session
          const mostRecent = sessions[0].id
          localStorage.setItem('pf_last_session', mostRecent)
          router.push(`/app/chat/${mostRecent}`)
        } else {
          // Create a new session and redirect
          const newSession = await apiCreateSession(token)
          localStorage.setItem('pf_last_session', newSession.id)
          router.push(`/app/chat/${newSession.id}`)
        }
      } catch (err) {
        console.error('Failed to initialize chat session', err)
        setLoading(false)
      }
    }

    initChat()
  }, [router])

  return (
    <div className="h-screen flex items-center justify-center bg-bg text-text-dim font-mono text-sm">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-lg border border-kira bg-kira-dim flex items-center justify-center animate-pulse">
          <span className="text-kira font-bold text-xl">⬡</span>
        </div>
        <p>INITIALIZING SECURE SESSION...</p>
      </div>
    </div>
  )
}

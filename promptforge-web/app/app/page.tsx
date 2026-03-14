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
        // Fetch sessions to see if we have any
        const sessions = await apiListSessions(token)
        
        if (sessions.length > 0) {
          // Redirect to the most recent session
          router.push(`/app/chat/${sessions[0].id}`)
        } else {
          // Create a new session and redirect
          const newSession = await apiCreateSession(token)
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

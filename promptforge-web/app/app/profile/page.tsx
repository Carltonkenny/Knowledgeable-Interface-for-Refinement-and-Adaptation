// app/app/profile/page.tsx
// Profile page

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getSession, getSupabaseClient } from '@/lib/supabase'
import { ROUTES } from '@/lib/constants'
import ProfileStats from '@/features/profile/components/ProfileStats'
import QualitySparkline from '@/features/profile/components/QualitySparkline'
import McpTokenSection from '@/features/profile/components/McpTokenSection'
import { useProfile } from '@/features/profile/hooks/useProfile'

export default function ProfilePage() {
  const [userId, setUserId] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    async function loadUser() {
      const session = await getSession()
      
      if (!session) {
        router.push(ROUTES.LOGIN)
        return
      }

      setUserId(session.user.id)
    }

    loadUser()
  }, [router])

  const { profile, sessionCount, trustLevel, isLoading } = useProfile(userId!)

  if (!userId || isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center animate-pulse">
          <span className="text-kira font-bold font-mono text-xl">K</span>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-text-bright mb-6">Profile</h1>

      {/* Profile stats */}
      <div className="mb-8 p-6 rounded-xl border border-border-strong bg-layer2">
        <ProfileStats profile={profile} sessionCount={sessionCount} />
      </div>

      {/* Quality trend */}
      <div className="mb-8 p-6 rounded-xl border border-border-strong bg-layer2">
        <h3 className="font-mono text-[10px] tracking-wider uppercase text-text-dim mb-4">
          Quality trend (30 days)
        </h3>
        <QualitySparkline />
      </div>

      {/* MCP token */}
      <div className="p-6 rounded-xl border border-border-strong bg-layer2">
        <McpTokenSection sessionCount={sessionCount} trustLevel={trustLevel} />
      </div>
    </div>
  )
}

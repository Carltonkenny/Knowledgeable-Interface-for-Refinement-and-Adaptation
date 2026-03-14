// app/app/profile/page.tsx
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getSession } from '@/lib/supabase'
import { ROUTES } from '@/lib/constants'
import { useProfile } from '@/features/profile/hooks/useProfile'

import UsernameEditor from '@/features/profile/components/UsernameEditor'
import DomainNiches from '@/features/profile/components/DomainNiches'
import LangMemPreview from '@/features/profile/components/LangMemPreview'
import QualityTrend from '@/features/profile/components/QualityTrend'
import UsageStats from '@/features/profile/components/UsageStats'
import DangerZone from '@/features/profile/components/DangerZone'

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

  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    if (userId) {
      getSession().then(s => {
        if (s) setToken(s.access_token)
      })
    }
  }, [userId])

  const profile = useProfile(token)

  if (!userId || profile.isInitializing) {
    return (
      <div className="h-full flex items-center justify-center min-h-[50vh]">
        <div className="w-12 h-12 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center animate-pulse shadow-[0_0_20px_rgba(var(--color-kira),0.2)]">
          <span className="text-kira font-bold font-mono text-xl">K</span>
        </div>
      </div>
    )
  }

  // Handle GDPR deletion redirect securely
  const handleDeleteAccount = async () => {
    const success = await profile.deleteAccount()
    if (success) {
      router.push(ROUTES.LOGIN)
      return true
    }
    return false
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 animate-fade-in pb-20">
      
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-text-bright tracking-tight">Digital Twin</h1>
          <p className="text-sm text-text-dim mt-1">Identity & behavioral analytics tracked by LangMem.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (Identity & Core Stats) */}
        <div className="lg:col-span-1 space-y-6 flex flex-col">
          <UsernameEditor 
            initialUsername={profile.stats?.member_since ? 'User' : undefined} 
            isUpdating={profile.isUpdatingAttr}
            onSave={profile.updateUsername}
          />
          <DomainNiches 
            domains={profile.domains} 
            isLoading={profile.isInitializing} 
          />
          <div className="flex-1">
            <LangMemPreview 
              memories={profile.memories} 
              isLoading={profile.isInitializing} 
            />
          </div>
        </div>

        {/* Right Column (Analytics & Danger) */}
        <div className="lg:col-span-2 space-y-6">
          <UsageStats 
            stats={profile.stats} 
            isLoading={profile.isInitializing} 
          />
          <QualityTrend 
            trend={profile.trend} 
            isLoading={profile.isInitializing} 
          />
          
          <div className="pt-6 border-t border-border-subtle/50 mt-6">
            <DangerZone 
              onExport={profile.exportData}
              onDelete={handleDeleteAccount}
              isAuthorizing={profile.isInitializing}
            />
          </div>
        </div>
        
      </div>
    </div>
  )
}

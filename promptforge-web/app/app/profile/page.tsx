'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ROUTES } from '@/lib/constants'
import { useToken } from '@/hooks/useToken'
import { useProfile } from '@/features/profile/hooks/useProfile'
import { apiUpdateProfile } from '@/lib/api'

import McpTokenSection from '@/features/profile/components/McpTokenSection'
import ProfileHeader from '@/features/profile/components/ProfileHeader'
import ProfileTabs from '@/features/profile/components/ProfileTabs'
import ProfileCompleteness from '@/features/profile/components/ProfileCompleteness'
import UsageStats from '@/features/profile/components/UsageStats'
import LangMemPreview from '@/features/profile/components/LangMemPreview'
import DataExport from '@/features/profile/components/DataExport'
import DangerZone from '@/features/profile/components/DangerZone'
import SecurityTab from '@/features/profile/components/SecurityTab'
import ActivityTab from '@/features/profile/components/ActivityTab'
import SettingsTab from '@/features/profile/components/SettingsTab'

export default function ProfilePage() {
  const router = useRouter()
  const token = useToken()
  const [activeTab, setActiveTab] = useState('overview')

  const profile = useProfile(token)

  // Show loading state while token initializes
  if (!token || profile.isInitializing) {
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

  // Handle profile update
  const handleProfileUpdate = async (data: {
    bio?: string | null
    location?: string | null
    job_title?: string | null
    company?: string | null
    website?: string | null
    github?: string | null
    twitter?: string | null
    linkedin?: string | null
    avatar_url?: string | null
  }) => {
    if (!token) return
    await apiUpdateProfile(token, data)
    // Refresh profile data
    profile.refreshStats()
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 animate-fade-in pb-20">
      {/* Profile Header */}
      <ProfileHeader
        email={profile.stats?.email || ''}
        username={profile.username}
        bio={profile.stats?.bio}
        location={profile.stats?.location}
        website={profile.stats?.website}
        github={profile.stats?.github}
        twitter={profile.stats?.twitter}
        linkedin={profile.stats?.linkedin}
        avatar_url={profile.stats?.avatar_url}
        job_title={profile.stats?.job_title}
        company={profile.stats?.company}
        tier={profile.tier as any}
        trustLevel={profile.trustLevel}
        onSave={handleProfileUpdate}
      />

      {/* Profile Tabs */}
      <div className="mt-6">
        <ProfileTabs activeTab={activeTab as any} onTabChange={(tab) => setActiveTab(tab as any)} />

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column */}
            <div className="lg:col-span-1 space-y-6">
              <ProfileCompleteness profile={{
                bio: profile.stats?.bio,
                location: profile.stats?.location,
                job_title: profile.stats?.job_title,
                company: profile.stats?.company,
                website: profile.stats?.website,
                github: profile.stats?.github,
                twitter: profile.stats?.twitter,
                linkedin: profile.stats?.linkedin,
                avatar_url: profile.stats?.avatar_url,
                phone: profile.stats?.phone
              }} />
              <LangMemPreview
                memories={profile.memories}
                isLoading={profile.isInitializing}
              />
            </div>

            {/* Right Column */}
            <div className="lg:col-span-2 space-y-6">
              <UsageStats
                stats={profile.stats}
                isLoading={profile.isInitializing}
              />

              {/* MCP Integration */}
              {token && (
                <McpTokenSection
                  sessionCount={profile.stats?.active_chat_sessions ?? 0}
                  trustLevel={profile.trustLevel}
                  authToken={token}
                />
              )}

              {/* Data Export */}
              <DataExport
                onExport={profile.exportData}
                isAuthorizing={profile.isInitializing}
              />

              {/* Danger Zone */}
              <div className="pt-6 border-t border-border-subtle/50 mt-6">
                <DangerZone
                  onDelete={handleDeleteAccount}
                  isAuthorizing={profile.isInitializing}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'security' && (
          <SecurityTab token={token} />
        )}

        {activeTab === 'activity' && (
          <ActivityTab token={token} />
        )}

        {activeTab === 'settings' && (
          <SettingsTab token={token} />
        )}
      </div>
    </div>
  )
}

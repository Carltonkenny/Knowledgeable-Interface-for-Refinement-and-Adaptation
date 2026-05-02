'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ROUTES } from '@/lib/constants'
import { useToken } from '@/hooks/useToken'
import { useProfile } from '@/features/profile/hooks/useProfile'
import { apiUpdateProfile } from '@/lib/api'
import { logger } from '@/lib/logger'
import { ErrorBoundary } from '@/components/ErrorBoundary'

import McpTokenSection from '@/features/profile/components/McpTokenSection'
import ProfileHeader from '@/features/profile/components/ProfileHeader'
import ProfileTabs from '@/features/profile/components/ProfileTabs'
import ProfileCompleteness from '@/features/profile/components/ProfileCompleteness'
import UsageStats from '@/features/profile/components/UsageStats'
import LangMemPreview from '@/features/profile/components/LangMemPreview'
import KiraInsights from '@/features/profile/components/KiraInsights'
import DataExport from '@/features/profile/components/DataExport'
import DangerZone from '@/features/profile/components/DangerZone'
import SecurityTab from '@/features/profile/components/SecurityTab'
import ActivityTab from '@/features/profile/components/ActivityTab'
import SettingsTab from '@/features/profile/components/SettingsTab'
import Boneyard from '@/components/ui/Boneyard'

export default function ProfilePage() {
  const router = useRouter()
  const token = useToken()
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'settings' | 'security'>('overview')

  const profile = useProfile(token)

  // Show loading state while token initializes
  if (!token || profile.isInitializing) {
    return (
      <div className="h-full flex items-center justify-center min-h-[50vh]">
        <Boneyard variant="kira" />
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
    username?: string | null
  }) => {
    if (!token) return

    // Filter out null values - only send fields that actually have data
    const cleaned = Object.fromEntries(
      Object.entries(data).filter(([_, v]) => v !== null && v !== '')
    ) as Record<string, string>

    if (Object.keys(cleaned).length === 0) {
      toast.info('No changes to save')
      return
    }

    try {
      // Split username from other attributes as they use different API paths
      const { username: newUsername, ...attributes } = cleaned

      const updateTasks: Promise<unknown>[] = []

      if (newUsername) {
        updateTasks.push(profile.updateUsername(newUsername))
      }

      if (Object.keys(attributes).length > 0) {
        updateTasks.push(apiUpdateProfile(token, attributes))
      }

      await Promise.all(updateTasks)
      
      toast.success('Profile synced successfully')
      await profile.refreshStats()
    } catch (err) {
      logger.error('Profile update failed', { err, fields: Object.keys(data) })
      toast.error(err instanceof Error ? err.message : 'Sync failed — your changes are safe. Try again.')
    }
  }

  // Handle username update
  const handleUsernameUpdate = async (newUsername: string): Promise<boolean> => {
    if (!token) return false
    try {
      await profile.updateUsername(newUsername)
      toast.success('Username updated successfully')
      await profile.refreshStats()
      return true
    } catch (err) {
      logger.error('Username update failed', { err })
      toast.error(err instanceof Error ? err.message : 'Failed to update username')
      return false
    }
  }

  return (
    <ErrorBoundary fallback={
      <div className="max-w-5xl mx-auto px-4 py-20 text-center">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold text-text-error mb-2">Profile failed to load</h2>
        <p className="text-text-dim mb-4">Your data is safe — this is a display issue</p>
        <button 
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-kira text-white rounded-lg hover:bg-kira/90 transition-colors"
        >
          Reload Profile
        </button>
      </div>
    }>
      <div className="max-w-5xl mx-auto px-4 py-8 animate-fade-in pb-20">

      {/* Profile Header */}
      <ProfileHeader
        email={profile.email}
        username={profile.username}
        bio={profile.bio}
        location={profile.location}
        website={profile.website}
        github={profile.github}
        twitter={profile.twitter}
        linkedin={profile.linkedin}
        avatar_url={profile.avatar_url}
        job_title={profile.job_title}
        company={profile.company}
        tier={profile.tier}
        trustLevel={profile.trustLevel}
        onSave={handleProfileUpdate}
      />

      {/* Profile Tabs */}
      <div className="mt-6">
        <ProfileTabs activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column */}
            <div className="lg:col-span-1 space-y-6">
              <ProfileCompleteness profile={{
                bio: profile.bio,
                location: profile.location,
                job_title: profile.job_title,
                company: profile.company,
                website: profile.website,
                github: profile.github,
                twitter: profile.twitter,
                linkedin: profile.linkedin,
                avatar_url: profile.avatar_url,
                phone: profile.phone
              }} />
              <KiraInsights
                dominantDomains={profile.dominantDomains}
                preferredTone={profile.preferredTone}
                clarificationRate={profile.clarificationRate}
                domainConfidence={profile.domainConfidence}
                promptQualityTrend={profile.promptQualityTrend}
                notablePatterns={profile.notablePatterns}
              />
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
          <ActivityTab 
            token={token} 
            stats={profile.stats} 
            domains={profile.domains} 
            tier={profile.tier} 
            xpTotal={profile.xpTotal} 
          />
        )}

        {activeTab === 'settings' && (
          <SettingsTab token={token} />
        )}
      </div>
    </div>
    </ErrorBoundary>
  )
}

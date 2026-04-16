'use client'

import { useState, useCallback, useEffect } from 'react'
import {
  apiUpdateUsername,
  apiGetDomains,
  apiGetMemories,
  apiGetQualityTrend,
  apiGetStats,
  apiDeleteAccount,
  apiExportData,
  apiGetProfileInfo,
  DomainStat,
  MemoryPreview,
  QualityTrendPoint,
  UsageStats,
  ExportData,
  UserProfile,
  apiGetAnalyticsHeatmap,
  ActivityHeatmap
} from '@/lib/api'
import { logger } from '@/lib/logger'

export function useProfile(token: string | null) {
  const [isInitializing, setIsInitializing] = useState(true)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [stats, setStats] = useState<UsageStats | null>(null)
  const [domains, setDomains] = useState<DomainStat[]>([])
  const [memories, setMemories] = useState<MemoryPreview[]>([])
  const [trend, setTrend] = useState<QualityTrendPoint[]>([])
  const [heatmap, setHeatmap] = useState<ActivityHeatmap | null>(null)
  const [isUpdatingAttr, setIsUpdatingAttr] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadProfileData = useCallback(async () => {
    if (!token) return
    setIsInitializing(true)
    setError(null)

    try {
      // Fetch all required data in parallel — use allSettled so secondary failures
      // (memories, heatmap, domains) don't block primary profile/stats from loading
      const [profileRes, statsRes, domainsRes, memoriesRes, heatmapRes] = await Promise.allSettled([
        apiGetProfileInfo(token),
        apiGetStats(token),
        apiGetDomains(token),
        apiGetMemories(token),
        apiGetAnalyticsHeatmap(token)
      ])

      // Primary: profile MUST succeed
      if (profileRes.status === 'fulfilled') {
        setProfile(profileRes.value)
      } else {
        logger.error('Profile fetch failed', { error: profileRes.reason })
        setError('Could not load profile data.')
      }

      // Secondary: stats (nice-to-have, profile works without it)
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value)
      }

      // Tertiary: domains
      if (domainsRes.status === 'fulfilled') {
        setDomains(domainsRes.value.domains)
      }

      // Quaternary: memories
      if (memoriesRes.status === 'fulfilled') {
        setMemories(memoriesRes.value.memories)
      }

      // Quinary: heatmap
      if (heatmapRes.status === 'fulfilled') {
        setHeatmap(heatmapRes.value)
      }
    } catch (err) {
      logger.error('Failed to load profile data', { error: err, hasToken: !!token })
      setError('Failed to initialize profile.')
    } finally {
      setIsInitializing(false)
    }
  }, [token])

  useEffect(() => {
    loadProfileData()
  }, [loadProfileData])

  const updateUsername = async (newUsername: string) => {
    if (!token) return false
    setIsUpdatingAttr(true)
    try {
      await apiUpdateUsername(token, newUsername)
      return true
    } catch (err) {
      logger.error('Failed to update username', { error: err })
      throw new Error('Username taken or error occurred.')
    } finally {
      setIsUpdatingAttr(false)
    }
  }

  const exportData = async (): Promise<ExportData | null> => {
    if (!token) return null
    try {
      const data = await apiExportData(token)
      return data
    } catch (err) {
      logger.error('Export failed', { error: err })
      throw new Error('Failed to export data.')
    }
  }

  const deleteAccount = async () => {
    if (!token) return false
    try {
      await apiDeleteAccount(token)
      return true
    } catch (err) {
      logger.error('Delete failed', { error: err })
      throw new Error('Failed to delete account.')
    }
  }

  const calculateTier = () => {
    if (!stats) return 'Bronze'
    if (stats.loyalty_tier) return stats.loyalty_tier
    const count = stats.total_prompts_engineered
    const quality = stats.average_quality_score

    if (count >= 1000 && quality >= 4.5) return 'Kira-Class (Forge-Master)'
    if (count >= 500 && quality >= 4.0) return 'Gold'
    if (count >= 100) return 'Silver'
    return 'Bronze'
  }

  return {
    isInitializing,
    profile,
    stats,
    domains,
    memories,
    heatmap,
    error,
    isUpdatingAttr,
    updateUsername,
    exportData,
    deleteAccount,
    refreshStats: loadProfileData,
    trustLevel: stats?.trust_level ?? 0,
    tier: calculateTier(),
    xpTotal: stats?.xp_total ?? profile?.xp_total ?? 0,
    // Profile fields come from the profile state (apiGetProfileInfo), NOT stats
    username: profile?.username ?? profile?.email?.split('@')[0] ?? 'User',
    email: profile?.email ?? '',
    bio: profile?.bio ?? null,
    location: profile?.location ?? null,
    website: profile?.website ?? null,
    github: profile?.github ?? null,
    twitter: profile?.twitter ?? null,
    linkedin: profile?.linkedin ?? null,
    avatar_url: profile?.avatar_url ?? null,
    job_title: profile?.job_title ?? null,
    company: profile?.company ?? null,
    phone: profile?.phone ?? null,
    // Kira's learned profile analysis fields
    dominantDomains: profile?.dominant_domains ?? [],
    preferredTone: profile?.preferred_tone ?? 'direct',
    clarificationRate: profile?.clarification_rate ?? 0.0,
    domainConfidence: profile?.domain_confidence ?? 0.5,
    promptQualityTrend: profile?.prompt_quality_trend ?? 'stable',
    notablePatterns: profile?.notable_patterns ?? [],
  }
}

'use client'

import { useState, useCallback, useEffect } from 'react'
import {
  apiUpdateUsername,
  apiGetProfile,
  apiGetDomains,
  apiGetMemories,
  apiGetQualityTrend,
  apiGetStats,
  apiDeleteAccount,
  apiExportData,
  DomainStat,
  MemoryPreview,
  QualityTrendPoint,
  UsageStats,
  ExportData,
  UserProfile,
  apiGetAnalyticsHeatmap,
  ActivityHeatmap
} from '@/lib/api'

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
      // Fetch all required data in parallel
      const [statsRes, domainsRes, memoriesRes, heatmapRes] = await Promise.all([
        apiGetStats(token),
        apiGetDomains(token),
        apiGetMemories(token),
        apiGetAnalyticsHeatmap(token)
      ])

      setStats(statsRes)
      setDomains(domainsRes.domains)
      setMemories(memoriesRes.memories)
      setHeatmap(heatmapRes)
    } catch (err: any) {
      console.error('Failed to load profile data:', err)
      setError(err.message || 'Failed to initialize profile.')
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
      // Username update is stored in auth metadata - no need to refresh
      return true
    } catch (err: any) {
      console.error('Failed to update username:', err)
      // Throw error to be caught by the component and shown to the user
      throw new Error(err.message || 'Username taken or error occurred.')
    } finally {
      setIsUpdatingAttr(false)
    }
  }

  const exportData = async (): Promise<ExportData | null> => {
    if (!token) return null
    try {
      const data = await apiExportData(token)
      return data
    } catch (err: any) {
      console.error('Export failed:', err)
      throw new Error(err.message || 'Failed to export data.')
    }
  }

  const deleteAccount = async () => {
    if (!token) return false
    try {
      const res = await apiDeleteAccount(token)
      return true
    } catch (err: any) {
      console.error('Delete failed:', err)
      throw new Error(err.message || 'Failed to delete account.')
    }
  }

  const calculateTier = () => {
    if (!stats) return 'Bronze'
    const count = stats.total_prompts_engineered
    const quality = stats.average_quality_score
    
    if (count >= 1000 && quality >= 4.5) return 'Kira'
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
    username: profile?.username ?? stats ? 'User' : null  // Fallback to 'User' if no profile
  }
}

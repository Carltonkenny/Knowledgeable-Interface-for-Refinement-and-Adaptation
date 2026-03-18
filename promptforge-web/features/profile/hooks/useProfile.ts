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
  DomainStat,
  MemoryPreview,
  QualityTrendPoint,
  UsageStats,
  ExportData
} from '@/lib/api'

export function useProfile(token: string | null) {
  const [isInitializing, setIsInitializing] = useState(true)
  const [stats, setStats] = useState<UsageStats | null>(null)
  const [domains, setDomains] = useState<DomainStat[]>([])
  const [memories, setMemories] = useState<MemoryPreview[]>([])
  const [trend, setTrend] = useState<QualityTrendPoint[]>([])
  const [isUpdatingAttr, setIsUpdatingAttr] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadProfileData = useCallback(async () => {
    if (!token) return
    setIsInitializing(true)
    setError(null)
    
    try {
      // Fetch all required data in parallel
      const [statsRes, domainsRes, memoriesRes, trendRes] = await Promise.all([
        apiGetStats(token),
        apiGetDomains(token),
        apiGetMemories(token),
        apiGetQualityTrend(token)
      ])
      
      setStats(statsRes)
      setDomains(domainsRes.domains)
      setMemories(memoriesRes.memories)
      setTrend(trendRes.trend)
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
      // Refresh all profile data to reflect username change
      await loadProfileData()
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

  return {
    isInitializing,
    stats,
    domains,
    memories,
    trend,
    error,
    isUpdatingAttr,
    updateUsername,
    exportData,
    deleteAccount,
    refreshStats: loadProfileData,
    trustLevel: stats?.trust_level ?? 0
  }
}

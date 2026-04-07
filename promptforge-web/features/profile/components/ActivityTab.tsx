'use client'

import { useState, useEffect } from 'react'
import { Activity, Award, TrendingUp, Clock } from 'lucide-react'
import PromptTimeline from './PromptTimeline'
import AchievementBadges from './AchievementBadges'
import ActivityStats from './ActivityStats'
import PromptHeatmap from './PromptHeatmap'
import NeuralExpertiseRadar from './NeuralExpertiseRadar'
import { DomainStat, UsageStats, apiGetAnalyticsHeatmap, apiGetAchievements } from '@/lib/api'
import { logger } from '@/lib/logger'

interface ActivityTabProps {
  token: string
  stats: UsageStats | null
  domains: DomainStat[]
  tier: string
  xpTotal: number
}

interface Achievement {
  id: string
  name: string
  icon: string
  description: string
}

export default function ActivityTab({ token, stats, domains, tier, xpTotal }: ActivityTabProps) {
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [heatmapData, setHeatmapData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadAchievements()
    loadHeatmap()
  }, [token])

  const loadHeatmap = async () => {
    try {
      const data = await apiGetAnalyticsHeatmap(token)
      setHeatmapData(data.heatmap || [])
    } catch (error) {
      logger.error('Failed to load heatmap', { error })
    }
  }

  const loadAchievements = async () => {
    try {
      const data = await apiGetAchievements(token)
      setAchievements(data.achievements || [])
    } catch (error) {
      logger.error('Failed to load achievements', { error })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-layer2 rounded-2xl border border-border-subtle p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-kira/10 text-kira">
            <Activity size={20} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-text-bright">Activity & Achievements</h2>
            <p className="text-sm text-text-dim">Track your prompt engineering journey</p>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <ActivityStats token={token} />

      {/* 365-Day Activity Heatmap */}
      <PromptHeatmap data={heatmapData} isLoading={isLoading} />
      
      {/* ── HIGH FIDELITY IDENTITY TOPOLOGY ── */}
      <div className="h-[400px]">
        <NeuralExpertiseRadar xpTotal={xpTotal} tier={tier} domains={domains} />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Prompts Timeline */}
        <div className="lg:col-span-1">
          <PromptTimeline token={token} />
        </div>

        {/* Achievement Badges */}
        <div className="lg:col-span-1">
          <AchievementBadges achievements={achievements} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}

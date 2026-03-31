'use client'

import { useState, useEffect } from 'react'
import { Activity, Award, TrendingUp, Clock } from 'lucide-react'
import PromptTimeline from './PromptTimeline'
import AchievementBadges from './AchievementBadges'
import ActivityStats from './ActivityStats'

interface ActivityTabProps {
  token: string
}

interface Achievement {
  id: string
  name: string
  icon: string
  description: string
}

export default function ActivityTab({ token }: ActivityTabProps) {
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadAchievements()
  }, [token])

  const loadAchievements = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user/achievements`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to load achievements')
      }

      setAchievements(data.achievements || [])
    } catch (error: any) {
      console.error('Failed to load achievements:', error)
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

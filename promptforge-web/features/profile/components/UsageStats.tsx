'use client'

import { Activity, MessageSquare, Zap, Target } from 'lucide-react'
import type { UsageStats as UsageStatsType } from '@/lib/api'

interface UsageStatsProps {
  stats: UsageStatsType | null
  isLoading: boolean
}

export default function UsageStats({ stats, isLoading }: UsageStatsProps) {
  if (isLoading || !stats) {
    return (
      <div className="bg-layer2 rounded-xl p-5 border border-border-subtle animate-pulse">
        <div className="h-6 w-32 bg-layer3 rounded-md mb-6" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-20 w-full bg-layer3 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  const parseDate = (isoString?: string) => {
    if (!isoString) return 'Active'
    const d = new Date(isoString)
    return isNaN(d.getTime()) ? 'Active' : d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
  }

  const statCards = [
    {
      label: 'Total Prompts',
      value: stats.total_prompts_engineered,
      icon: <Zap size={18} />,
      color: 'text-kira',
      bg: 'bg-kira/10'
    },
    {
      label: 'Avg Quality',
      value: stats.average_quality_score.toFixed(1),
      icon: <Target size={18} />,
      color: 'text-success',
      bg: 'bg-success/10'
    },
    {
      label: 'Active Threads',
      value: stats.active_chat_sessions,
      icon: <MessageSquare size={18} />,
      color: 'text-primary',
      bg: 'bg-primary/10'
    },
    {
      label: 'Member Since',
      value: parseDate(stats.member_since),
      icon: <Activity size={18} />,
      color: 'text-text-muted',
      bg: 'bg-layer3'
    }
  ]

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-layer3 text-text-bright">
          <Activity size={18} />
        </div>
        <div>
          <h3 className="text-base font-medium text-text-bright">Lifetime Analytics</h3>
          <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
            System Usage
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((card, idx) => (
          <div key={idx} className="bg-layer1 rounded-lg p-4 border border-border-subtle flex flex-col items-center justify-center text-center">
            <div className={`p-2 rounded-full ${card.bg} ${card.color} mb-2`}>
              {card.icon}
            </div>
            <p className="text-2xl font-bold text-text-bright tracking-tight">
              {card.value}
            </p>
            <p className="text-xs text-text-muted mt-1 font-medium">
              {card.label}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

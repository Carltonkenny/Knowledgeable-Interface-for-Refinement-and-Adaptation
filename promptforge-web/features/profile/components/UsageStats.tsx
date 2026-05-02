'use client'

import { Activity, MessageSquare, Zap, Target, LogOut } from 'lucide-react'
import type { UsageStats as UsageStatsType } from '@/lib/api'
import { signOut } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { ROUTES } from '@/lib/constants'
import { logger } from '@/lib/logger'
import Boneyard from '@/components/ui/Boneyard'

interface UsageStatsProps {
  stats: UsageStatsType | null
  isLoading: boolean
}

export default function UsageStats({ stats, isLoading }: UsageStatsProps) {
  const router = useRouter()

  const handleLogout = async () => {
    try {
      await signOut()
      router.push(ROUTES.LOGIN)
    } catch (err) {
      logger.error('Logout failed', { error: err })
    }
  }

  if (isLoading || !stats) {
    return (
      <Boneyard variant="card" count={4} />
    )
  }

  // Empty state check
  const hasNoData = stats.total_prompts_engineered === 0

  const statCards = [
    {
      label: 'PROMPTS FORGED',
      value: hasNoData ? '—' : stats.total_prompts_engineered.toLocaleString(),
      icon: <Zap size={18} />,
      color: 'text-kira',
      bg: 'bg-kira/10'
    },
    {
      label: 'ACTIVE CHATS',
      value: hasNoData ? '—' : stats.active_chat_sessions.toLocaleString(),
      icon: <MessageSquare size={18} />,
      color: 'text-purple-400',
      bg: 'bg-purple-400/10'
    },
    {
      label: 'AVG QUALITY',
      value: hasNoData ? '—' : stats.average_quality_score.toFixed(1),
      icon: <Target size={18} />,
      color: 'text-green-400',
      bg: 'bg-green-400/10'
    },
    {
      label: 'MEMBER SINCE',
      value: hasNoData ? '—' : new Date(stats.member_since).toLocaleDateString(undefined, { month: 'short', year: 'numeric' }),
      icon: <Activity size={18} />,
      color: 'text-blue-400',
      bg: 'bg-blue-400/10'
    }
  ]

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle shadow-xl relative overflow-hidden group/main">
      {/* Subtle background glow */}
      <div className="absolute -top-24 -right-24 w-48 h-48 bg-kira/5 blur-[80px] rounded-full group-hover/main:bg-kira/10 transition-colors pointer-events-none" />

      {/* Empty state overlay */}
      {hasNoData && (
        <div className="absolute inset-0 bg-layer2/95 z-20 flex flex-col items-center justify-center text-center p-6 animate-in fade-in duration-300">
          <div className="w-16 h-16 bg-kira/10 rounded-full flex items-center justify-center mb-4">
            <Activity size={24} className="text-kira/50" />
          </div>
          <h4 className="text-base font-semibold text-text-bright mb-2">No Data Yet</h4>
          <p className="text-sm text-text-dim max-w-xs">
            Start forging prompts to unlock your lifetime analytics. Your first prompt will populate these stats.
          </p>
        </div>
      )}

      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-layer3 text-text-bright shadow-[0_0_10px_rgba(var(--color-kira),0.1)]">
            <Activity size={18} />
          </div>
          <div>
            <h3 className="text-base font-medium text-text-bright tracking-tight">Lifetime Overview</h3>
            <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
              Lifetime Analytics
            </p>
          </div>
        </div>

        <button
          id="logout-button"
          name="logout"
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-intent/30 hover:bg-intent/10 text-intent transition-all active:scale-95 group"
          aria-label="Sign out of your account"
          title="Sign out"
        >
          <LogOut size={14} className="group-hover:-translate-x-0.5 transition-transform" />
          <span className="text-[10px] font-bold uppercase tracking-wider">Sign Out</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 relative z-10">
        {statCards.map((card, idx) => (
          <div 
            key={idx} 
            className="group bg-layer1 rounded-xl p-4 border border-border-subtle flex flex-col items-center justify-center text-center hover:border-kira/30 transition-all hover:bg-kira/5 active:scale-95 cursor-default relative overflow-hidden"
          >
            {/* Glass highlight */}
            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/5 to-transparent" />
            
            <div className={`p-2 rounded-full ${card.bg} ${card.color} mb-2 group-hover:scale-110 transition-transform`}>
              {card.icon}
            </div>
            <p className="text-2xl font-bold text-text-bright tracking-tighter">
              {card.value}
            </p>
            <p className="text-[10px] text-text-dim mt-1 font-bold uppercase tracking-wider">
              {card.label}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

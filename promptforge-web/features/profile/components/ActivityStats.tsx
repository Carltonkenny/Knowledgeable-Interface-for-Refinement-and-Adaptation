'use client'

import { useState, useEffect } from 'react'
import { Activity, TrendingUp, Award, Target, Zap } from 'lucide-react'
import { motion } from 'framer-motion'
import { apiGetActivity } from '@/lib/api'
import { logger } from '@/lib/logger'

interface ActivityStatsProps {
  token: string
}

export default function ActivityStats({ token }: ActivityStatsProps) {
  const [stats, setStats] = useState({
    total_prompts: 0,
    avg_quality: 0,
    best_domain: 'N/A',
    streak: 0
  })
  const [isLoading, setIsLoading] = useState(true)

  const loadStats = async () => {
    try {
      setIsLoading(true)
      const data = await apiGetActivity(token)

      // Calculate stats from prompts
      const prompts = data.prompts || []
      const domainCount: Record<string, number> = {}

      prompts.forEach((p: any) => {
        domainCount[p.domain] = (domainCount[p.domain] || 0) + 1
      })

      const bestDomain = Object.entries(domainCount).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A'

      setStats({
        total_prompts: data.total_prompts || 0,
        avg_quality: data.avg_quality || 0,
        best_domain: bestDomain,
        streak: data.streak || 0
      })
    } catch (error) {
      logger.error('Failed to load activity stats', { error })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadStats()
  }, [token])

  useEffect(() => {
    const handleUpdate = () => {
      logger.debug('Activity stats: real-time sync triggered by domain update')
      loadStats()
    }
    window.addEventListener('update-domain', handleUpdate)
    return () => window.removeEventListener('update-domain', handleUpdate)
  }, [token])

  const statCards = [
    {
      label: 'Total Prompts',
      value: stats.total_prompts.toLocaleString(),
      icon: <Activity size={18} />,
      color: 'text-kira',
      bg: 'bg-kira/10'
    },
    {
      label: 'Best Domain',
      value: stats.best_domain,
      icon: <Target size={18} />,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10'
    },
    {
      label: 'Avg Quality',
      value: stats.avg_quality > 0 ? stats.avg_quality.toFixed(1) : '—',
      icon: <TrendingUp size={18} />,
      color: 'text-green-400',
      bg: 'bg-green-500/10'
    },
    {
      label: 'Current Streak',
      value: stats.streak > 0 ? `${stats.streak} days` : '—',
      icon: <Award size={18} />,
      color: 'text-yellow-400',
      bg: 'bg-yellow-500/10'
    }
  ]

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-layer2/40 rounded-2xl animate-pulse border border-border-default/50 backdrop-blur-sm" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {statCards.map((card, index) => (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          key={index}
          className="group relative bg-layer1/80 backdrop-blur-md rounded-2xl border border-border-default/50 p-5 flex flex-col items-center justify-center text-center hover:border-kira/50 transition-all overflow-hidden shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:shadow-[0_0_20px_rgba(var(--color-kira),0.2)]"
        >
          <div className="absolute inset-0 bg-gradient-to-t from-kira/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
          
          <div className={`p-2.5 rounded-xl ${card.bg} ${card.color} mb-3 shadow-[inset_0_0_10px_rgba(255,255,255,0.1)] group-hover:scale-110 transition-transform`}>
            {card.icon}
          </div>
          
          <p className={`text-2xl font-mono font-bold tracking-tight ${card.color === 'text-kira' ? 'text-text-bright drop-shadow-[0_0_8px_rgba(var(--color-kira),0.8)]' : 'text-text-bright drop-shadow-[0_0_5px_rgba(255,255,255,0.3)]'}`}>
            {card.value}
          </p>
          
          <p className="text-[10px] uppercase font-bold tracking-wider text-text-dim mt-2 group-hover:text-kira/80 transition-colors">
            {card.label}
          </p>
        </motion.div>
      ))}
    </div>
  )
}

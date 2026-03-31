'use client'

import { useState } from 'react'
import { Award, Trophy, Star, Zap, Info, X, Lock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const ALL_ACHIEVEMENTS = [
  { id: 'first_prompt', name: 'First Prompt', icon: '📝', description: 'Created first prompt' },
  { id: 'ten', name: 'Getting Started', icon: '📝📝', description: 'Created 10 prompts' },
  { id: 'hundred', name: 'Century', icon: '💯', description: 'Created 100 prompts' },
  { id: 'quality_pro', name: 'Quality Pro', icon: '⭐', description: 'Average quality 4.0+' },
  { id: 'quality_master', name: 'Quality Master', icon: '⭐⭐', description: 'Average quality 4.5+' }
]

interface Achievement {
  id: string
  name: string
  icon: string
  description: string
}

interface AchievementBadgesProps {
  achievements: Achievement[]
  isLoading: boolean
}

export default function AchievementBadges({ achievements, isLoading }: AchievementBadgesProps) {
  const [showInfo, setShowInfo] = useState(false)

  const getIconComponent = (icon: string) => {
    // Simple emoji rendering for now
    return <span className="text-xl">{icon}</span>
  }

  if (isLoading) {
    return (
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-kira/20 text-kira border border-kira/30 shadow-[0_0_10px_rgba(var(--color-kira),0.5)]">
            <Award size={18} />
          </div>
          <h3 className="text-sm font-bold tracking-widest text-text-bright uppercase">Neural Badges</h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-28 bg-layer3/50 backdrop-blur-sm rounded-xl border border-kira/10 animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)] relative overflow-hidden">
      {/* Background glow decoration */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-kira/10 rounded-full blur-3xl -z-10 animate-pulse pointer-events-none" />

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-kira/20 text-kira border border-kira/30 shadow-[0_0_10px_rgba(var(--color-kira),0.5)]">
            <Award size={18} />
          </div>
          <h3 className="text-sm font-bold tracking-widest text-text-bright uppercase">Neural Badges</h3>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setShowInfo(!showInfo)}
            className="p-1.5 rounded-full hover:bg-kira/20 text-kira/70 hover:text-kira focus:outline-none focus:ring-1 focus:ring-kira transition-colors"
            title="View Badge Directory"
          >
            <Info size={16} />
          </button>
          <span className="text-xs font-mono font-bold text-kira bg-kira/10 px-2 py-1 rounded shadow-[inset_0_0_5px_rgba(var(--color-kira),0.3)]">{achievements.length} UNLOCKED</span>
        </div>
      </div>

      <AnimatePresence>
        {showInfo && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden mb-6"
          >
            <div className="bg-layer1/90 rounded-xl border border-kira/30 p-4 shadow-[0_0_15px_rgba(var(--color-kira),0.2)]">
              <div className="flex items-center justify-between mb-3 border-b border-border-default/50 pb-2">
                <h4 className="text-xs font-mono tracking-widest text-text-bright uppercase">Available Protocols</h4>
                <button onClick={() => setShowInfo(false)} className="text-text-dim hover:text-kira"><X size={14}/></button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                {ALL_ACHIEVEMENTS.map(ach => {
                  const isUnlocked = achievements.some(a => a.id === ach.id)
                  return (
                    <div key={ach.id} className={`flex items-center gap-3 p-2 rounded-lg border transition-all ${isUnlocked ? 'bg-kira/10 border-kira/30 text-text-bright shadow-[inset_0_0_10px_rgba(var(--color-kira),0.2)]' : 'bg-layer2/50 border-border-default md:opacity-60 text-text-dim'}`}>
                      <div className={`text-xl ${!isUnlocked && 'grayscale opacity-50'}`}>{ach.icon}</div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-[10px] font-bold font-mono tracking-widest uppercase">{ach.name}</p>
                          {!isUnlocked && <Lock size={10} className="text-text-dim/50" />}
                        </div>
                        <p className="text-[9px] font-mono mt-0.5 opacity-80">{ach.description}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 relative z-10">
        {achievements.length === 0 ? (
          <div className="col-span-2 sm:col-span-3 text-center py-10 bg-layer1/30 rounded-xl border border-kira/10 backdrop-blur-sm">
            <Award size={32} className="mx-auto mb-3 text-kira opacity-30 animate-pulse" />
            <p className="text-sm font-mono text-kira/70 uppercase">No Data Imprint</p>
            <p className="text-xs text-text-dim mt-1">Keep forging to unlock neural badges</p>
          </div>
        ) : (
          achievements.map((achievement, index) => (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.05, y: -5 }}
              key={achievement.id}
              className="group relative p-4 rounded-xl bg-layer1/60 border border-kira/30 hover:border-kira shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] hover:shadow-[0_0_20px_rgba(var(--color-kira),0.4)] transition-all text-center overflow-hidden backdrop-blur-md cursor-help"
              title={achievement.description}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-kira/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
              <div className="mb-2 transform group-hover:scale-110 transition-transform drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]">{getIconComponent(achievement.icon)}</div>
              <p className="text-xs font-bold font-mono tracking-tight text-text-bright line-clamp-1 group-hover:text-white transition-colors">
                {achievement.name}
              </p>
              <p className="text-[10px] text-kira/70 line-clamp-2 mt-1 leading-tight group-hover:text-kira transition-colors">
                {achievement.description}
              </p>
            </motion.div>
          ))
        )}
      </div>
    </div>
  )
}

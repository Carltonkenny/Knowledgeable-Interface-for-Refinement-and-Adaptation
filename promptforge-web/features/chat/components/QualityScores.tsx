// features/chat/components/QualityScores.tsx
// 3 Premium Liquid SVG Rings (Specificity, Clarity, Actionability)

import { motion } from 'framer-motion'
import type { QualityScore } from '@/lib/api'

interface QualityScoresProps {
  scores: QualityScore
}

export default function QualityScores({ scores }: QualityScoresProps) {
  if (!scores || typeof scores !== 'object') return null

  const items = [
    { label: 'Specificity', value: scores.specificity ?? 0 },
    { label: 'Clarity', value: scores.clarity ?? 0 },
    { label: 'Actionability', value: scores.actionability ?? 0 },
  ]

  return (
    <div className="flex items-center justify-between gap-4 mt-6 pt-5 border-t border-white/5 relative">
      <div className="absolute inset-0 bg-gradient-to-r from-[var(--kira-primary)]/5 via-transparent to-[var(--kira-primary)]/5 opacity-30 pointer-events-none" />
      
      {items.map((item, idx) => (
        <ProgressRing 
          key={item.label} 
          label={item.label} 
          value={item.value} 
          delay={0.1 * idx} 
        />
      ))}
    </div>
  )
}

function ProgressRing({ label, value, delay }: { label: string, value: number, delay: number }) {
  const radius = 22
  const circumference = 2 * Math.PI * radius
  const cappedValue = Math.min(Math.max(value, 0), 5) // Cap 0-5
  const strokeDashoffset = circumference - (cappedValue / 5) * circumference

  // Compute liquid colors based on score
  const isHighScore = value >= 4;
  const strokeColor = isHighScore ? 'url(#liquid-gradient-high)' : 'url(#liquid-gradient-mid)'

  return (
    <div className="flex flex-col items-center gap-2 group relative z-10 w-1/3">
      <div className="relative flex items-center justify-center">
        {/* Glow behind ring */}
        <div 
          className="absolute inset-0 rounded-full blur-[10px] transition-opacity duration-700 opacity-20 group-hover:opacity-40"
          style={{ backgroundColor: isHighScore ? 'var(--kira-primary)' : '#888' }}
        />

        <svg width="56" height="56" className="transform -rotate-90 drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]">
          <defs>
            <linearGradient id="liquid-gradient-high" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="var(--kira-primary)" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
            <linearGradient id="liquid-gradient-mid" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#888" />
              <stop offset="100%" stopColor="#aaa" />
            </linearGradient>
          </defs>

          {/* Background Track */}
          <circle
            cx="28"
            cy="28"
            r={radius}
            fill="transparent"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth="4"
          />

          {/* Animated Liquid Ring */}
          <motion.circle
            cx="28"
            cy="28"
            r={radius}
            fill="transparent"
            stroke={strokeColor}
            strokeWidth="4"
            strokeLinecap="round"
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, delay, ease: [0.23, 1, 0.32, 1] }}
            style={{ strokeDasharray: circumference }}
            className="filter drop-shadow-[0_0_2px_rgba(255,255,255,0.5)]"
          />
        </svg>

        {/* Center Value Text */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: delay + 0.3, ease: "easeOut" }}
          className="absolute flex items-baseline gap-0.5"
        >
          <span className="font-mono text-sm font-bold text-white group-hover:text-[var(--kira-primary)] transition-colors duration-300 drop-shadow-md">
            {value.toFixed(1)}
          </span>
        </motion.div>
      </div>

      <span className="text-[10px] uppercase tracking-widest font-mono text-white/50 group-hover:text-white/80 transition-colors duration-300 text-center">
        {label}
      </span>
    </div>
  )
}

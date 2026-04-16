// features/chat/components/EmptyState.tsx
// First-visit empty state with animated floating prompts and liquid glass aesthetics

import { useEffect, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'

interface EmptyStateProps {
  domain?: string
  onSuggestionClick: (text: string) => void
}

const ENGINEERING_PROMPTS = [
  "Draft a crisp system architecture doc for a Next.js microservice",
  "Write an exhaustive code review checklist for senior devs",
  "Engineer a strict system prompt for a specialized SQL agent",
  "Explain this complex race condition like I'm a junior dev",
  "Refactor this monolithic component using Atomic Design principles",
  "Create a comprehensive disaster recovery protocol",
  "Write a highly visual runbook for deploying to Kubernetes",
  "Draft a security audit report template for a fintech app",
]

const STRATEGY_PROMPTS = [
  "Write a compelling executive summary for our Series A pitch",
  "Draft a Q3 performance review for a high-performing PM",
  "Create a crisp highly actionable OKR framework",
  "Synthesize these user interview notes into 3 core insights",
  "Write a 90-day onboarding plan for a Staff Engineer",
  "Draft a go-to-market strategy for a developer tool",
  "Redesign our SaaS pricing tiers for enterprise clients",
  "Write a highly technical post-mortem for a production outage",
]

const CREATIVE_PROMPTS = [
  "Suggest 5 high-converting cold email hooks for B2B SaaS",
  "Write a punchy LinkedIn post analyzing the latest AI trends",
  "Draft an empathetic response to a frustrated enterprise client",
  "Create a highly visual content calendar for deep-tech blogs",
  "Write an engaging product launch announcement for our changelog",
  "Draft a professional rejection letter for a senior candidate",
  "Design a highly converting landing page wireframe prompt",
  "Write a compelling brand manifesto for an AI startup",
]

export default function EmptyState({ domain, onSuggestionClick }: EmptyStateProps) {
  // Prevent hydration mismatch for animations
  const [isMounted, setIsMounted] = useState(false)
  
  // Pause animation state on hover
  const [isHovered, setIsHovered] = useState(false)

  useEffect(() => setIsMounted(true), [])

  if (!isMounted) return null

  return (
    <div className="flex flex-col items-center justify-center h-full w-full overflow-hidden relative">
      
      {/* Background ambient liquid glow */}
      <div className="absolute inset-0 bg-transparent pointer-events-none flex items-center justify-center">
        <div className="w-[600px] h-[600px] bg-[var(--kira-primary)]/10 rounded-full blur-[120px] opacity-60 block mix-blend-screen" />
      </div>

      {/* Kira avatar & Welcome Header (Z-index above floating items but below interactions) */}
      <div className="relative z-10 flex flex-col items-center mb-16 pointer-events-none">
        <div className="w-16 h-16 rounded-2xl border border-[var(--kira-primary)]/40 bg-[var(--kira-primary)]/10 backdrop-blur-2xl shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_0_30px_rgba(var(--kira-primary-rgb),0.2)] flex items-center justify-center mb-6">
          <span className="text-[var(--kira-primary)] font-bold font-mono text-3xl drop-shadow-[0_0_10px_rgba(var(--kira-primary-rgb),0.8)]">K</span>
        </div>
        <p className="text-white/80 text-lg max-w-md text-center font-medium drop-shadow-md">
          {domain
            ? `${domain} mode — ready. Paste a rough idea and I'll engineer it into a precise prompt.`
            : "Ready when you are. Paste a rough idea and I'll turn it into a production-grade prompt."}
        </p>
      </div>

      {/* Floating Prompt Marquee System */}
      <div 
        className="w-full relative py-6 flex flex-col gap-6 transform rotate-[-2deg] mask-image-[linear-gradient(to_right,transparent,black_15%,black_85%,transparent)]"
        style={{ WebkitMaskImage: 'linear-gradient(to right, transparent, black 15%, black 85%, transparent)' }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >

        {/* 
          Using exactly [...PROMPTS, ...PROMPTS] and animating from x: 0% to x: -50% 
          creates a mathematically perfect visual loop since the second half replaces the first.
        */}

        {/* Lane 1: Engineering (Left) */}
        <div className="flex overflow-visible w-full min-w-max">
          <motion.div 
            animate={{ x: isHovered ? undefined : ["0%", "-50%"] }}
            transition={{ ease: "linear", duration: 45, repeat: Infinity }}
            className="flex gap-4 pr-4 w-max"
          >
            {[...ENGINEERING_PROMPTS, ...ENGINEERING_PROMPTS].map((suggestion, index) => (
              <PromptPill key={`eng-${index}`} text={suggestion} onClick={() => onSuggestionClick(suggestion)} index={index} />
            ))}
          </motion.div>
        </div>

        {/* Lane 2: Strategy (Right) */}
        <div className="flex overflow-visible w-full min-w-max justify-end">
          <motion.div 
            animate={{ x: isHovered ? undefined : ["-50%", "0%"] }}
            transition={{ ease: "linear", duration: 55, repeat: Infinity }}
            className="flex gap-4 pr-4 w-max"
          >
            {[...STRATEGY_PROMPTS, ...STRATEGY_PROMPTS].map((suggestion, index) => (
              <PromptPill key={`strat-${index}`} text={suggestion} onClick={() => onSuggestionClick(suggestion)} index={index} />
            ))}
          </motion.div>
        </div>

        {/* Lane 3: Creative (Left) */}
        <div className="flex overflow-visible w-full min-w-max">
          <motion.div 
            animate={{ x: isHovered ? undefined : ["0%", "-50%"] }}
            transition={{ ease: "linear", duration: 65, repeat: Infinity }}
            className="flex gap-4 pr-4 w-max"
          >
            {[...CREATIVE_PROMPTS, ...CREATIVE_PROMPTS].map((suggestion, index) => (
              <PromptPill key={`create-${index}`} text={suggestion} onClick={() => onSuggestionClick(suggestion)} index={index} />
            ))}
          </motion.div>
        </div>

      </div>
    </div>
  )
}

function PromptPill({ text, onClick, index }: { text: string, onClick: () => void, index: number }) {
  // Compute deterministic floating params based on index to prevent layout thrashing
  const yDistance = index % 2 === 0 ? -8 : 8;
  const duration = 4 + (index % 3);

  return (
    <motion.button
      onClick={onClick}
      // The true sine-wave zero-gravity float
      animate={{ y: [0, yDistance, 0] }}
      transition={{ duration, repeat: Infinity, ease: "easeInOut" }}
      className="px-6 py-3 rounded-full border border-white/10 bg-white/5 backdrop-blur-xl hover:bg-white/15 hover:border-white/30 transition-colors duration-500 ease-out flex items-center justify-between group shadow-[inset_0_1px_1px_rgba(255,255,255,0.08),0_4px_16px_rgba(0,0,0,0.15)] relative overflow-hidden cursor-pointer w-max"
      whileHover={{ scale: 1.05, y: 0 }}
    >
      {/* Liquid Shimmer Sweep */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-150%] group-hover:translate-x-[150%] transition-transform duration-[1200ms] ease-in-out" />
      
      {/* Kira Primary Liquid Glow on Hover */}
      <div className="absolute inset-0 bg-[var(--kira-primary)]/0 group-hover:bg-[var(--kira-primary)]/10 transition-colors duration-500" />
      
      <span className="text-white/70 group-hover:text-white/95 text-[13px] font-medium tracking-wide z-10 transition-colors duration-300">
        {text}
      </span>
      <Sparkles className="w-4 h-4 ml-3 opacity-0 group-hover:opacity-100 text-[var(--kira-primary)] transition-all duration-300 transform scale-50 group-hover:scale-100 z-10 drop-shadow-[0_0_5px_rgba(var(--kira-primary-rgb),1)]" />
    </motion.button>
  )
}


// features/chat/components/AgentThought.tsx
// Displays individual agent thinking with latency and skip reasons

'use client'

import { motion } from 'framer-motion'
import { Brain, Target, Users, Globe, Wrench, SkipForward, Clock } from 'lucide-react'

interface AgentData {
  // Orchestrator data
  agents_to_run?: string[]
  clarification_needed?: boolean
  tone_used?: string
  skip_reasons?: Record<string, string>

  // Intent data
  primary_intent?: string
  goal_clarity?: string
  missing_info?: string[]

  // Context data
  skill_level?: string
  tone?: string
  constraints?: string[]
  implicit_preferences?: string[]

  // Domain data
  primary_domain?: string
  sub_domain?: string
  relevant_patterns?: string[]
  complexity?: string
  confidence?: number

  // Engineer data
  quality_score?: Record<string, number>
  agents_run?: string[]
  agents_skipped?: string[]
}

interface AgentThoughtProps {
  agent: 'orchestrator' | 'intent' | 'context' | 'domain' | 'engineer'
  status: 'running' | 'complete' | 'skipped'
  latencyMs: number
  data?: AgentData | null
  skipReason?: string
  memoriesApplied?: number
}

const AGENT_CONFIG = {
  orchestrator: {
    icon: Brain,
    label: 'Kira Core System',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/20'
  },
  intent: {
    icon: Target,
    label: 'Intent Analyst',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/20'
  },
  context: {
    icon: Users,
    label: 'Context Engine',
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/20'
  },
  domain: {
    icon: Globe,
    label: 'Domain Specialist',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20'
  },
  engineer: {
    icon: Wrench,
    label: 'Prompt Synthesizer',
    color: 'text-pink-400',
    bgColor: 'bg-pink-500/10',
    borderColor: 'border-pink-500/20'
  }
}

export default function AgentThought({
  agent,
  status,
  latencyMs,
  data,
  skipReason,
  memoriesApplied
}: AgentThoughtProps) {
  const config = AGENT_CONFIG[agent]
  const Icon = config.icon

  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const renderData = () => {
    if (!data) return null

    switch (agent) {
      case 'orchestrator':
        return (
          <div className="space-y-1.5 text-xs">
            {data.agents_to_run && data.agents_to_run.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                <span className="text-white/50">Agents:</span>
                {data.agents_to_run.map((a) => (
                  <span key={a} className="px-1.5 py-0.5 rounded bg-white/10 text-white/80 font-mono text-[10px]">
                    {a}
                  </span>
                ))}
              </div>
            )}
            {data.tone_used && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Tone:</span>
                <span className="text-white/80 capitalize">{data.tone_used}</span>
              </div>
            )}
            {memoriesApplied !== undefined && memoriesApplied > 0 && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Memories:</span>
                <span className="text-white/80">{memoriesApplied} recalled</span>
              </div>
            )}
            {data.skip_reasons && Object.entries(data.skip_reasons).length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                <span className="text-white/50">Skipped:</span>
                {Object.entries(data.skip_reasons).map(([key, reason]) => (
                  <span key={key} className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 font-mono text-[10px]">
                    {key}
                  </span>
                ))}
              </div>
            )}
          </div>
        )

      case 'intent':
        return (
          <div className="space-y-1.5 text-xs">
            {data.primary_intent && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Goal:</span>
                <span className="text-white/80 italic">"{data.primary_intent}"</span>
              </div>
            )}
            {data.goal_clarity && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Clarity:</span>
                <span className={`font-medium ${
                  data.goal_clarity === 'high' ? 'text-green-400' :
                  data.goal_clarity === 'medium' ? 'text-amber-400' :
                  'text-red-400'
                }`}>
                  {data.goal_clarity.toUpperCase()}
                </span>
              </div>
            )}
            {data.missing_info && data.missing_info.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                <span className="text-white/50">Missing:</span>
                {data.missing_info.map((info, i) => (
                  <span key={i} className="px-1.5 py-0.5 rounded bg-red-500/10 text-red-300 text-[10px]">
                    {info}
                  </span>
                ))}
              </div>
            )}
            {data.missing_info && data.missing_info.length === 0 && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Missing:</span>
                <span className="text-green-400">None — crystal clear</span>
              </div>
            )}
          </div>
        )

      case 'context':
        return (
          <div className="space-y-1.5 text-xs">
            {data.skill_level && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Skill:</span>
                <span className="text-white/80 capitalize">{data.skill_level}</span>
              </div>
            )}
            {data.tone && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Tone:</span>
                <span className="text-white/80 capitalize">{data.tone}</span>
              </div>
            )}
            {data.constraints && data.constraints.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                <span className="text-white/50">Constraints:</span>
                {data.constraints.map((c, i) => (
                  <span key={i} className="px-1.5 py-0.5 rounded bg-white/10 text-white/80 text-[10px]">
                    {c}
                  </span>
                ))}
              </div>
            )}
          </div>
        )

      case 'domain':
        return (
          <div className="space-y-1.5 text-xs">
            {data.primary_domain && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Domain:</span>
                <span className="text-white/80">{data.primary_domain}</span>
              </div>
            )}
            {data.sub_domain && data.sub_domain !== 'general' && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Sub-domain:</span>
                <span className="text-white/80 italic">({data.sub_domain})</span>
              </div>
            )}
            {data.relevant_patterns && data.relevant_patterns.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                <span className="text-white/50">Patterns:</span>
                {data.relevant_patterns.map((p, i) => (
                  <span key={i} className="px-1.5 py-0.5 rounded bg-white/10 text-white/80 font-mono text-[10px]">
                    {p}
                  </span>
                ))}
              </div>
            )}
            {data.complexity && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Complexity:</span>
                <span className={`font-medium ${
                  data.complexity === 'simple' ? 'text-green-400' :
                  data.complexity === 'moderate' ? 'text-amber-400' :
                  'text-red-400'
                }`}>
                  {data.complexity}
                </span>
              </div>
            )}
            {data.confidence && (
              <div className="flex gap-1.5">
                <span className="text-white/50">Confidence:</span>
                <span className="text-white/80">{(data.confidence * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>
        )

      case 'engineer':
        return (
          <div className="space-y-1.5 text-xs">
            {data.agents_run && data.agents_run.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                <span className="text-white/50">Agents:</span>
                {data.agents_run.map((a) => (
                  <span key={a} className="px-1.5 py-0.5 rounded bg-green-500/10 text-green-300 font-mono text-[10px]">
                    {a}
                  </span>
                ))}
              </div>
            )}
            {data.agents_skipped && data.agents_skipped.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                <span className="text-white/50">Skipped:</span>
                {data.agents_skipped.map((a) => (
                  <span key={a} className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 font-mono text-[10px]">
                    {a}
                  </span>
                ))}
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  // Skipped state
  if (status === 'skipped') {
    return (
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        className="relative flex gap-4 w-full pb-6"
      >
        <div className="relative z-10 flex-shrink-0">
          <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white/5 border border-white/10">
            <SkipForward className={`w-3.5 h-3.5 ${config.color} opacity-50`} strokeWidth={2.5} />
          </div>
        </div>
        <div className="flex-1 pt-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-white/40 text-[13px]">{config.label}</span>
            <span className="text-[10px] text-white/30 font-mono">({formatLatency(latencyMs)})</span>
          </div>
          {skipReason && (
            <div className="text-[11px] text-white/30 mt-1">
              {skipReason}
            </div>
          )}
        </div>
      </motion.div>
    )
  }

  // Running state
  if (status === 'running') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="relative flex gap-4 w-full pb-6"
      >
        <div className="relative z-10 flex-shrink-0">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${config.bgColor} border ${config.borderColor} shadow-[0_0_15px_rgba(255,255,255,0.05)]`}>
            <Icon className={`w-4 h-4 ${config.color} animate-pulse`} strokeWidth={2} />
          </div>
        </div>
        <div className="flex-1 pt-1.5 flex items-center gap-2 text-white/60">
          <span className="font-medium text-[13px] tracking-wide">{config.label}</span>
          <div className="flex gap-1">
            <span className="w-1 h-1 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1 h-1 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1 h-1 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </motion.div>
    )
  }

  // Handle Missing Info / Amber Node edge cases
  const isMissingInfo = agent === 'intent' && data?.missing_info && data.missing_info.length > 0;
  const isWarning = isMissingInfo || agent === 'orchestrator' && data?.clarification_needed;

  const nodeBgColor = isWarning ? 'bg-amber-500/10' : config.bgColor;
  const nodeBorderColor = isWarning ? 'border-amber-500/30' : config.borderColor;
  const iconColor = isWarning ? 'text-amber-400' : config.color;

  // Complete state
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="relative flex gap-4 w-full pb-6 group"
    >
      {/* Node */}
      <div className="relative z-10 flex-shrink-0">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${nodeBgColor} border ${nodeBorderColor} shadow-md transition-all duration-300 group-hover:scale-105`}>
          <Icon className={`w-4 h-4 ${iconColor}`} strokeWidth={2} />
        </div>
      </div>

      {/* Content wrapper */}
      <div className="flex-1 pt-0.5">
        <div className="flex items-center gap-2 mb-2">
          <span className={`font-medium text-[13px] ${isWarning ? 'text-amber-200' : 'text-white/90'}`}>{config.label}</span>
          <span className="text-[10px] text-white/40 font-mono tracking-wider">({formatLatency(latencyMs)})</span>
          {isWarning && (
            <span className="px-1.5 py-0.5 rounded text-[9px] uppercase tracking-widest bg-amber-500/20 text-amber-300 ml-auto border border-amber-500/20">Action Required</span>
          )}
        </div>

        {/* Data Box */}
        <div className="p-3.5 bg-black/20 rounded-xl border border-white/5 shadow-[inset_0_1px_1px_rgba(255,255,255,0.02)] backdrop-blur-sm group-hover:bg-black/30 transition-colors duration-300">
            {renderData()}
        </div>
      </div>
    </motion.div>
  )
}

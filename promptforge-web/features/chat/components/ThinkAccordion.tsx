// features/chat/components/ThinkAccordion.tsx
// Modern AI Think Mode — Shows real agent thinking with expandable details

'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight, Brain, CheckCircle, SkipForward, Clock } from 'lucide-react'
import AgentThought from './AgentThought'
import type { ProcessingStatus } from '../types'

interface AgentState {
  status: 'idle' | 'running' | 'complete' | 'skipped'
  latencyMs: number
  data?: any | null
  skipReason?: string
  memoriesApplied?: number
}

interface ThinkAccordionProps {
  status: ProcessingStatus
}

export default function ThinkAccordion({ status }: ThinkAccordionProps) {
  const isRunning = status.state === 'kira_reading' || status.state === 'swarm_running'
  const isDone = status.state === 'complete'

  const [isExpanded, setIsExpanded] = useState(false)

  // Agent states tracking
  const [agentStates, setAgentStates] = useState<Record<string, AgentState>>({
    orchestrator: { status: 'idle', latencyMs: 0, data: null },
    intent: { status: 'idle', latencyMs: 0, data: null },
    context: { status: 'idle', latencyMs: 0, data: null },
    domain: { status: 'idle', latencyMs: 0, data: null },
    engineer: { status: 'idle', latencyMs: 0, data: null },
  })

  // Auto-expand when swarm starts, collapse when done
  useEffect(() => {
    if (isRunning) {
      setIsExpanded(true)
    } else if (isDone) {
      setIsExpanded(false)
    }
  }, [isRunning, isDone])

  // Update agent states from status updates
  useEffect(() => {
    if (status.agentUpdates) {
      status.agentUpdates.forEach((update) => {
        setAgentStates((prev) => ({
          ...prev,
          [update.agent]: {
            status: update.state,
            latencyMs: update.latency_ms,
            data: update.data,
            skipReason: update.skip_reason,
            memoriesApplied: update.memories_applied,
          },
        }))
      })
    }
  }, [status.agentUpdates])

  // Don't render if completely idle
  if (status.state === 'idle' || (isDone && (!status.statusLogs || status.statusLogs.length === 0))) {
    return null
  }

  // Calculate total latency
  const totalLatency = Object.values(agentStates).reduce(
    (sum, state) => sum + state.latencyMs,
    0
  )

  // Format latency for display
  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  // Count completed agents
  const completedCount = Object.values(agentStates).filter(
    (s) => s.status === 'complete'
  ).length
  const skippedCount = Object.values(agentStates).filter(
    (s) => s.status === 'skipped'
  ).length

  return (
    <div className="w-full max-w-2xl mx-auto mb-6 px-4">
      {/* Header Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls="kira-analysis-pipeline"
        aria-label={isRunning ? "Kira analysis in progress" : "View Kira's analysis details"}
        className={`group flex items-center gap-2.5 px-4 py-2.5 rounded-full text-[13px] font-semibold transition-all duration-400 ease-[0.23,1,0.32,1] backdrop-blur-3xl border shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)]
          ${isRunning
            ? 'bg-[var(--kira-primary)]/15 text-[var(--kira-primary)] border-[var(--kira-primary)]/30 animate-pulse-soft shadow-[0_0_20px_rgba(var(--kira-primary-rgb),0.15)]'
            : 'bg-white/5 text-white/80 border-white/10 hover:bg-white/10 hover:text-white hover:border-white/20 hover:shadow-[0_8px_16px_rgba(0,0,0,0.2)]'
          }`}
      >
        <Brain className={`w-4 h-4 transition-transform duration-500 group-hover:scale-110 ${isRunning ? 'animate-pulse' : ''}`} />
        <span className="tracking-wide">
          {isRunning
            ? `Kira is analyzing... (${completedCount}/${4 - skippedCount} nodes)`
            : status.state === 'clarification'
            ? 'Analysis Finalized'
            : isDone && totalLatency > 0
            ? `Analysis Engine (${formatLatency(totalLatency)})`
            : 'Analysis Details'}
        </span>
        <ChevronDown className={`w-3.5 h-3.5 ml-1 transition-transform duration-500 ease-[0.23,1,0.32,1] ${isExpanded ? 'rotate-0' : '-rotate-90'}`} />
      </button>

      {/* Accordion Body */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            id="kira-analysis-pipeline"
            role="region"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }} 
            className="overflow-hidden"
          >
            <div className="mt-4 p-6 rounded-3xl bg-[#08080a]/60 border border-white/5 backdrop-blur-3xl shadow-[inset_0_1px_1px_rgba(255,255,255,0.03),0_20px_40px_rgba(0,0,0,0.4)] flex flex-col gap-4 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.04] to-transparent pointer-events-none" />
              
              {/* Discovery Logs */}
              {status.statusLogs && status.statusLogs.length > 0 && (
                <div 
                  className="relative z-10 space-y-2 pb-4 border-b border-white/5 mb-2"
                  aria-live="polite"
                >
                  <AnimatePresence initial={false}>
                    {status.statusLogs.map((log, i) => (
                      <motion.div
                        key={`log-${i}`}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center gap-3 text-[11px] sm:text-[12px] text-white/50 font-mono pl-1"
                      >
                        <div className="w-1.5 h-1.5 rounded-full bg-[var(--kira-primary)]/50 shadow-[0_0_8px_rgba(var(--kira-primary-rgb),0.4)] flex-shrink-0" />
                        <span className="flex-1 break-words leading-relaxed tracking-tight">{log}</span>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}

              {/* Total latency badge */}
              {isDone && totalLatency > 0 && (
                <div className="absolute top-4 right-4 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
                  <Clock className="w-3.5 h-3.5 text-white/40" />
                  <span className="text-xs text-white/60 font-mono">{formatLatency(totalLatency)}</span>
                </div>
              )}

              {/* Enterprise Timeline Analysis */}
              <div className="relative pt-2 sm:pt-4 sm:pl-2">
                {/* The vertical timeline connector stroke */}
                <div className="absolute left-[15.5px] sm:left-[23.5px] top-6 bottom-[60px] w-[1px] bg-gradient-to-b from-white/20 via-white/10 to-transparent shadow-[0_0_10px_rgba(255,255,255,0.05)]" />

                <div className="relative z-10 flex flex-col">
                  {Object.entries(agentStates)
                    .filter(([_, state]) => state.status !== 'idle')
                    .map(([agentName, agentState]) => (
                      <AgentThought
                        key={agentName}
                        agent={agentName as any}
                        status={agentState.status as any}
                        latencyMs={agentState.latencyMs}
                        data={agentState.data}
                        skipReason={agentState.skipReason}
                        memoriesApplied={agentState.memoriesApplied}
                      />
                    ))}
                </div>
              </div>

              {/* Empty state while loading */}
              {isRunning && completedCount === 0 && skippedCount === 0 && (!status.statusLogs || status.statusLogs.length === 0) && (
                <div className="pl-6 text-sm text-white/50 flex items-center gap-2 py-4">
                  <div className="w-4 h-4 rounded-full border-2 border-white/10 border-t-white/50 animate-spin" />
                  Initializing enterprise analysis thread...
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

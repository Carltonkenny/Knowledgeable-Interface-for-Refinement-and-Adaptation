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
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border
          ${isRunning
            ? 'bg-[var(--kira-primary)]/10 text-[var(--kira-primary)] border-[var(--kira-primary)]/20 animate-pulse-soft'
            : 'bg-white/5 text-white/60 border-white/10 hover:bg-white/10 hover:text-white/90'
          }`}
      >
        <Brain className={`w-4 h-4 ${isRunning ? 'animate-pulse' : ''}`} />
        <span>
          {isRunning
            ? `Kira is analyzing... (${completedCount}/${4 - skippedCount} modules)`
            : status.state === 'clarification'
            ? 'Analysis Complete ✨'
            : isDone && totalLatency > 0
            ? `Kira's Analysis (${formatLatency(totalLatency)} total)`
            : 'Kira\'s Analysis'}
        </span>
        {isExpanded ? <ChevronDown className="w-4 h-4 ml-1" /> : <ChevronRight className="w-4 h-4 ml-1" />}
      </button>

      {/* Accordion Body */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="mt-3 p-4 rounded-xl bg-black/40 border border-white/10 backdrop-blur-md shadow-inner flex flex-col gap-3 relative">
              
              {/* PHASE 1: Discovery (Status Logs from Brain/Memories) */}
              {status.statusLogs && status.statusLogs.length > 0 && (
                <div className="space-y-1.5 pb-2 border-b border-white/5">
                  <AnimatePresence initial={false}>
                    {status.statusLogs.map((log, i) => (
                      <motion.div
                        key={`log-${i}`}
                        initial={{ opacity: 0, x: -5 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center gap-2 text-[11px] text-white/60 font-mono pl-1"
                      >
                        <div className="w-1 h-1 rounded-full bg-[var(--kira-primary)]/40" />
                        {log}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}

              {/* Total latency badge */}
              {isDone && totalLatency > 0 && (
                <div className="absolute top-3 right-3 flex items-center gap-1 px-2 py-1 rounded-full bg-white/5 border border-white/10">
                  <Clock className="w-3 h-3 text-white/40" />
                  <span className="text-xs text-white/60 font-mono">{formatLatency(totalLatency)}</span>
                </div>
              )}

              {/* Agent Thinking Cards */}
              <div className="space-y-2">
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

              {/* Empty state while loading */}
              {isRunning && completedCount === 0 && skippedCount === 0 && (!status.statusLogs || status.statusLogs.length === 0) && (
                <div className="pl-6 text-sm text-white/50 animate-pulse flex items-center gap-2">
                  <Clock className="w-4 h-4 animate-pulse" />
                  Initializing modules...
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

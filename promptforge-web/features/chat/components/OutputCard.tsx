// features/chat/components/OutputCard.tsx
// Engineered prompt card with diff, quality scores, actions

'use client'

import { useState } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { Chip } from '@/components/ui'
import { History as HistoryIcon } from 'lucide-react'
import { cn, formatDuration } from '@/lib/utils'
import DiffView from './DiffView'
import QualityScores from './QualityScores'
import type { ChatResult } from '@/lib/api'
import { useImplicitFeedback } from '../hooks/useImplicitFeedback'

interface OutputCardProps {
  promptId: string
  sessionId: string
  result: ChatResult
}

// Helper function for safe diff counting (DRY principle)
const countDiffType = (diff: ChatResult['diff'], type: 'add' | 'remove'): number => {
  if (!Array.isArray(diff)) return 0
  return diff.filter((d) => d?.type === type).length
}

export default function OutputCard({ promptId, sessionId, result }: OutputCardProps) {
  const shouldReduce = useReducedMotion()
  const [showDiff, setShowDiff] = useState(false)
  const [isCopied, setIsCopied] = useState(false)

  const { trackCopy } = useImplicitFeedback(
    sessionId,
    promptId,
    result.improved_prompt
  )

  const handleCopy = () => {
    navigator.clipboard.writeText(result.improved_prompt)
    setIsCopied(true)
    trackCopy()
    setTimeout(() => setIsCopied(false), 2000)
  }

  // Count additions/removals for annotation chips using safe helper
  const additions = countDiffType(result.diff, 'add')
  const removals = countDiffType(result.diff, 'remove')

  // Strip markdown symbols for display only (preserve original for copy)
  const displayPrompt = result.improved_prompt
    ? result.improved_prompt.replace(/(\*\*|```|`|^#+\s)/gm, '')
    : ''

  return (
    <motion.div 
      layoutId={shouldReduce ? undefined : `output-card-${promptId}`}
      initial={{ opacity: 0, scale: shouldReduce ? 1 : 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 30, duration: shouldReduce ? 0 : undefined }}
      className="mb-6"
    >
      {/* Liquid Premium Glass Border Wrapper */}
      <div className="rounded-2xl p-[1px] bg-gradient-to-br from-white/15 via-white/5 to-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.3)]">
        <div className="bg-[#0a0a0c]/80 backdrop-blur-3xl rounded-[15px] p-6 relative overflow-hidden transition-all duration-400 ease-[0.23,1,0.32,1]">
          
          {/* Ambient Liquid Gradient Inside Card */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--kira-primary)]/10 blur-[80px] rounded-full pointer-events-none transform translate-x-1/2 -translate-y-1/2 mix-blend-screen" />
          {/* Header */}
          <div className="flex items-center gap-3 mb-4">
            <span className="font-mono text-[9px] tracking-widest uppercase text-white/50">
              Output Generation
            </span>
            {result.memories_applied > 0 && (
              <Chip variant="memory" className="bg-white/10 text-white/70">
                ● {result.memories_applied} memory matches
              </Chip>
            )}
            <span className="font-mono text-[10px] text-white/40 ml-auto">
              {formatDuration(result.latency_ms)}
            </span>
          </div>

          {/* Premium Syntax Block for Output */}
          <div className="relative group mb-5">
            <div className="absolute inset-0 bg-white/[0.02] rounded-xl border border-white/5 pointer-events-none shadow-[inset_0_1px_2px_rgba(255,255,255,0.02)]" />
            <p className="text-white/90 text-[15px] leading-relaxed p-5 whitespace-pre-wrap font-sans tracking-wide selection:bg-[var(--kira-primary)]/30">
              {displayPrompt}
            </p>
          </div>

          {/* Liquid Engineering Rationale */}
          <div className="flex flex-col gap-2 mb-5">
            <span className="text-[10px] uppercase tracking-wider font-mono text-[var(--kira-primary)] flex items-center gap-2 drop-shadow-[0_0_8px_rgba(var(--kira-primary-rgb),0.5)]">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--kira-primary)] animate-pulse" />
              Engineering Rationale
            </span>
            <div className="flex gap-2 flex-wrap">
              {additions > 0 && (
                <span className="px-2.5 py-1 text-xs rounded-md bg-white/5 text-white/80 border border-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] backdrop-blur-md">
                  <span className="text-green-400 mr-1">+</span> Injected precise constraints and expert persona
                </span>
              )}
              {removals > 0 && (
                <span className="px-2.5 py-1 text-xs rounded-md bg-white/5 text-white/80 border border-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] backdrop-blur-md">
                  <span className="text-red-400 mr-1">−</span> Excised vague or conflicting requirements
                </span>
              )}
              {additions === 0 && removals === 0 && (
                <span className="px-2.5 py-1 text-xs rounded-md bg-white/5 text-white/60 border border-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] backdrop-blur-md">
                  No structural changes required
                </span>
              )}
            </div>
          </div>

          {/* Diff toggle */}
          <button
            onClick={() => setShowDiff(!showDiff)}
            className="text-[11px] font-medium text-white/40 hover:text-[var(--kira-primary)] mb-3 transition-colors duration-300 ease-[0.23,1,0.32,1] flex items-center gap-1.5"
          >
            {showDiff ? 'Hide diff' : 'Show diff view'}
            <div className="w-1 h-1 rounded-full bg-white/20" />
          </button>

          {/* Diff view */}
          <AnimatePresence initial={false}>
            {showDiff && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: shouldReduce ? 0 : 0.4, ease: [0.23, 1, 0.32, 1] }}
                className="mb-4 overflow-hidden"
              >
                <div className="p-3 bg-[var(--surface-hover)] rounded-lg border border-border-subtle">
                  <DiffView diff={result.diff} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Quality scores */}
          {result.quality_score && <QualityScores scores={result.quality_score} />}

          {/* Suggestions/Alternative Paths */}
          {result.suggestions && result.suggestions.length > 0 && (
            <div className="mt-5 mb-2 pt-5 border-t border-white/5">
              <span className="text-[10px] uppercase tracking-widest font-mono text-white/60 block mb-4">
                Alternate Trajectories
              </span>
              <div className="flex flex-wrap gap-2">
                {result.suggestions.map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      const event = new CustomEvent('send-chat-message', { detail: { message: suggestion } })
                      window.dispatchEvent(event)
                    }}
                    className="text-xs bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 hover:shadow-[0_2px_8px_rgba(0,0,0,0.2)] text-white/80 hover:text-white px-3.5 py-2 rounded-full transition-all duration-300 backdrop-blur-sm"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between mt-5 pt-4 border-t border-white/5">
            <div className="flex gap-4">
              <button
                onClick={handleCopy}
                className="text-[11px] text-white/60 hover:text-white font-mono flex items-center gap-2 transition-all duration-300 ease-[0.23,1,0.32,1] hover:bg-white/5 px-2.5 py-1.5 rounded-lg border border-transparent hover:border-white/10"
              >
                <div className={cn("w-2 h-2 rounded-full transition-all duration-500", isCopied ? "bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)]" : "bg-white/20")} />
                {isCopied ? 'Action successful' : 'Copy result'}
              </button>

              {result.version_id && (
                <button
                  onClick={() => {
                    const event = new CustomEvent('open-version-history', { 
                      detail: { versionId: result.version_id, vNumber: result.version_number } 
                    })
                    window.dispatchEvent(event)
                  }}
                  className="text-xs text-[var(--kira-primary)] hover:text-white font-mono flex items-center gap-1.5 transition-colors duration-200"
                >
                  <HistoryIcon size={14} className="opacity-70" />
                  View History
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

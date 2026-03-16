// features/chat/components/OutputCard.tsx
// Engineered prompt card with diff, quality scores, actions

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Chip } from '@/components/ui'
import { History as HistoryIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
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

  return (
    <motion.div 
      layoutId={`output-card-${promptId}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="mb-6"
    >
      {/* Gradient border wrapper */}
      <div className="rounded-[11px] p-px bg-gradient-to-br from-kira/60 via-engineer/40 to-memory/30">
        <div className="bg-layer1 rounded-[10px] p-4">
          {/* Header */}
          <div className="flex items-center gap-3 mb-3">
            <span className="font-mono text-[9px] tracking-wider uppercase text-text-dim">
              Engineered prompt
            </span>
            {result.memories_applied > 0 && (
              <Chip variant="memory">
                ● {result.memories_applied} memories
              </Chip>
            )}
            <span className="font-mono text-[10px] text-teal">
              {result.latency_ms / 1000}s
            </span>
          </div>

          {/* Output text */}
          <p className="text-[--output-text] text-sm leading-relaxed mb-4">
            {result.improved_prompt}
          </p>

          {/* Annotation chips */}
          <div className="flex gap-2 mb-3 flex-wrap">
            {additions > 0 && (
              <Chip variant="context">+ Added structure</Chip>
            )}
            {removals > 0 && (
              <Chip variant="intent">− Removed vagueness</Chip>
            )}
          </div>

          {/* Diff toggle */}
          <button
            onClick={() => setShowDiff(!showDiff)}
            className="text-xs text-text-dim hover:text-text-bright mb-3"
          >
            {showDiff ? 'Hide diff' : 'Show diff'}
          </button>

          {/* Diff view */}
          <AnimatePresence initial={false}>
            {showDiff && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
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
            <div className="mt-4 mb-3 border-t border-border-subtle pt-4">
              <span className="text-[10px] uppercase tracking-wider font-mono text-text-dim block mb-2">
                Alternative paths
              </span>
              <div className="flex flex-wrap gap-2">
                {result.suggestions.map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      const event = new CustomEvent('send-chat-message', { detail: { message: suggestion } })
                      window.dispatchEvent(event)
                    }}
                    className="text-xs bg-layer2 hover:bg-layer3 border border-border-subtle hover:border-kira/40 text-text-bright px-3 py-1.5 rounded-full transition-all duration-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-4 mt-4 pt-4 border-t border-border-subtle">
            <button
              onClick={handleCopy}
              className="text-xs text-text-dim hover:text-text-bright font-mono flex items-center gap-1.5"
            >
              <div className={cn("w-1.5 h-1.5 rounded-full", isCopied ? "bg-green-400" : "bg-text-dim")} />
              {isCopied ? 'Copied!' : 'Copy'}
            </button>

            {result.version_id && (
              <button
                onClick={() => {
                  const event = new CustomEvent('open-version-history', { 
                    detail: { versionId: result.version_id, vNumber: result.version_number } 
                  })
                  window.dispatchEvent(event)
                }}
                className="text-xs text-kira hover:text-kira-bright font-mono flex items-center gap-1.5"
              >
                <HistoryIcon size={14} />
                History
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

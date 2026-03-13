// features/chat/components/OutputCard.tsx
// Engineered prompt card with diff, quality scores, actions

'use client'

import { useState } from 'react'
import { Chip } from '@/components/ui'
import DiffView from './DiffView'
import QualityScores from './QualityScores'
import type { ChatResult } from '@/lib/api'

interface OutputCardProps {
  result: ChatResult
  onCopy: () => void
  isCopied: boolean
}

// Helper function for safe diff counting (DRY principle)
const countDiffType = (diff: ChatResult['diff'], type: 'add' | 'remove'): number => {
  if (!Array.isArray(diff)) return 0
  return diff.filter((d) => d?.type === type).length
}

export default function OutputCard({ result, onCopy, isCopied }: OutputCardProps) {
  const [showDiff, setShowDiff] = useState(false)

  // Count additions/removals for annotation chips using safe helper
  const additions = countDiffType(result.diff, 'add')
  const removals = countDiffType(result.diff, 'remove')

  return (
    <div className="mb-6">
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
          {showDiff && (
            <div className="mb-4 p-3 bg-layer2 rounded-lg border border-border-subtle">
              <DiffView diff={result.diff} />
            </div>
          )}

          {/* Quality scores */}
          {result.quality_score && <QualityScores scores={result.quality_score} />}

          {/* Actions */}
          <div className="flex gap-2 mt-4 pt-4 border-t border-border-subtle">
            <button
              onClick={onCopy}
              className="text-xs text-text-dim hover:text-text-bright font-mono"
            >
              {isCopied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// features/chat/components/MemoryCitations.tsx
// Enterprise-style memory citations with numbered badges and expandable panel
// Like Perplexity sources, but for Kira's applied memories

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, ChevronDown, ChevronUp, Clock } from 'lucide-react'
import type { MemoryCitation } from '../types'

interface MemoryCitationsProps {
  citations: MemoryCitation[]
}

function formatDate(isoString: string): string {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return ''
  }
}

function CitationBadge({
  number,
  citation,
  isExpanded,
  onToggle,
}: {
  number: number
  citation: MemoryCitation
  isExpanded: boolean
  onToggle: () => void
}) {
  return (
    <div className="border border-border-subtle rounded-lg overflow-hidden bg-layer1/50">
      {/* Badge header — always visible */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-layer2 transition-colors group"
        aria-expanded={isExpanded}
      >
        <span className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-kira/10 text-kira text-[10px] font-mono font-bold flex-shrink-0">
          {number}
        </span>
        <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex-shrink-0">
          {citation.domain.toUpperCase()}
        </span>
        <span className="text-xs text-text-muted line-clamp-1 flex-1 text-left">
          {citation.content}
        </span>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {citation.created_at && (
            <span className="text-[10px] text-text-dim flex items-center gap-0.5">
              <Clock size={10} />
              {formatDate(citation.created_at)}
            </span>
          )}
          {isExpanded ? (
            <ChevronUp size={12} className="text-text-dim" />
          ) : (
            <ChevronDown size={12} className="text-text-dim" />
          )}
        </div>
      </button>

      {/* Expandable detail panel */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 pt-1 border-t border-border-subtle/50">
              <div className="flex items-start gap-2 mb-2">
                <Brain size={12} className="text-kira/60 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-xs text-text-bright leading-relaxed">
                    {citation.content}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-[10px] text-text-dim">
                <span>
                  Quality: {(citation.quality_score * 100).toFixed(0)}%
                </span>
                {citation.id && (
                  <span className="font-mono">
                    ID: {citation.id.slice(0, 8)}
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function MemoryCitations({ citations }: MemoryCitationsProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  if (!citations || citations.length === 0) return null

  const toggleId = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <div className="mt-4 pt-4 border-t border-border-subtle/50">
      <div className="flex items-center gap-2 mb-3">
        <Brain size={14} className="text-kira/60" />
        <span className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
          Sources from your past sessions
        </span>
        <span className="text-[10px] text-text-dim bg-layer3 px-1.5 py-0.5 rounded-full">
          {citations.length}
        </span>
      </div>

      <div className="space-y-2">
        {citations.map((citation, index) => (
          <CitationBadge
            key={citation.id || index}
            number={index + 1}
            citation={citation}
            isExpanded={expandedIds.has(citation.id)}
            onToggle={() => toggleId(citation.id)}
          />
        ))}
      </div>
    </div>
  )
}

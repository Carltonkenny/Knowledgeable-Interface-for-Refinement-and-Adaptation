'use client'

import { Brain, Star } from 'lucide-react'
import type { DomainStat } from '@/lib/api'

interface DomainNichesProps {
  domains: DomainStat[]
  isLoading: boolean
}

export default function DomainNiches({ domains, isLoading }: DomainNichesProps) {
  if (isLoading) {
    return (
      <div className="bg-layer2 rounded-xl p-5 border border-border-subtle animate-pulse h-48">
        <div className="h-6 w-32 bg-layer3 rounded-md mb-4" />
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-8 w-24 bg-layer3 rounded-full" />
          ))}
        </div>
      </div>
    )
  }

  // Visual helper to render confidence dots
  const renderConfidenceDots = (confidence: number) => {
    // 0-1 scale -> 1-5 dots
    const dots = Math.max(1, Math.ceil(confidence * 5))
    return (
      <div className="flex gap-0.5" title={`Confidence: ${(confidence * 100).toFixed(0)}%`}>
        {[1, 2, 3, 4, 5].map((level) => (
          <div 
            key={level} 
            className={`w-1.5 h-1.5 rounded-full ${
              level <= dots ? 'bg-kira shadow-[0_0_8px_rgba(var(--color-kira),0.5)]' : 'bg-layer3'
            }`}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-primary/10 text-primary">
          <Brain size={18} />
        </div>
        <div>
          <h3 className="text-base font-medium text-text-bright">Domain Niches</h3>
          <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
            Tracked by LangMem
          </p>
        </div>
      </div>

      {domains.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-6 text-text-dim border border-dashed border-border-subtle rounded-lg bg-layer1/50">
          <Star size={24} className="mb-2 opacity-30" />
          <p className="text-sm">No specialized domains detected yet.</p>
          <p className="text-xs mt-1">Chat more in specific topics to build your profile.</p>
        </div>
      ) : (
        <div className="flex flex-wrap gap-3">
          {domains.map((domain, idx) => (
            <div 
              key={idx}
              className="flex items-center gap-3 bg-layer1 px-3 py-2 rounded-lg border border-border-subtle hover:border-primary/30 transition-colors group cursor-default"
            >
              <span className="text-sm text-text-muted group-hover:text-text-bright transition-colors font-medium">
                {domain.domain}
              </span>
              <div className="h-4 w-[1px] bg-border-subtle" />
              {renderConfidenceDots(domain.confidence)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

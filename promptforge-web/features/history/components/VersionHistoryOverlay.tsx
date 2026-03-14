// features/history/components/VersionHistoryOverlay.tsx
'use client'

import { useState, useEffect } from 'react'
import { X, History as HistoryIcon, Scaling } from 'lucide-react'
import VersionHistory from './VersionHistory'
import VersionComparison from './VersionComparison'
import type { VersionData } from '@/lib/api'

interface VersionHistoryOverlayProps {
  token: string
}

export default function VersionHistoryOverlay({ token }: VersionHistoryOverlayProps) {
  const [activeVersionId, setActiveVersionId] = useState<string | null>(null)
  const [compareTargets, setCompareTargets] = useState<{ v1: number; v2: number } | null>(null)
  const [baseVersion, setBaseVersion] = useState<VersionData | null>(null)

  useEffect(() => {
    const handleOpen = (e: any) => {
      setActiveVersionId(e.detail.versionId)
      // vNumber is available if we want to pre-select or highlight
    }
    window.addEventListener('open-version-history', handleOpen)
    return () => window.removeEventListener('open-version-history', handleOpen)
  }, [])

  if (!activeVersionId) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end animate-fade-in pointer-events-none">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/40 backdrop-blur-sm pointer-events-auto"
        onClick={() => {
          setActiveVersionId(null)
          setCompareTargets(null)
          setBaseVersion(null)
        }}
      />

      {/* Panel */}
      <div className="relative w-full max-w-lg md:max-w-xl h-full bg-layer1 shadow-2xl border-l border-border-subtle animate-slide-in-right pointer-events-auto flex flex-col">
        {compareTargets ? (
          <VersionComparison
            token={token}
            versionId={activeVersionId}
            v1={compareTargets.v1}
            v2={compareTargets.v2}
            onClose={() => {
              setCompareTargets(null)
              setBaseVersion(null)
            }}
          />
        ) : (
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-border-subtle flex items-center justify-between bg-layer2/50">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-kira/10 text-kira">
                   <HistoryIcon size={18} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-text-bright">Evolution Tracker</h2>
                  <p className="text-[10px] text-text-dim uppercase tracking-wider">Prompt Lineage & Versions</p>
                </div>
              </div>
              <button 
                onClick={() => setActiveVersionId(null)}
                className="p-2 rounded-full hover:bg-layer3 text-text-dim transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-hidden">
               <VersionHistory 
                token={token} 
                versionId={activeVersionId}
                onClose={() => setActiveVersionId(null)}
                onSelectForCompare={(v) => {
                  // For now, let's compare with Version 1 or a previous version
                  // If we want a more complex multi-select, we'd add it here.
                  // Simple logic: If we have v_number, compare v_number-1 and v_number
                  const v1 = v.version_number > 1 ? v.version_number - 1 : v.version_number
                  const v2 = v.version_number
                  setCompareTargets({ v1, v2 })
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

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
  const [compareMode, setCompareMode] = useState(false)
  const [selectedVersions, setSelectedVersions] = useState<VersionData[]>([])

  useEffect(() => {
    const handleOpen = (e: CustomEvent<{ versionId: string }>) => {
      setActiveVersionId(e.detail.versionId)
      setCompareMode(false)
      setSelectedVersions([])
    }
    window.addEventListener('open-version-history', handleOpen as EventListener)
    return () => window.removeEventListener('open-version-history', handleOpen as EventListener)
  }, [])

  if (!activeVersionId) return null

  // Handle version selection in compare mode
  const handleSelectForCompare = (version: VersionData) => {
    setSelectedVersions(prev => {
      const exists = prev.find(v => v.version_number === version.version_number)
      if (exists) {
        return prev.filter(v => v.version_number !== version.version_number)
      }
      if (prev.length >= 2) {
        return [prev[1], version]
      }
      return [...prev, version]
    })
  }

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
        {/* Header with Compare Mode toggle */}
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
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setCompareMode(!compareMode)
                setSelectedVersions([])
              }}
              className={`px-2.5 py-1.5 rounded text-[10px] font-semibold uppercase tracking-wider border transition-all ${
                compareMode 
                  ? 'bg-kira/20 text-kira border-kira/30' 
                  : 'bg-layer3 text-text-dim border-border-subtle hover:border-border-strong'
              }`}
            >
              Compare {compareMode ? 'ON' : 'OFF'}
            </button>
            <button
              onClick={() => setActiveVersionId(null)}
              className="p-2 rounded-full hover:bg-layer3 text-text-dim transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Compare Selected button */}
        {selectedVersions.length === 2 && (
          <div className="p-3 border-b border-border-subtle bg-kira/5">
            <button
              onClick={() => {
                setCompareTargets({
                  v1: selectedVersions[0].version_number,
                  v2: selectedVersions[1].version_number
                })
              }}
              className="w-full py-2 bg-kira text-white rounded-lg text-sm font-medium hover:bg-kira/90 transition-colors flex items-center justify-center gap-2"
            >
              <Scaling size={16} />
              Compare Selected (v{selectedVersions[0].version_number} vs v{selectedVersions[1].version_number})
            </button>
          </div>
        )}

        {/* Content */}
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
          <div className="flex-1 overflow-hidden">
             <VersionHistory
              token={token}
              versionId={activeVersionId}
              onClose={() => setActiveVersionId(null)}
              onSelectForCompare={compareMode ? handleSelectForCompare : undefined}
              compareMode={compareMode}
              selectedVersions={selectedVersions}
            />
          </div>
        )}
      </div>
    </div>
  )
}

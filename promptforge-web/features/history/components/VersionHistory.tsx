// features/history/components/VersionHistory.tsx
'use client'

import { useState, useEffect } from 'react'
import { apiGetVersionHistory, apiRollbackVersion, type VersionData } from '@/lib/api'
import { History as HistoryIcon, RotateCcw, CheckCircle2, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface VersionHistoryProps {
  token: string
  versionId: string
  onClose: () => void
  onSelectForCompare?: (version: VersionData) => void
  compareMode?: boolean
  selectedVersions?: VersionData[]
}

export default function VersionHistory({
  token,
  versionId,
  onClose,
  onSelectForCompare,
  compareMode,
  selectedVersions
}: VersionHistoryProps) {
  const [versions, setVersions] = useState<VersionData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentVersionNumber, setCurrentVersionNumber] = useState(0)

  useEffect(() => {
    async function load() {
      try {
        const data = await apiGetVersionHistory(token, versionId)
        setVersions(data.versions.reverse()) // Show latest first
        setCurrentVersionNumber(data.current_version)
      } catch (err) {
        console.error('Failed to load version history', err)
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [token, versionId])

  const handleRollback = async (vNumber: number) => {
    if (!confirm(`Are you sure you want to rollback to Version ${vNumber}?`)) return
    
    try {
      await apiRollbackVersion(token, versionId, vNumber)
      setCurrentVersionNumber(vNumber)
      // Refresh list to update "LIVE" status
      const data = await apiGetVersionHistory(token, versionId)
      setVersions(data.versions.reverse())
    } catch (err) {
      alert('Rollback failed')
    }
  }

  return (
    <div className="flex flex-col h-full bg-layer1">
      <div className="p-4 border-b border-border-subtle flex items-center justify-between">
        <div className="flex items-center gap-2">
          <HistoryIcon className="w-4 h-4 text-kira" />
          <h3 className="font-bold text-sm">Version History</h3>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 bg-layer2 animate-pulse rounded-xl" />
            ))}
          </div>
        ) : (
          <div className="space-y-4 relative">
            {/* Timeline Line */}
            <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border-subtle" />

            {versions.map((v) => {
              const isSelected = selectedVersions?.some(sv => sv.version_number === v.version_number) || false
              const isDisabled = !isSelected && (selectedVersions?.length || 0) >= 2

              return (
                <div key={v.id} className="relative pl-10 group">
                  {/* Timeline Dot */}
                  <div className={cn(
                    "absolute left-0 top-1.5 w-8 h-8 rounded-full border-4 border-layer1 flex items-center justify-center z-10 transition-all",
                    v.is_production ? "bg-kira text-layer1" : "bg-layer2 text-text-dim border-border-subtle",
                    isSelected && "bg-kira text-layer1 ring-2 ring-kira/50"
                  )}>
                    {v.is_production ? <CheckCircle2 size={16} /> : <span className="text-[10px] font-bold">{v.version_number}</span>}
                  </div>

                  {/* Checkbox for compare mode */}
                  {compareMode && onSelectForCompare && (
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => !isDisabled && onSelectForCompare(v)}
                      disabled={isDisabled}
                      className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 rounded border-border-subtle bg-layer1 text-kira focus:ring-kira focus:ring-2 z-20 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                    />
                  )}

                  <div className={cn(
                    "p-4 rounded-xl border transition-all",
                    isSelected 
                      ? "bg-kira/10 border-kira/40 shadow-[0_0_15px_rgba(99,102,241,0.15)]"
                      : v.is_production
                        ? "bg-kira/5 border-kira/30 shadow-sm"
                        : "bg-layer2/50 border-border-subtle hover:border-border-strong"
                  )}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-text-bright">
                          Version {v.version_number}
                        </span>
                        {v.is_production && (
                          <span className="bg-kira text-white text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase tracking-wider">
                            Live
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-text-dim">
                        {new Date(v.created_at).toLocaleString()}
                      </span>
                    </div>

                    <p className="text-sm text-text-default mb-3 line-clamp-2 italic">
                      "{v.change_summary || 'No summary provided'}"
                    </p>

                    {!compareMode && onSelectForCompare && (
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => onSelectForCompare(v)}
                          className="text-[11px] text-kira hover:underline font-bold flex items-center gap-1"
                        >
                          Compare <ChevronRight size={12} />
                        </button>

                        {!v.is_production && (
                          <button
                            onClick={() => handleRollback(v.version_number)}
                            className="text-[11px] text-text-dim hover:text-text-bright flex items-center gap-1 transition-colors"
                          >
                            <RotateCcw size={12} /> Rollback
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

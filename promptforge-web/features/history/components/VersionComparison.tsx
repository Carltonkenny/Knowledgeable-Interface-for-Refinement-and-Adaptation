// features/history/components/VersionComparison.tsx
'use client'

import { useState, useEffect } from 'react'
import { apiCompareVersions, type VersionData, type DiffItem } from '@/lib/api'
import { Scaling, X, ArrowRight, Info } from 'lucide-react'
import DiffView from '@/features/chat/components/DiffView'

interface VersionComparisonProps {
  token: string
  versionId: string
  v1: number
  v2: number
  onClose: () => void
}

export default function VersionComparison({ 
  token, 
  versionId, 
  v1, 
  v2, 
  onClose 
}: VersionComparisonProps) {
  const [data, setData] = useState<{
    version_1: VersionData
    version_2: VersionData
    diff: DiffItem[]
  } | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const result = await apiCompareVersions(token, versionId, v1, v2)
        setData(result)
      } catch (err) {
        console.error('Failed to compare versions', err)
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [token, versionId, v1, v2])

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-layer1">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-kira"></div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="flex flex-col h-full bg-layer1 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border-subtle flex items-center justify-between bg-layer2/30">
        <div className="flex items-center gap-3">
          <div className="bg-kira/10 p-1.5 rounded-lg">
             <Scaling className="w-4 h-4 text-kira" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-text-bright">Side-by-Side Comparison</h3>
            <p className="text-[10px] text-text-dim">Comparing v{v1} and v{v2}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-layer3 rounded-md transition-colors">
          <X size={18} className="text-text-dim" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
        {/* Raw Comparison */}
        <div className="grid grid-cols-2 gap-6 relative">
          {/* Arrow */}
          <div className="absolute left-1/2 top-10 -translate-x-1/2 w-8 h-8 rounded-full bg-layer3 border border-border-strong flex items-center justify-center z-10 hidden md:flex shadow-xl">
             <ArrowRight size={14} className="text-kira" />
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-text-dim uppercase tracking-widest">Version {v1}</span>
            </div>
            <div className="p-4 rounded-2xl bg-layer2 border border-border-subtle text-sm text-text-default font-serif leading-relaxed min-h-[120px]">
              {data.version_1.improved_prompt}
            </div>
          </div>

          <div className="space-y-3">
             <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-text-bright uppercase tracking-widest">Version {v2}</span>
              {data.version_2.is_production && (
                <span className="bg-kira text-white text-[8px] px-1.5 py-0.5 rounded-full font-bold">LIVE</span>
              )}
            </div>
            <div className="p-4 rounded-2xl bg-layer2 border border-kira/30 text-sm text-text-bright shadow-lg shadow-kira/5 font-serif leading-relaxed min-h-[120px]">
              {data.version_2.improved_prompt}
            </div>
          </div>
        </div>

        {/* Change Summary */}
        <div className="p-4 rounded-xl bg-kira/5 border border-kira/20 flex gap-3">
          <Info className="w-4 h-4 text-kira shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-bold text-kira mb-1 uppercase tracking-wider">Evolution Note</p>
            <p className="text-sm text-text-default italic">
              "{data.version_2.change_summary || 'No summary for this change'}"
            </p>
          </div>
        </div>

        {/* Diff View */}
        <div className="space-y-4 pt-4 border-t border-border-subtle">
           <h4 className="text-[10px] font-bold text-text-dim uppercase tracking-widest">Semantic Delta</h4>
           <div className="p-5 rounded-2xl bg-layer2 border border-border-subtle shadow-inner">
             <DiffView diff={data.diff} />
           </div>
        </div>
      </div>
    </div>
  )
}

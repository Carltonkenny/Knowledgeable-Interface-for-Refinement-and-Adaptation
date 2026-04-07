'use client'
import { logger } from '@/lib/logger'

import { useState } from 'react'
import { Download, Loader2, CheckCircle2 } from 'lucide-react'
import type { ExportData } from '@/lib/api'

interface DataExportProps {
  onExport: () => Promise<ExportData | null>
  isAuthorizing: boolean
}

export default function DataExport({ onExport, isAuthorizing }: DataExportProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [exportComplete, setExportComplete] = useState(false)

  const handleExport = async () => {
    setIsExporting(true)
    setExportComplete(false)

    try {
      const data = await onExport()
      if (data) {
        // Create downloadable JSON file
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `promptforge_export_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        // Show success state briefly
        setExportComplete(true)
        setTimeout(() => setExportComplete(false), 3000)
      }
    } catch (error) {
      logger.error('Export failed:', { error: error })
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="rounded-xl border border-border-subtle overflow-hidden bg-layer1">
      <div className="p-4 bg-layer2 border-b border-border-subtle flex items-center gap-3">
        <Download size={18} className="text-primary" />
        <h3 className="font-semibold text-text-bright">Data Export</h3>
      </div>

      <div className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-text-bright mb-1">
              Download Your Data
            </h4>
            <p className="text-xs text-text-dim max-w-md">
              Get a complete JSON file containing all your prompts, chat history, 
              domain analytics, and profile data. Complies with GDPR data portability rights.
            </p>
          </div>

          <button
            id="data-export-button"
            name="export-data"
            onClick={handleExport}
            disabled={isAuthorizing || isExporting}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
              exportComplete
                ? 'bg-success/10 text-success border border-success/30'
                : 'bg-layer1 border border-border-subtle hover:border-primary/50 hover:text-primary text-text-muted'
            }`}
            aria-label="Export your data as JSON"
          >
            {exportComplete ? (
              <>
                <CheckCircle2 size={16} />
                Exported!
              </>
            ) : isExporting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Packaging...
              </>
            ) : (
              <>
                <Download size={16} />
                Export JSON
              </>
            )}
          </button>
        </div>

        {/* What's included */}
        <div className="mt-4 pt-4 border-t border-border-subtle">
          <p className="text-[10px] font-mono text-text-dim mb-2">INCLUDED IN EXPORT:</p>
          <div className="flex flex-wrap gap-2">
            <span className="px-2 py-1 bg-layer2 rounded text-[10px] text-text-dim border border-border-subtle">
              Profile Data
            </span>
            <span className="px-2 py-1 bg-layer2 rounded text-[10px] text-text-dim border border-border-subtle">
              All Prompts
            </span>
            <span className="px-2 py-1 bg-layer2 rounded text-[10px] text-text-dim border border-border-subtle">
              Chat Sessions
            </span>
            <span className="px-2 py-1 bg-layer2 rounded text-[10px] text-text-dim border border-border-subtle">
              Conversations
            </span>
            <span className="px-2 py-1 bg-layer2 rounded text-[10px] text-text-dim border border-border-subtle">
              Domain Stats
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

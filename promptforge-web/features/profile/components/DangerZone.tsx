'use client'

import { useState } from 'react'
import { AlertTriangle, Download, Trash2, Check, X, Loader2 } from 'lucide-react'
import type { ExportData } from '@/lib/api'

interface DangerZoneProps {
  onExport: () => Promise<ExportData | null>
  onDelete: () => Promise<boolean>
  isAuthorizing: boolean
}

export default function DangerZone({ onExport, onDelete, isAuthorizing }: DangerZoneProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false)
  const [deleteConfirmationText, setDeleteConfirmationText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  const handleExport = async () => {
    setIsExporting(true)
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
      }
    } finally {
      setIsExporting(false)
    }
  }

  const handleDelete = async () => {
    if (deleteConfirmationText !== 'DELETE') return
    setIsDeleting(true)
    try {
      const success = await onDelete()
      if (success) {
        // Let the parent layout handle the redirect or logout
      }
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="bg-intent/5 rounded-xl border border-intent/20 overflow-hidden">
      <div className="p-4 bg-intent/10 border-b border-intent/20 flex items-center gap-3">
        <AlertTriangle size={18} className="text-intent" />
        <h3 className="font-semibold text-intent">Danger Zone</h3>
      </div>
      
      <div className="p-5 flex flex-col gap-5">
        
        {/* Export Data */}
        <div className="flex items-center justify-between pb-5 border-b border-border-subtle">
          <div>
            <h4 className="text-sm font-medium text-text-bright mb-1">Export Data</h4>
            <p className="text-xs text-text-dim max-w-sm">
              Download a master JSON file containing all your requests, chat history, domain niches, and profile data to comply with GDPR portability rights.
            </p>
          </div>
          <button
            onClick={handleExport}
            disabled={isAuthorizing || isExporting}
            className="flex items-center gap-2 px-4 py-2 bg-layer1 border border-border-subtle hover:border-primary/50 text-text-muted hover:text-primary transition-colors rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {isExporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            {isExporting ? 'Packaging...' : 'Export JSON'}
          </button>
        </div>

        {/* Delete Account */}
        <div className="flex items-start justify-between">
          <div>
            <h4 className="text-sm font-medium text-text-bright mb-1">Delete Account</h4>
            <p className="text-xs text-text-dim max-w-sm mb-3">
              Permanently destroy your LangMem context graph, historical prompts, domain tracking, and digital identity. This action cannot be undone.
            </p>
            
            {isConfirmingDelete && (
              <div className="bg-layer1 border border-intent/30 p-3 rounded-lg flex items-center gap-3 w-fit animate-fade-in">
                <input
                  type="text"
                  placeholder="Type DELETE"
                  value={deleteConfirmationText}
                  onChange={(e) => setDeleteConfirmationText(e.target.value)}
                  className="bg-layer2 border border-border-subtle text-text-bright text-xs rounded px-2 py-1.5 focus:outline-none focus:border-intent/50 w-28 uppercase"
                  autoFocus
                />
                <button
                  onClick={handleDelete}
                  disabled={deleteConfirmationText !== 'DELETE' || isDeleting || isAuthorizing}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-intent/20 hover:bg-intent text-white transition-colors rounded text-xs font-semibold disabled:opacity-50"
                >
               {isDeleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
               Confirm
                </button>
                <button
                  onClick={() => {
                    setIsConfirmingDelete(false)
                    setDeleteConfirmationText('')
                  }}
                  disabled={isDeleting}
                  className="p-1 hover:bg-layer3 rounded text-text-dim transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>
          
          {!isConfirmingDelete && (
            <button
              onClick={() => setIsConfirmingDelete(true)}
              disabled={isAuthorizing}
              className="px-4 py-2 bg-intent/10 hover:bg-intent/20 text-intent border border-intent/20 transition-colors rounded-lg text-sm font-semibold"
            >
               Delete Everything
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

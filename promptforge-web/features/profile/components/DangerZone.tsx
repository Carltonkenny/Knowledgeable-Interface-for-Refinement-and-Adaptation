'use client'

import { useState } from 'react'
import { AlertTriangle, Trash2, Check, X, Loader2 } from 'lucide-react'

interface DangerZoneProps {
  onDelete: () => Promise<boolean>
  isAuthorizing: boolean
}

export default function DangerZone({ onDelete, isAuthorizing }: DangerZoneProps) {
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false)
  const [deleteConfirmationText, setDeleteConfirmationText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    if (deleteConfirmationText !== 'DELETE') return
    setIsDeleting(true)
    try {
      const success = await onDelete()
      if (success) {
        // Parent component handles redirect/logout
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

      <div className="p-5">
        {/* Delete Account */}
        <div className="flex items-start justify-between">
          <div>
            <h4 className="text-sm font-medium text-text-bright mb-1">
              Delete Account
            </h4>
            <p className="text-xs text-text-dim max-w-sm mb-3">
              Permanently destroy your LangMem context graph, historical prompts, 
              domain tracking, and digital identity. This action <strong className="text-intent">CANNOT be undone</strong>.
            </p>

            {/* What will be deleted */}
            <div className="mb-4 p-3 bg-layer1 border border-intent/20 rounded-lg">
              <p className="text-[10px] font-mono text-intent mb-2">WILL BE PERMANENTLY DELETED:</p>
              <div className="flex flex-wrap gap-1.5">
                <span className="px-2 py-0.5 bg-intent/10 rounded text-[10px] text-intent border border-intent/20">
                  All Prompts
                </span>
                <span className="px-2 py-0.5 bg-intent/10 rounded text-[10px] text-intent border border-intent/20">
                  Chat History
                </span>
                <span className="px-2 py-0.5 bg-intent/10 rounded text-[10px] text-intent border border-intent/20">
                  LangMem Context
                </span>
                <span className="px-2 py-0.5 bg-intent/10 rounded text-[10px] text-intent border border-intent/20">
                  Domain Stats
                </span>
                <span className="px-2 py-0.5 bg-intent/10 rounded text-[10px] text-intent border border-intent/20">
                  Profile Data
                </span>
              </div>
            </div>

            {/* Confirmation step 2: Type DELETE */}
            {isConfirmingDelete && (
              <div className="bg-layer1 border border-intent/30 p-3 rounded-lg flex flex-col gap-3 w-fit animate-fade-in">
                <div className="flex items-center gap-2">
                  <AlertTriangle size={14} className="text-intent" />
                  <span className="text-xs font-semibold text-intent">
                    Type DELETE to confirm
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Type DELETE"
                    value={deleteConfirmationText}
                    onChange={(e) => setDeleteConfirmationText(e.target.value.toUpperCase())}
                    className="bg-layer2 border border-border-subtle text-text-bright text-xs rounded px-2 py-1.5 focus:outline-none focus:border-intent/50 w-32 uppercase tracking-wider"
                    autoFocus
                  />
                  <button
                    onClick={handleDelete}
                    disabled={deleteConfirmationText !== 'DELETE' || isDeleting || isAuthorizing}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-intent hover:bg-intent/90 text-white transition-colors rounded text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isDeleting ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        Deleting...
                      </>
                    ) : (
                      <>
                        <Trash2 size={14} />
                        Confirm
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setIsConfirmingDelete(false)
                      setDeleteConfirmationText('')
                    }}
                    disabled={isDeleting}
                    className="p-1.5 hover:bg-layer3 rounded text-text-dim transition-colors"
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Step 1: Click to reveal confirmation */}
          {!isConfirmingDelete && (
            <button
              onClick={() => setIsConfirmingDelete(true)}
              disabled={isAuthorizing}
              className="px-4 py-2.5 bg-intent/10 hover:bg-intent/20 text-intent border border-intent/20 transition-colors rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Trash2 size={16} />
              Delete Everything
            </button>
          )}
        </div>

        {/* Final warning */}
        <div className="mt-4 pt-4 border-t border-intent/20">
          <p className="text-[10px] text-text-dim flex items-center gap-2">
            <AlertTriangle size={12} className="text-intent" />
            Once deleted, there is no way to recover your data. Consider exporting first.
          </p>
        </div>
      </div>
    </div>
  )
}

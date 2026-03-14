// features/chat/components/RecycleBin.tsx
'use client'

import { useEffect } from 'react'
import { X, RotateCcw, Trash2, Calendar, AlertCircle } from 'lucide-react'
import { useChatSessions } from '../hooks/useChatSessions'
import { cn } from '@/lib/utils'

interface RecycleBinProps {
  token: string
  onClose: () => void
}

export default function RecycleBin({ token, onClose }: RecycleBinProps) {
  const { 
    deletedSessions, 
    isRecycleBinLoading, 
    refreshDeletedSessions,
    restoreSession,
    permanentlyDeleteSession
  } = useChatSessions(token)

  // Pre-fetched in useChatSessions for seamless transition

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-layer-1 border border-border-subtle rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh] animate-scale-up">
        {/* Header */}
        <div className="p-5 border-b border-border-subtle flex items-center justify-between bg-layer-2/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-intent/10 text-intent">
               <Trash2 size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-text-bright">Recycle Bin</h2>
              <p className="text-xs text-text-muted">Deleted chats are kept for 30 days before permanent removal.</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-full hover:bg-layer-3 text-text-dim transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
          {isRecycleBinLoading ? (
            <div className="flex flex-col gap-3">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-16 rounded-xl bg-layer-2 animate-pulse" />
              ))}
            </div>
          ) : deletedSessions.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center text-center p-8">
              <div className="w-16 h-16 rounded-full bg-layer-2 flex items-center justify-center text-text-muted mb-4">
                <Trash2 size={32} />
              </div>
              <h3 className="text-lg font-semibold text-text-bright mb-1">Recycle Bin is Empty</h3>
              <p className="text-sm text-text-muted max-w-xs">You haven't deleted any chats recently. Good job keeping things tidy!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {deletedSessions.map((session) => (
                <div 
                  key={session.id}
                  className="flex items-center gap-4 p-4 rounded-xl border border-border-subtle bg-layer-2/30 hover:bg-layer-2 hover:border-border-strong transition-all group"
                >
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-text-bright truncate">{session.title || 'Untitled Chat'}</h4>
                    <div className="flex items-center gap-3 mt-1">
                       <div className="flex items-center gap-1 text-[11px] text-text-muted">
                        <Calendar size={12} />
                        <span>Deleted {new Date(session.deleted_at || '').toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => restoreSession(session.id)}
                      className="px-3 py-1.5 rounded-lg bg-kira/10 text-kira hover:bg-kira hover:text-white text-xs font-bold flex items-center gap-1.5 transition-all"
                    >
                      <RotateCcw size={14} />
                      Restore
                    </button>
                    <button 
                      onClick={() => {
                        // Optimistic UI in hook already handles immediate removal.
                        // Removing the blocking confirm for seamless user experience.
                        permanentlyDeleteSession(session.id)
                      }}
                      className="p-2 rounded-lg hover:bg-intent/20 text-text-muted hover:text-intent transition-all"
                      title="Permanently Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-layer-2/50 border-t border-border-subtle flex items-center gap-3">
           <AlertCircle size={16} className="text-amber-400 shrink-0" />
           <p className="text-[11px] text-text-muted">
             Kira automatically purges items in the recycle bin after 30 days of inactivity.
           </p>
        </div>
      </div>
    </div>
  )
}

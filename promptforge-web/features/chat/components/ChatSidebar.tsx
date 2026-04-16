// features/chat/components/ChatSidebar.tsx
'use client'

import { useState } from 'react'
import { Plus, MessageSquare, Trash2, ChevronLeft, ChevronRight, Pin, Star, Trash, Sparkles } from 'lucide-react'
import { useChatSessions } from '../hooks/useChatSessions'
import RecycleBin from './RecycleBin'
import { cn } from '@/lib/utils'
import { memo } from 'react'

interface SessionItemProps {
  session: any
  currentSessionId: string | undefined
  confirmDeleteId: string | null
  isCollapsed: boolean
  onSwitch: (id: string) => void
  onTogglePin: (id: string) => void
  onToggleFavorite: (id: string) => void
  onDelete: (id: string) => void
  setConfirmDeleteId: (id: string | null) => void
}

const SessionItem = memo(({ 
  session, 
  currentSessionId, 
  confirmDeleteId, 
  isCollapsed,
  onSwitch,
  onTogglePin,
  onToggleFavorite,
  onDelete,
  setConfirmDeleteId
}: SessionItemProps) => {
  const isConfirming = confirmDeleteId === session.id

  return (
    <div 
      className={cn(
        "group relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all cursor-pointer",
        currentSessionId === session.id 
          ? "bg-kira-dim text-kira border border-kira/20 font-bold" 
          : "text-text-dim hover:bg-layer-2 hover:text-text-bright"
      )}
      onClick={() => onSwitch(session.id)}
      onMouseLeave={() => isConfirming && setConfirmDeleteId(null)}
    >
      <MessageSquare size={16} className={cn(
        currentSessionId === session.id ? "text-kira" : "text-text-muted"
      )} />
      
      {!isCollapsed && (
        <>
          <span className="flex-1 truncate">
            {session.title || 'Untitled Chat'}
          </span>
          
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
             <button
              onClick={(e) => {
                e.stopPropagation()
                onTogglePin(session.id)
              }}
              className={cn(
                "p-1 rounded-md hover:bg-layer-3 transition-all",
                session.is_pinned ? "text-kira" : "text-text-muted"
              )}
              title={session.is_pinned ? "Unpin" : "Pin"}
            >
              <Pin size={13} className={session.is_pinned ? "fill-current" : ""} />
            </button>

            <button
              onClick={(e) => {
                e.stopPropagation()
                onToggleFavorite(session.id)
              }}
              className={cn(
                "p-1 rounded-md hover:bg-layer-3 transition-all",
                session.is_favorite ? "text-amber-400" : "text-text-muted"
              )}
              title={session.is_favorite ? "Remove from favorites" : "Favorite"}
            >
              <Star size={13} className={session.is_favorite ? "fill-current" : ""} />
            </button>

            <button
              onClick={(e) => {
                e.stopPropagation()
                if (isConfirming) {
                  onDelete(session.id)
                  setConfirmDeleteId(null)
                } else {
                  setConfirmDeleteId(session.id)
                }
              }}
              className={cn(
                "p-1 rounded-md transition-all",
                isConfirming
                  ? "bg-intent text-white shadow-lg shadow-intent/20 scale-110"
                  : "hover:bg-layer-3 text-text-muted hover:text-intent"
              )}
              title={isConfirming ? "Click again to confirm delete" : "Delete"}
            >
              <Trash2 size={13} className={isConfirming ? "animate-pulse" : ""} />
            </button>

            {isConfirming && (
              <span className="text-[10px] font-bold text-intent animate-pulse ml-1">
                Confirm?
              </span>
            )}
          </div>
        </>
      )}
    </div>
  )
})

SessionItem.displayName = 'SessionItem'

interface ChatSidebarProps {
  token: string
  mode?: 'chat' | 'history'
}

export default function ChatSidebar({ token, mode = 'chat' }: ChatSidebarProps) {
  const {
    sessions,
    isLoading,
    currentSessionId,
    createNewChat,
    isCreating,
    deleteSession,
    switchSession,
    togglePin,
    toggleFavorite
  } = useChatSessions(token)

  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('pf_sidebar_collapsed') === 'true'
    }
    return false
  })
  const [showRecycleBin, setShowRecycleBin] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

  const toggleCollapse = (value: boolean) => {
    setIsCollapsed(value)
    if (typeof window !== 'undefined') {
      localStorage.setItem('pf_sidebar_collapsed', String(value))
    }
  }

  const pinnedSessions = sessions.filter(s => s.is_pinned)
  const recentSessions = sessions.filter(s => !s.is_pinned)

  const renderSessionItem = (session: typeof sessions[0]) => (
    <SessionItem
      key={session.id}
      session={session}
      currentSessionId={currentSessionId}
      confirmDeleteId={confirmDeleteId}
      isCollapsed={isCollapsed}
      onSwitch={switchSession}
      onTogglePin={togglePin}
      onToggleFavorite={toggleFavorite}
      onDelete={deleteSession}
      setConfirmDeleteId={setConfirmDeleteId}
    />
  )

  return (
    <aside 
      className={cn(
        "h-full border-r border-border-subtle bg-layer-1 transition-all duration-300 flex flex-col relative",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Collapse Toggle */}
      <button 
        onClick={() => toggleCollapse(!isCollapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full border border-border-strong bg-layer-2 flex items-center justify-center text-text-dim hover:text-text-bright z-20 shadow-sm"
      >
        {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {/* Header Label */}
      <div className={cn("p-4 pb-2", isCollapsed && "hidden")}>
         <h2 className="text-[10px] font-bold text-text-dim uppercase tracking-[0.2em]">
            {mode === 'history' ? 'Search History' : 'Chat Sessions'}
         </h2>
      </div>

      {/* New Action Button */}
      <div className={cn("p-4 pt-2", isCollapsed && "flex justify-center")}>
        <button
          onClick={() => createNewChat()}
          disabled={isCreating}
          className={cn(
            "flex items-center gap-3 transition-all group",
            isCollapsed 
              ? "w-10 h-10 rounded-full border-2 border-kira bg-kira/10 justify-center shadow-[0_0_15px_rgba(var(--color-kira),0.3)] hover:scale-110 active:scale-95" 
              : "w-full px-3 py-2.5 rounded-xl border border-kira/20 bg-kira/5 text-text-bright hover:bg-kira/10 hover:border-kira/40 shadow-sm shadow-kira/5"
          )}
          title={mode === 'history' ? "New Search" : "New Chat"}
        >
          {isCollapsed ? (
            mode === 'history' ? <Sparkles size={18} className="text-kira" /> : <Plus size={20} className="text-kira" />
          ) : (
            <>
              <div className="p-1.5 rounded-lg bg-layer2 border border-border group-hover:border-kira/30 shrink-0">
                {mode === 'history' ? <Sparkles size={16} className="text-kira" /> : <Plus size={16} className="text-kira transition-transform group-hover:rotate-90" />}
              </div>
              <span className="font-semibold text-sm">{mode === 'history' ? 'Palace Search' : 'New Chat'}</span>
            </>
          )}
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-6 custom-scrollbar">
        {isLoading && !sessions.length ? (
          <div className="flex flex-col gap-2 p-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-10 rounded-lg bg-layer-2 animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            {/* Pinned Section */}
            {pinnedSessions.length > 0 && !isCollapsed && (
              <div className="space-y-1">
                <h3 className="px-3 text-[10px] font-bold text-text-muted uppercase tracking-wider mb-2">Pinned</h3>
                {pinnedSessions.map(renderSessionItem)}
              </div>
            )}
            
            {/* Recent Section */}
            <div className="space-y-1">
              {!isCollapsed && (
                 <h3 className="px-3 text-[10px] font-bold text-text-muted uppercase tracking-wider mb-2">
                   {mode === 'history' ? 'Older Sessions' : 'Recent Chats'}
                 </h3>
              )}
              {recentSessions.map(renderSessionItem)}
            </div>
          </>
        )}
      </div>

      {/* Footer Area */}
      <div className="mt-auto flex flex-col border-t border-border-subtle">
        {/* Recycle Bin Button */}
        <button
          onClick={() => setShowRecycleBin(true)}
          className={cn(
            "flex items-center gap-3 px-5 py-3 text-text-dim hover:bg-layer-2 hover:text-text-bright transition-colors",
            isCollapsed && "justify-center px-0"
          )}
          title="Recycle Bin"
        >
          <Trash size={16} />
          {!isCollapsed && <span className="text-sm font-medium">Recycle Bin</span>}
        </button>

        {/* User Profile */}
        <div className="p-4 border-t border-border-subtle">
          <div className={cn(
            "flex items-center gap-3",
            isCollapsed && "justify-center px-0"
          )}>
            <div className="w-8 h-8 rounded-lg border border-kira/30 bg-kira/10 flex items-center justify-center text-kira font-bold font-mono text-sm shrink-0 shadow-sm">
              K
            </div>
            {!isCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="text-sm font-semibold text-text-bright truncate">PromptForge</span>
                <span className="text-xs text-text-muted truncate">v2.0</span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Recycle Bin Modal */}
      {showRecycleBin && (
        <RecycleBin 
          token={token} 
          onClose={() => setShowRecycleBin(false)} 
        />
      )}
    </aside>
  )
}

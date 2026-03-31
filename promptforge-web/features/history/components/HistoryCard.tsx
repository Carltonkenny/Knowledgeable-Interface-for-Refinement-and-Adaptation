import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Copy, Play, Check, Clock, Edit2, Star } from 'lucide-react'
import type { HistoryItem } from '@/lib/api'

interface HistoryCardProps {
  item: HistoryItem
  onUseAgain: (prompt: string) => void
  isSelected?: boolean
  onToggleSelect?: (id: string) => void
}

export default function HistoryCard({ item, onUseAgain, isSelected, onToggleSelect }: HistoryCardProps) {
  const router = useRouter()
  const [copied, setCopied] = useState(false)

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(item.improved_prompt)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation()
    
    // We emit a global event so the parent list can optimistically update state without deeply coupled props
    const newStatus = !item.is_favorite
    window.dispatchEvent(new CustomEvent('toggle-favorite', {
      detail: { id: item.id, is_favorite: newStatus }
    }))
  }

  const handleViewSession = (e: React.MouseEvent) => {
    e.stopPropagation()
    // Navigate to the chat session this history item belongs to
    router.push(`/app?session=${item.session_id}`)
  }

  const handleRename = (e: React.MouseEvent) => {
    e.stopPropagation()
    const newTitle = prompt('Rename this session:', item.session_id)
    if (newTitle) {
      window.dispatchEvent(new CustomEvent('rename-session', { 
        detail: { sessionId: item.session_id, title: newTitle } 
      }))
    }
  }

  return (
    <div className={`group relative p-6 rounded-3xl border transition-all duration-300 ${
      isSelected 
      ? 'border-kira bg-kira/5 shadow-lg shadow-kira/10 ring-1 ring-kira/20' 
      : 'border-border/50 bg-layer2/50 hover:border-kira/30 hover:bg-layer2 hover:shadow-xl'
    }`}>
      {/* Selection Checkbox */}
      <div 
        onClick={(e) => {
          e.stopPropagation()
          onToggleSelect && onToggleSelect(item.id)
        }}
        className={`absolute -left-2 -top-2 w-6 h-6 rounded-full border-2 flex items-center justify-center cursor-pointer transition-all z-20 ${
          isSelected 
          ? 'bg-kira border-kira text-white scale-110' 
          : 'bg-layer3 border-border text-transparent group-hover:border-kira/50'
        }`}
      >
        <Check className="w-3 h-3" strokeWidth={3} />
      </div>

      {/* Header Row */}
      <div className="flex justify-between items-start">
        <div className="flex flex-col flex-1 min-w-0 pr-4">
          <p className="text-text-dim text-[11px] font-mono uppercase tracking-wider line-clamp-1 opacity-60">
            Initial Prompt: {item.raw_prompt}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] font-mono text-text-dim/50">
              {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
            </span>
            <span className="w-1 h-1 rounded-full bg-border/30" />
            <span className="text-[10px] font-mono text-text-dim bg-layer3 px-2 py-0.5 rounded-full border border-border">
              {item.domain || 'general'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button 
            onClick={handleToggleFavorite}
            className={`p-2 rounded-xl transition-all border active:scale-95 ${
              item.is_favorite 
                ? 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30 shadow-[0_0_10px_rgba(250,204,21,0.2)]' 
                : 'text-text-dim hover:text-yellow-400/70 bg-layer3/50 hover:bg-yellow-400/5 hover:border-yellow-400/20 border-border/50'
            }`}
            title={item.is_favorite ? "Remove from Favorites" : "Add to Favorites"}
          >
            <Star size={14} className={item.is_favorite ? "fill-yellow-400" : ""} />
          </button>
          <button 
            onClick={handleRename}
            className="p-2 text-text-dim hover:text-kira bg-layer3/50 hover:bg-kira/10 rounded-xl transition-all border border-border/50 hover:border-kira/20 active:scale-95"
            title="Rename Session"
          >
            <Edit2 size={14} />
          </button>
        </div>
      </div>

      {/* Improved prompt */}
      <h4 className="text-text font-medium text-sm my-4 leading-relaxed line-clamp-3 group-hover:line-clamp-none transition-all duration-500">
        {item.improved_prompt}
      </h4>

      {/* Footer / Meta Row */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-6 pt-4 border-t border-border/10">
        <div className="flex gap-4 flex-1">
          <div className="flex flex-col gap-1.5 flex-1">
            <div className="flex items-center justify-between text-[8px] font-bold text-text-dim/40 uppercase tracking-widest font-mono">
              <span>Specificity</span>
              <span>{Math.round((item.quality_score?.specificity ?? 0) * 20)}%</span>
            </div>
            <div className="h-1 w-full bg-layer3 rounded-full overflow-hidden">
              <div 
                className="h-full bg-kira transition-all duration-1000" 
                style={{ width: `${(item.quality_score?.specificity ?? 0) * 20}%` }}
              />
            </div>
          </div>
          
          <div className="flex flex-col gap-1.5 flex-1">
            <div className="flex items-center justify-between text-[8px] font-bold text-text-dim/40 uppercase tracking-widest font-mono">
              <span>Clarity</span>
              <span>{item.quality_score?.clarity ? Math.round(item.quality_score.clarity * 20) : 45}%</span>
            </div>
            <div className="h-1 w-full bg-layer3 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all duration-1000" 
                style={{ width: `${item.quality_score?.clarity ? item.quality_score.clarity * 20 : 45}%` }}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2">
          <button 
            onClick={handleViewSession}
            className="p-2 text-text-dim hover:text-text rounded-lg hover:bg-layer3 transition-all active:scale-95" 
            title="Access Session Transcript"
          >
            <Clock size={16} />
          </button>
          <button 
            onClick={handleCopy}
            className={`p-2 rounded-lg transition-all active:scale-95 ${copied ? 'text-green-400 bg-green-500/10' : 'text-text-dim hover:text-text hover:bg-layer3'}`}
            title="Copy Prompt"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
          </button>
          <button 
            onClick={() => onUseAgain(item.raw_prompt)}
            className="flex items-center gap-2 bg-text text-bg px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-kira hover:text-white transition-all shadow-sm active:scale-95"
          >
            <Play size={12} fill="currentColor" />
            Iterate
          </button>
        </div>
      </div>
    </div>
  )
}

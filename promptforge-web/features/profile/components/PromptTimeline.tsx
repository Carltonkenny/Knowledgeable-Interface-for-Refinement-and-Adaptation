'use client'

import { useState, useEffect } from 'react'
import { FileText, Star, Clock, Target } from 'lucide-react'
import { apiToggleFavorite } from '@/lib/api'

interface Prompt {
  id: string
  raw_prompt: string
  improved_prompt: string
  domain: string
  quality_score: number
  created_at: string
  is_favorite?: boolean
}

interface PromptTimelineProps {
  token: string
}

export default function PromptTimeline({ token }: PromptTimelineProps) {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadPrompts()
  }, [token])

  const loadPrompts = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user/activity?limit=10`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to load activity')
      }

      setPrompts(data.prompts || [])
    } catch (error: any) {
      console.error('Failed to load prompts:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleFavorite = async (id: string, currentStatus: boolean) => {
    const newStatus = !currentStatus
    // Optimistic visual update
    setPrompts(prev => prev.map(p => p.id === id ? { ...p, is_favorite: newStatus } : p))
    try {
      await apiToggleFavorite(token, id, newStatus)
    } catch (e) {
      console.error('Failed to toggle favorite:', e)
      // Revert on failure
      setPrompts(prev => prev.map(p => p.id === id ? { ...p, is_favorite: currentStatus } : p))
    }
  }

  const formatTimeAgo = (isoString: string) => {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  const domainColors: Record<string, string> = {
    python: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    javascript: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    business: 'bg-green-500/10 text-green-400 border-green-500/30',
    creative: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    technical: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    general: 'bg-layer3 text-text-dim border-border-subtle'
  }

  if (isLoading) {
    return (
      <div className="bg-layer2 rounded-2xl border border-border-subtle p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-kira/10 text-kira">
            <FileText size={18} />
          </div>
          <h3 className="text-sm font-semibold text-text-bright">Recent Prompts</h3>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-layer3 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-layer2 rounded-2xl border border-border-subtle p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-kira/10 text-kira">
            <FileText size={18} />
          </div>
          <h3 className="text-sm font-semibold text-text-bright">Recent Prompts</h3>
        </div>
        <span className="text-xs text-text-dim">{prompts.length} prompts</span>
      </div>

      <div className="space-y-3">
        {prompts.length === 0 ? (
          <div className="text-center py-8">
            <FileText size={32} className="mx-auto mb-3 text-text-dim opacity-30" />
            <p className="text-sm text-text-dim">No prompts yet</p>
            <p className="text-xs text-text-dim mt-1">Start forging to see your activity</p>
          </div>
        ) : (
          prompts.map((prompt, index) => (
            <div
              key={prompt.id}
              className="group p-4 rounded-lg bg-layer1 border border-border-subtle hover:border-kira/30 transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <button 
                    onClick={(e) => { e.stopPropagation(); handleToggleFavorite(prompt.id, prompt.is_favorite || false); }}
                    className={`focus:outline-none transition-transform hover:scale-125 ${prompt.is_favorite ? 'text-yellow-400 drop-shadow-[0_0_8px_rgba(250,204,21,0.6)]' : 'text-text-dim hover:text-yellow-400/50'}`}
                    title={prompt.is_favorite ? "Remove from Favorites" : "Add to Favorites"}
                  >
                    <Star size={14} className={prompt.is_favorite ? "fill-yellow-400" : ""} />
                  </button>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${
                    domainColors[prompt.domain.toLowerCase()] || domainColors.general
                  }`}>
                    {prompt.domain}
                  </span>
                  <span className="flex items-center gap-1 text-[10px] text-text-dim font-mono">
                    <Clock size={10} />
                    {formatTimeAgo(prompt.created_at).toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[10px] font-mono text-text-dim bg-layer2 px-2 py-0.5 rounded border border-border-default/50" title="LangSmith Quality Score">
                  <Target size={10} className={prompt.quality_score >= 4 ? 'text-kira' : 'text-text-dim'} />
                  <span>[Q: {prompt.quality_score.toFixed(1)}]</span>
                </div>
              </div>
              <p className="text-xs text-text-bright line-clamp-2 mb-1">
                {prompt.raw_prompt}
              </p>
              {prompt.improved_prompt && (
                <p className="text-[10px] text-text-dim line-clamp-1">
                  → {prompt.improved_prompt}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

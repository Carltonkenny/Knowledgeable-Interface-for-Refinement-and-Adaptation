'use client'

import { useState, useEffect } from 'react'
import { FileText, Star, Clock, Target, Edit2, Check, X } from 'lucide-react'
import { apiToggleFavorite, apiUpdatePromptDomain, apiGetActivity, type QualityScore } from '@/lib/api'
import { logger } from '@/lib/logger'
import { motion, AnimatePresence } from 'framer-motion'

interface Prompt {
  id: string
  raw_prompt: string
  improved_prompt: string
  domain: string
  sub_domain?: string | null
  quality_score: QualityScore | null
  created_at: string
  is_favorite?: boolean
}

interface PromptTimelineProps {
  token: string
}

export default function PromptTimeline({ token }: PromptTimelineProps) {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [editingId, setEditingId] = useState<string | null>(null)

  useEffect(() => {
    loadPrompts()
  }, [token])

  const loadPrompts = async () => {
    try {
      const data = await apiGetActivity(token, 10)
      setPrompts(data.prompts || [])
    } catch (error) {
      logger.error('Failed to load prompts', { error })
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleFavorite = async (id: string, currentStatus: boolean) => {
    const newStatus = !currentStatus
    setPrompts(prev => prev.map(p => p.id === id ? { ...p, is_favorite: newStatus } : p))
    try {
      await apiToggleFavorite(token, id, newStatus)
    } catch (e) {
      logger.error('Failed to toggle favorite', { error: e, id })
      setPrompts(prev => prev.map(p => p.id === id ? { ...p, is_favorite: currentStatus } : p))
    }
  }

  const handleUpdateDomain = async (id: string, newDomain: string) => {
    const originalPrompt = prompts.find(p => p.id === id)
    if (!originalPrompt) return

    setPrompts(prev => prev.map(p => p.id === id ? { ...p, domain: newDomain } : p))
    setEditingId(null)

    try {
      await apiUpdatePromptDomain(token, id, newDomain)
    } catch (e) {
      logger.error('Failed to update domain', { error: e, id })
      setPrompts(prev => prev.map(p => p.id === id ? { ...p, domain: originalPrompt.domain } : p))
    }
  }

  const disciplines = [
    'Technical Architecture', 'Full-Stack Development', 'Data Intelligence',
    'Creative Synthesis', 'Strategic Business', 'Instructional Design',
    'Persona Engineering', 'Security & Research', 'Legal & Compliance',
    'Project Management', 'Scientific Computing', 'Meta-Prompting'
  ]

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
    'technical architecture': 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    'full-stack development': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    'data intelligence': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    'creative synthesis': 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    'strategic business': 'bg-green-500/10 text-green-400 border-green-500/30',
    'instructional design': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    'persona engineering': 'bg-pink-500/10 text-pink-400 border-pink-500/30',
    'security & research': 'bg-red-500/10 text-red-400 border-red-500/30',
    'legal & compliance': 'bg-slate-500/10 text-slate-400 border-slate-500/30',
    'project management': 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    'scientific computing': 'bg-teal-500/10 text-teal-400 border-teal-500/30',
    'meta-prompting': 'bg-kira/10 text-kira border-kira/30',
    'general': 'bg-layer3 text-text-dim border-border-subtle'
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
                  <div className="relative">
                      <span 
                        onClick={(e) => { e.stopPropagation(); setEditingId(editingId === prompt.id ? null : prompt.id); }}
                        className={`group/tag flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-full font-medium border cursor-pointer hover:border-kira/60 transition-all uppercase tracking-tight ${
                          domainColors[prompt.domain.toLowerCase()] || domainColors.general
                        }`}
                      >
                        <span className="opacity-90">{prompt.domain}</span>
                        {prompt.sub_domain && (
                          <>
                            <span className="opacity-30 mx-0.5 text-[8px]">›</span>
                            <span className="font-bold tracking-normal opacity-80">{prompt.sub_domain}</span>
                          </>
                        )}
                        <Edit2 size={8} className="opacity-0 group-hover/tag:opacity-100 transition-opacity ml-1" />
                      </span>

                    <AnimatePresence>
                      {editingId === prompt.id && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.95, y: -10 }}
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.95, y: -10 }}
                          className="absolute z-20 top-full left-0 mt-2 p-2 bg-layer2 border border-kira/30 rounded-xl shadow-2xl min-w-[220px]"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="text-[10px] uppercase tracking-wider font-bold text-text-dim px-2 mb-2 flex justify-between">
                            Change Discipline
                            <X size={10} className="cursor-pointer hover:text-kira" onClick={() => setEditingId(null)} />
                          </div>
                          <div className="grid grid-cols-1 gap-1 max-h-[250px] overflow-y-auto no-scrollbar">
                            {disciplines.map(d => (
                              <button
                                key={d}
                                onClick={() => handleUpdateDomain(prompt.id, d)}
                                className={`text-left px-3 py-1.5 rounded-lg text-[10px] transition-colors ${
                                  prompt.domain === d ? 'bg-kira/20 text-kira' : 'hover:bg-layer3 text-text-bright'
                                }`}
                              >
                                {d}
                              </button>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  <span className="flex items-center gap-1 text-[10px] text-text-dim font-mono">
                    <Clock size={10} />
                    {formatTimeAgo(prompt.created_at).toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[10px] font-mono text-text-dim bg-layer2 px-2 py-0.5 rounded border border-border-default/50" title="LangSmith Quality Score">
                  <Target size={10} className={prompt.quality_score ? ((prompt.quality_score.specificity + prompt.quality_score.clarity + prompt.quality_score.actionability) / 3) >= 4 ? 'text-kira' : 'text-text-dim' : 'text-text-dim'} />
                  <span>[Q: {prompt.quality_score ? ((prompt.quality_score.specificity + prompt.quality_score.clarity + prompt.quality_score.actionability) / 3).toFixed(1) : '—'}]</span>
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

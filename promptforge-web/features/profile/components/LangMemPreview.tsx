import { useState } from 'react'
import { Database, Lock, Clock, ChevronDown, ChevronRight, Trash2 } from 'lucide-react'
import type { MemoryPreview } from '@/lib/api'
import Boneyard from '@/components/ui/Boneyard'
import { toast } from 'sonner'

interface LangMemPreviewProps {
  memories: MemoryPreview[]
  isLoading: boolean
  onForget?: (id: string) => Promise<boolean>
}

// Category configuration for professional color coding
const categoryConfig: Record<string, { label: string; color: string; bg: string; border: string; icon: string }> = {
  identity: { label: 'Identity', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', icon: '👤' },
  preference: { label: 'Preference', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30', icon: '✨' },
  project: { label: 'Project Context', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30', icon: '🏭' },
  constraint: { label: 'Constraints', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30', icon: '⛓️' },
  feedback: { label: 'Feedback', color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30', icon: '🎯' },
  other: { label: 'Knowledge', color: 'text-text-muted', bg: 'bg-layer3', border: 'border-border-subtle', icon: '🧠' },
}

interface MemoryGroupProps {
  category: string
  memories: MemoryPreview[]
  isExpanded: boolean
  onToggle: () => void
  onForget?: (id: string) => Promise<boolean>
}

function MemoryGroup({ category, memories, isExpanded, onToggle, onForget }: MemoryGroupProps) {
  const config = categoryConfig[category] || categoryConfig.other
  const count = memories.length
  const [isDeleting, setIsDeleting] = useState<string | null>(null)

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!onForget) return
    
    setIsDeleting(id)
    try {
      await onForget(id)
      toast.success('Memory forgotten')
    } catch (err) {
      toast.error('Failed to forget memory')
    } finally {
      setIsDeleting(null)
    }
  }

  return (
    <div className="border border-border-subtle rounded-lg overflow-hidden bg-layer1/50">
      {/* Collapsible Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-layer2 transition-colors group"
        aria-expanded={isExpanded}
        aria-controls={`memory-group-${category}`}
      >
        <div className="flex items-center gap-2.5">
          <span className="text-base">
            {config.icon}
          </span>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${config.bg} ${config.color} border ${config.border}`}>
              {config.label.toUpperCase()}
            </span>
            <span className="text-[10px] text-text-dim bg-layer3 px-1.5 py-0.5 rounded-full">
              {count} {count === 1 ? 'fact' : 'facts'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-text-dim group-hover:text-text-bright transition-colors">
            {isExpanded ? 'Collapse' : 'Expand'}
          </span>
          {isExpanded ? (
            <ChevronDown size={14} className="text-text-dim" />
          ) : (
            <ChevronRight size={14} className="text-text-dim" />
          )}
        </div>
      </button>

      {/* Expandable Content */}
      {isExpanded && (
        <div id={`memory-group-${category}`} className="px-3 pb-3 space-y-2 animate-in slide-in-from-top-2 duration-200">
          {memories.map((memory) => (
            <div
              key={memory.id}
              className={`bg-layer1 rounded-lg p-3 border border-border-subtle group/card hover:border-intent/30 transition-all ${isDeleting === memory.id ? 'opacity-50 grayscale scale-[0.98]' : ''}`}
              title={memory.content}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${config.bg} ${config.color}`}>
                  {category.toUpperCase()}
                </span>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 text-[10px] text-text-dim">
                    <Clock size={10} />
                    <span>Active</span>
                  </div>
                  {onForget && (
                    <button
                      onClick={(e) => handleDelete(e, memory.id)}
                      className="p-1 rounded hover:bg-rose-500/10 text-text-dim hover:text-rose-400 transition-colors opacity-0 group-hover/card:opacity-100"
                      title="Forget this memory"
                      disabled={isDeleting === memory.id}
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              </div>
              <p className="text-sm text-text-muted group-hover/card:text-text-bright transition-colors line-clamp-3">
                {memory.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function LangMemPreview({ memories, isLoading, onForget }: LangMemPreviewProps) {
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})

  // Group memories by category
  const groupedMemories = memories.reduce((acc, memory) => {
    const category = memory.category || 'other'
    if (!acc[category]) acc[category] = []
    acc[category].push(memory)
    return acc
  }, {} as Record<string, MemoryPreview[]>)

  const handleToggle = (category: string) => {
    setExpandedGroups(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  if (isLoading) {
    return (
      <div className="bg-layer2 rounded-xl p-5 border border-border-subtle h-64">
        <Boneyard variant="card" count={3} height="h-full" />
      </div>
    )
  }

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle flex flex-col h-full min-h-[400px]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-intent/10 text-intent">
            <Database size={18} />
          </div>
          <div>
            <h3 className="text-base font-medium text-text-bright">Memory Palace</h3>
            <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
              Kira's Atomic Identity Store
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-layer3/50 border border-border-subtle">
          <Lock size={10} className="text-text-muted" />
          <span className="text-[10px] font-mono text-text-muted uppercase">Encrypted</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-3">
        {memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-text-dim border border-dashed border-border-subtle rounded-lg bg-layer1/50 h-full min-h-[300px]">
            <Database size={32} className="mb-4 opacity-20 text-intent" />
            <h4 className="text-sm font-semibold text-text-bright mb-2">Kira is listening</h4>
            <p className="text-xs text-center max-w-[240px] mb-6 leading-relaxed">
              Start a conversation to help Kira learn your workflow. High-confidence facts are extracted instantly from Turn 1.
            </p>
            <div className="w-full max-w-[200px] space-y-2 bg-layer2/50 p-3 rounded-lg border border-border-subtle">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500/50" />
                <span className="text-[10px] italic">"I am a Lead Architect"</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-500/50" />
                <span className="text-[10px] italic">"I prefer functional patterns"</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500/50" />
                <span className="text-[10px] italic">"Stack: Next.js + FastAPI"</span>
              </div>
            </div>
          </div>
        ) : (
          // Render grouped memories
          Object.entries(groupedMemories).map(([category, categoryMemories]) => (
            <MemoryGroup
              key={category}
              category={category}
              memories={categoryMemories}
              isExpanded={expandedGroups[category] ?? true}
              onToggle={() => handleToggle(category)}
              onForget={onForget}
            />
          ))
        )}
      </div>
    </div>
  )
}

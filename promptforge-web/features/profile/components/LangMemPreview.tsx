'use client'

import { useState } from 'react'
import { Database, Lock, Clock, ChevronDown, ChevronRight } from 'lucide-react'
import type { MemoryPreview } from '@/lib/api'

interface LangMemPreviewProps {
  memories: MemoryPreview[]
  isLoading: boolean
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
}

function MemoryGroup({ category, memories, isExpanded, onToggle }: MemoryGroupProps) {
  const config = categoryConfig[category] || categoryConfig.other
  const count = memories.length

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
              {count} {count === 1 ? 'rule' : 'rules'}
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
              className="bg-layer1 rounded-lg p-3 border border-border-subtle group hover:border-intent/30 transition-colors"
              title={memory.content}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${config.bg} ${config.color}`}>
                  {category.toUpperCase()}
                </span>
                <div className="flex items-center gap-1 text-[10px] text-text-dim">
                  <Clock size={10} />
                  <span>Active</span>
                </div>
              </div>
              <p className="text-sm text-text-muted group-hover:text-text-bright transition-colors line-clamp-2">
                {memory.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function LangMemPreview({ memories, isLoading }: LangMemPreviewProps) {
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})

  // Group memories by category
  const groupedMemories = memories.reduce((acc, memory) => {
    const category = memory.category || 'other'
    if (!acc[category]) acc[category] = []
    acc[category].push(memory)
    return acc
  }, {} as Record<string, MemoryPreview[]>)

  // Initialize all groups as expanded by default
  const allCategories = Object.keys(groupedMemories)
  const defaultExpanded = allCategories.reduce((acc, cat) => ({ ...acc, [cat]: true }), {})

  const handleToggle = (category: string) => {
    setExpandedGroups(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  const currentExpanded = expandedGroups

  if (isLoading) {
    return (
      <div className="bg-layer2 rounded-xl p-5 border border-border-subtle animate-pulse h-64">
        <div className="h-6 w-48 bg-layer3 rounded-md mb-6" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-12 w-full bg-layer3 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-intent/10 text-intent">
            <Database size={18} />
          </div>
          <div>
            <h3 className="text-base font-medium text-text-bright">Core Memories</h3>
            <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
              Active Memory Rules
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-layer3/50 border border-border-subtle">
          <Lock size={10} className="text-text-muted" />
          <span className="text-[10px] font-mono text-text-muted">RLS SECURED</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-3">
        {memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-text-dim border border-dashed border-border-subtle rounded-lg bg-layer1/50 h-full">
            <Database size={24} className="mb-2 opacity-30" />
            <h4 className="text-sm font-semibold text-text-bright mb-2">No Memories Yet</h4>
            <p className="text-xs text-center max-w-[220px] mb-3">
              Kira automatically extracts and stores your preferences as you forge prompts.
            </p>
            <div className="text-[10px] text-text-dim space-y-1">
              <p>✨ Extraction occurs every 5 turns.</p>
              <p>• "Use direct, professional tone"</p>
              <p>• "Format as JSON with schema"</p>
              <p>• "Focus on Python best practices"</p>
            </div>
          </div>
        ) : (
          // Render grouped memories
          Object.entries(groupedMemories).map(([category, categoryMemories]) => (
            <MemoryGroup
              key={category}
              category={category}
              memories={categoryMemories}
              isExpanded={currentExpanded[category] ?? true}
              onToggle={() => handleToggle(category)}
            />
          ))
        )}
      </div>
    </div>
  )
}

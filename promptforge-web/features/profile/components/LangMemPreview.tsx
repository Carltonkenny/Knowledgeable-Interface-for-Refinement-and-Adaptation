'use client'

import { Database, Lock, Clock } from 'lucide-react'
import type { MemoryPreview } from '@/lib/api'

interface LangMemPreviewProps {
  memories: MemoryPreview[]
  isLoading: boolean
}

export default function LangMemPreview({ memories, isLoading }: LangMemPreviewProps) {
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
              Persisted Context Rules
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-layer3/50 border border-border-subtle">
          <Lock size={10} className="text-text-muted" />
          <span className="text-[10px] font-mono text-text-muted">RLS SECURED</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-text-dim border border-dashed border-border-subtle rounded-lg bg-layer1/50 h-full">
            <Database size={24} className="mb-2 opacity-30" />
            <p className="text-sm">Memory core is currently empty.</p>
            <p className="text-xs mt-1 text-center max-w-[200px]">
              Kira will automatically extract styling rules as you improve more prompts.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {memories.map((memory) => (
              <div 
                key={memory.id} 
                className="bg-layer1 rounded-lg p-3 border border-border-subtle group hover:border-intent/30 transition-colors"
                title={memory.content}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono font-semibold text-intent bg-intent/10 px-1.5 py-0.5 rounded">
                    {memory.category.toUpperCase()}
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
    </div>
  )
}

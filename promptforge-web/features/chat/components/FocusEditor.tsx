// features/chat/components/FocusEditor.tsx
// High-fidelity prompt engineering modal for distraction-free crafting
// Applied: Premium hardware aesthetics, liquid glass transitions

'use client'

import { useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Command } from 'lucide-react'

interface FocusEditorProps {
  isOpen: boolean
  onClose: () => void
  value: string
  onChange: (val: string) => void
  onSend: () => void
  placeholder?: string
}

export default function FocusEditor({
  isOpen,
  onClose,
  value,
  onChange,
  onSend,
  placeholder = 'Architect your prompt here...'
}: FocusEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-focus on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => textareaRef.current?.focus(), 100)
    }
  }, [isOpen])

  // Statistics
  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0
  const charCount = value.length

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      onSend()
    }
    if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-8">
          {/* Backdrop blur */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-xl"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30, ease: [0.23, 1, 0.32, 1] }}
            className="relative w-full max-w-5xl h-full max-h-[85vh] flex flex-col bg-[#0a0a0c] border border-white/10 rounded-[32px] overflow-hidden shadow-[0_32px_64px_-12px_rgba(0,0,0,0.8)]"
            onKeyDown={handleKeyDown}
          >
            {/* Header / Toolbar */}
            <div className="flex items-center justify-between px-8 py-6 border-b border-white/5 bg-gradient-to-r from-white/[0.02] to-transparent">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-[var(--kira-primary)] animate-pulse" />
                <h2 className="text-sm font-semibold uppercase tracking-widest text-white/90">Focus Editor</h2>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="hidden sm:flex items-center gap-6 mr-6 border-r border-white/10 pr-6">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-white/30 uppercase tracking-tighter">Words</span>
                    <span className="text-xs font-mono text-white/70">{wordCount}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] text-white/30 uppercase tracking-tighter">Characters</span>
                    <span className="text-xs font-mono text-white/70">{charCount}</span>
                  </div>
                </div>
                
                <button
                  onClick={onClose}
                  className="p-2 text-white/40 hover:text-white/90 hover:bg-white/5 rounded-full transition-all duration-300"
                  aria-label="Close"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Editor Textarea */}
            <div className="flex-1 relative p-8 bg-[#08080a] shadow-[inset_0_2px_10px_rgba(0,0,0,0.3)]">
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                className="w-full h-full bg-transparent border-none outline-none text-white/90 text-xl md:text-2xl leading-relaxed resize-none placeholder:text-white/10 selection:bg-[var(--kira-primary)]/30 font-sans tracking-tight"
              />
            </div>

            {/* Footer / Actions */}
            <div className="px-8 py-6 bg-gradient-to-t from-white/[0.02] to-transparent border-t border-white/5 flex items-center justify-between">
              <div className="hidden md:flex items-center gap-2 text-[11px] text-white/30 font-mono">
                <Command size={14} className="opacity-50" />
                <span>+ Enter to execute pipeline</span>
              </div>

              <div className="flex items-center gap-4 w-full md:w-auto">
                <button
                  onClick={onClose}
                  className="flex-1 md:flex-none px-6 py-2.5 text-sm font-medium text-white/60 hover:text-white transition-colors duration-300"
                >
                  Exit without sending
                </button>
                <button
                  onClick={onSend}
                  disabled={!value.trim()}
                  className="flex-1 md:flex-none px-8 py-3 bg-[var(--kira-primary)] text-black rounded-2xl font-semibold flex items-center justify-center gap-2 hover:bg-white hover:scale-105 hover:shadow-[0_0_20px_rgba(var(--kira-primary-rgb),0.4)] transition-all duration-400 ease-[0.23,1,0.32,1] disabled:opacity-30 disabled:hover:scale-100 disabled:hover:bg-[var(--kira-primary)]"
                >
                  <Send size={18} />
                  Execute System
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}

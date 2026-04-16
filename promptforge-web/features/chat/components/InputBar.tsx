// features/chat/components/InputBar.tsx
// Message input with persona dot, attachment, voice, and waveform visualization
// Production hardening: ARIA labels, accessibility compliance (item #5)

'use client'

import { useRef, KeyboardEvent, useLayoutEffect } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Chip } from '@/components/ui'
import AttachmentPill from './AttachmentPill'
import { Paperclip, Mic, ArrowRight, Maximize2 } from 'lucide-react'

interface InputBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  onAttach: (file: File) => void
  onVoice: () => void
  disabled: boolean
  personaDotColor: 'cold' | 'warm' | 'tuned'
  placeholder: string
  isRecording?: boolean
  attachment?: File | null
  onRemoveAttachment?: () => void
  // Waveform visualization props
  waveformLevels?: number[]
  recordingDuration?: number
  // Accessibility props (Production item #5)
  transcriptionStatus?: 'idle' | 'transcribing' | 'success' | 'error'
  transcriptionMessage?: string
  // Expansion props
  onMaximize?: () => void
}

/**
 * WaveformBar — individual bar in the waveform visualization
 */
function WaveformBar({ level, index }: { level: number; index: number }) {
  const height = Math.max(4, level * 24) // Min 4px, max ~24px

  return (
    <motion.div
      className="w-0.5 bg-[var(--kira-primary)] rounded-full transition-all duration-75"
      style={{ height: `${height}px` }}
      initial={{ height: 4 }}
      animate={{ height: `${height}px` }}
      transition={{ duration: 0.05 }}
    />
  )
}

export default function InputBar({
  value,
  onChange,
  onSubmit,
  onAttach,
  onVoice,
  disabled,
  personaDotColor,
  placeholder,
  isRecording,
  attachment,
  onRemoveAttachment,
  waveformLevels = [],
  recordingDuration = 0,
  transcriptionStatus = 'idle',
  transcriptionMessage,
  onMaximize,
}: InputBarProps) {
  const shouldReduce = useReducedMotion()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const dotColors = {
    cold: 'bg-[var(--dot-cold)]',
    warm: 'bg-[var(--dot-warm)] shadow-[0_0_8px_var(--domain)]',
    tuned: 'bg-[var(--dot-tuned)] shadow-tuned',
  }

  const dotTooltips = {
    cold: "Kira doesn't know you yet",
    warm: 'Kira is learning your patterns',
    tuned: 'Kira knows your work deeply',
  }

  // Liquid Auto-Expansion Logic
  useLayoutEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const newHeight = Math.min(textareaRef.current.scrollHeight, 400)
      textareaRef.current.style.height = `${newHeight}px`
    }
  }, [value])

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSubmit()
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      onAttach(file)
    }
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Format duration as MM:SS
  function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const hasWaveform = isRecording && waveformLevels.length > 0

  return (
    <div className={`relative border border-white/10 bg-[#0a0a0c]/60 backdrop-blur-3xl rounded-2xl p-4 sm:p-5 transition-all duration-400 ease-[0.23,1,0.32,1] shadow-[inset_0_1px_1px_rgba(255,255,255,0.05),0_8px_32px_rgba(0,0,0,0.2)] focus-within:shadow-[0_0_20px_rgba(var(--kira-primary-rgb),0.15)] focus-within:border-[var(--kira-primary)]/40 ${disabled && !isRecording ? 'opacity-80' : ''}`}>
      
      {/* Dynamic ambient pulse when thinking */}
      {disabled && !isRecording && (
        <div className="absolute inset-0 bg-[var(--kira-primary)]/5 rounded-2xl animate-pulse pointer-events-none" />
      )}

      {/* Attachment pill */}
      {attachment && onRemoveAttachment && (
        <div className="mb-3">
          <AttachmentPill file={attachment} onRemove={onRemoveAttachment} />
        </div>
      )}

      {/* Waveform visualization (shown during recording) */}
      {hasWaveform && (
        <div className="mb-4 flex items-center gap-4 px-2" role="status" aria-label="Recording in progress">
          {/* Visual recording indicator with screen reader text */}
          <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse flex-shrink-0 shadow-[0_0_8px_rgba(239,68,68,0.6)]" aria-hidden="true" />
          <span className="sr-only" aria-live="polite">Recording audio, {formatDuration(recordingDuration)} elapsed</span>
          <div className="flex items-center gap-[3px] flex-1 justify-center h-8" aria-hidden="true">
            {waveformLevels.map((level, i) => (
              <WaveformBar key={i} level={level} index={i} />
            ))}
          </div>
          <span className="text-xs text-white/60 font-mono flex-shrink-0 tabular-nums" aria-label={`Recording duration: ${formatDuration(recordingDuration)}`}>
            {formatDuration(recordingDuration)}
          </span>
        </div>
      )}

      {/* Transcription status for screen readers (Production item #5) */}
      {transcriptionStatus !== 'idle' && (
        <div role="status" aria-live="polite" className="sr-only">
          {transcriptionMessage || `Transcription ${transcriptionStatus}`}
        </div>
      )}

      <div className="flex items-end gap-3 sm:gap-4 relative z-10">
        {/* Persona dot */}
        <div className="relative group flex items-center justify-center p-1 sm:p-0">
          <div
            className={`w-2 h-2 rounded-full flex-shrink-0 transition-colors duration-500 ${dotColors[personaDotColor]}`}
          />
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 px-3 py-1.5 bg-[#1a1a1c] border border-white/10 rounded-md text-[11px] text-white/70 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-xl">
            {dotTooltips[personaDotColor]}
          </div>
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={`flex-1 bg-transparent border-none outline-none text-white/90 text-[15px] sm:text-base placeholder:text-white/30 resize-none transition-opacity duration-300 ${disabled && !isRecording ? 'opacity-50' : 'opacity-100'}`}
          style={{ minHeight: '24px', maxHeight: '400px' }}
        />

        {/* Action buttons */}
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
          {/* Paperclip */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="p-2.5 sm:p-2 text-white/40 hover:text-white/90 hover:scale-105 transition-all duration-300 ease-[0.23,1,0.32,1] disabled:opacity-30 rounded-lg hover:bg-white/5 active:scale-95 flex items-center justify-center min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 focus-visible:ring-2 focus-visible:ring-[var(--kira-primary)] outline-none"
            title="Attach file"
            aria-label="Attach file"
          >
            <Paperclip size={20} strokeWidth={2} />
          </button>

          {/* Maximize Toggle */}
          {onMaximize && (
            <button
              onClick={onMaximize}
              disabled={disabled}
              className="hidden sm:flex p-2 text-white/40 hover:text-white/90 hover:scale-105 transition-all duration-300 ease-[0.23,1,0.32,1] disabled:opacity-30 rounded-lg hover:bg-white/5 active:scale-95 items-center justify-center min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 focus-visible:ring-2 focus-visible:ring-[var(--kira-primary)] outline-none"
              title="Expand to Focus Editor"
              aria-label="Expand to Focus Editor"
            >
              <Maximize2 size={18} strokeWidth={2} />
            </button>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,image/*"
            onChange={handleFileSelect}
            className="hidden"
          />

          {/* Mic */}
          <button
            onClick={onVoice}
            disabled={disabled}
            className={`p-2.5 sm:p-2 transition-all duration-300 ease-[0.23,1,0.32,1] disabled:opacity-30 rounded-lg hover:bg-white/5 active:scale-95 flex items-center justify-center min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 focus-visible:ring-2 focus-visible:ring-[var(--kira-primary)] outline-none
              ${isRecording ? 'text-red-400 bg-red-400/10 hover:bg-red-400/20 shadow-[0_0_15px_rgba(239,68,68,0.3)]' : 'text-white/40 hover:text-white/90'}
            `}
            title={isRecording ? 'Stop recording' : 'Voice input'}
            aria-label={isRecording ? 'Stop recording' : 'Start voice recording'}
            aria-pressed={isRecording}
            role="switch"
          >
            <Mic size={20} className={isRecording ? 'animate-pulse' : ''} strokeWidth={2} aria-hidden="true" />
          </button>

          {/* Send */}
          <motion.button
            whileTap={shouldReduce ? undefined : { scale: 0.92 }}
            transition={{ type: 'spring', stiffness: 500, damping: 25 }}
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className="bg-[var(--kira-primary)] text-black rounded-xl px-4 py-2 sm:px-3 sm:py-2 flex items-center justify-center hover:bg-white hover:shadow-[0_0_20px_rgba(var(--kira-primary-rgb),0.4)] hover:scale-105 disabled:opacity-30 disabled:scale-100 disabled:hover:bg-[var(--kira-primary)] disabled:hover:shadow-none disabled:cursor-not-allowed transition-all duration-400 ease-[0.23,1,0.32,1] min-w-[48px] min-h-[48px] sm:min-w-0 sm:min-h-0 focus-visible:ring-2 focus-visible:ring-white outline-none"
            aria-label="Send message"
          >
            <ArrowRight size={20} strokeWidth={2.5} />
          </motion.button>
        </div>
      </div>
    </div>
  )
}

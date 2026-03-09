// features/chat/components/InputBar.tsx
// Message input with persona dot, attachment, voice

'use client'

import { useRef, KeyboardEvent } from 'react'
import { Chip } from '@/components/ui'
import AttachmentPill from './AttachmentPill'

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
}: InputBarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const dotColors = {
    cold: 'bg-[var(--dot-cold)]',
    warm: 'bg-[var(--dot-warm)] shadow-[0_0_6px_var(--domain)]',
    tuned: 'bg-[var(--dot-tuned)] shadow-tuned',
  }

  const dotTooltips = {
    cold: "Kira doesn't know you yet",
    warm: 'Kira is learning your patterns',
    tuned: 'Kira knows your work deeply',
  }

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

  return (
    <div className="border border-border-strong bg-layer2 rounded-xl p-3">
      {/* Attachment pill */}
      {attachment && onRemoveAttachment && (
        <div className="mb-2">
          <AttachmentPill file={attachment} onRemove={onRemoveAttachment} />
        </div>
      )}

      <div className="flex items-end gap-2.5">
        {/* Persona dot */}
        <div className="relative group">
          <div
            className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColors[personaDotColor]}`}
          />
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-layer3 border border-border-strong rounded text-[10px] text-text-dim whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
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
          className="flex-1 bg-transparent border-none outline-none text-text-default text-sm placeholder:text-text-dim resize-none max-h-32"
          style={{ minHeight: '24px' }}
        />

        {/* Action buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Paperclip */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="text-text-dim hover:text-text-bright disabled:opacity-50"
            title="Attach file"
          >
            📎
          </button>
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
            className={`text-text-dim hover:text-text-bright disabled:opacity-50 ${
              isRecording ? 'text-intent border-intent animate-pulse' : ''
            }`}
            title="Voice input"
          >
            🎤
          </button>

          {/* Send */}
          <button
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className="bg-kira border-kira text-white rounded-lg px-3 py-1.5 text-sm font-medium hover:shadow-kira-strong disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            →
          </button>
        </div>
      </div>
    </div>
  )
}

// features/chat/hooks/useInputBar.ts
// Client component hook — Input, attachment, voice state
// 'use client' — contains form state

'use client'

import { useState, KeyboardEvent } from 'react'
import { LIMITS } from '@/lib/constants'

interface UseInputBarProps {
  onSubmit: (message: string, attachment?: File) => void
}

/**
 * Input bar state management
 */
export function useInputBar({ onSubmit }: UseInputBarProps) {
  const [input, setInput] = useState('')
  const [attachment, setAttachment] = useState<File | null>(null)

  /**
   * Handle input change
   */
  function handleInputChange(value: string) {
    setInput(value)
  }

  /**
   * Handle attachment selection
   */
  function handleAttachment(file: File) {
    // Validate file size
    const maxSize = file.type.startsWith('image/') 
      ? LIMITS.IMAGE_MAX_BYTES 
      : LIMITS.FILE_MAX_BYTES
    
    if (file.size > maxSize) {
      // File too large — don't attach
      return { error: `File too large. Max ${maxSize / (1024 * 1024)}MB.` }
    }

    setAttachment(file)
    return { error: null }
  }

  /**
   * Handle keyboard events (Enter to submit)
   */
  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  /**
   * Submit message
   * Input cleared on success, preserved on error
   */
  function handleSubmit() {
    const trimmed = input.trim()
    
    // Validate minimum length
    if (trimmed.length < LIMITS.PROMPT_MIN) {
      return // Don't submit, don't show error
    }

    // Submit (optimistic clear)
    onSubmit(trimmed, attachment ?? undefined)
    setInput('')
    setAttachment(null)
  }

  /**
   * Clear attachment
   */
  function clearAttachment() {
    setAttachment(null)
  }

  return {
    input,
    setInput: handleInputChange,
    attachment,
    setAttachment: handleAttachment,
    clearAttachment,
    handleSubmit,
    handleKeyDown,
  }
}

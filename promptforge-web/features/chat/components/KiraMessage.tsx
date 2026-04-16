// features/chat/components/KiraMessage.tsx
// Kira message with avatar, streaming typewriter effect, and TTS playback button
// Production hardening: ARIA live regions, accessibility compliance (item #5)

'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Volume2, VolumeX, Loader2 } from 'lucide-react'

interface KiraMessageProps {
  message: string
  isError?: boolean
  isStreaming?: boolean
  retryable?: boolean
  onRetry?: () => void
  // TTS props
  onSpeak?: (text: string) => void
  ttsPlaybackState?: 'idle' | 'loading' | 'playing' | 'paused' | 'stopped' | 'error'
  ttsError?: string | null
  // Accessibility: browser fallback notification (Production item #5)
  isUsingBrowserFallback?: boolean
}

export default function KiraMessage({
  message,
  isError,
  isStreaming,
  retryable,
  onRetry,
  onSpeak,
  ttsPlaybackState = 'idle',
  ttsError,
  isUsingBrowserFallback = false,
}: KiraMessageProps) {
  // Parse simple bold markdown (**text**)
  const parseBold = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-text-bright font-semibold">{part.slice(2, -2)}</strong>
      }
      return part
    })
  }

  const handleSpeakClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    onSpeak?.(message)
  }, [onSpeak, message])

  const isSpeaking = ttsPlaybackState === 'playing' || ttsPlaybackState === 'loading'

  // ARIA live announcement for TTS state changes (Production item #5)
  const ttsStateAnnouncement = {
    idle: '',
    loading: 'Generating speech, please wait...',
    playing: 'Speaking...',
    paused: 'Paused',
    stopped: 'Stopped',
    error: 'Speech playback failed',
  }[ttsPlaybackState] || ''

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex gap-3 mb-4 ${isError ? 'border border-intent/20 bg-intent/5 rounded-xl p-4' : ''}`}
      role="article"
      aria-label={`Kira's response${isError ? ' (error)' : ''}`}
    >
      {/* ARIA live region for TTS state changes (Production item #5) */}
      {ttsStateAnnouncement && (
        <div role="status" aria-live="polite" className="sr-only">
          {ttsStateAnnouncement}
        </div>
      )}
      {/* Kira Avatar */}
      <div className="w-8 h-8 rounded-lg border border-kira/30 bg-kira/10 flex items-center justify-center flex-shrink-0 shadow-card">
        <span className="text-kira font-bold font-mono text-sm leading-none">K</span>
      </div>

      {/* Message */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-2">
          <p className="text-text-default text-sm leading-relaxed flex-1">
            {parseBold(message)}
            {isStreaming && (
              <span className="inline-block w-0.5 h-4 bg-kira ml-1 animate-pulse" />
            )}
          </p>

          {/* Speaker/TTS button */}
          {message && !isStreaming && onSpeak && (
            <button
              onClick={handleSpeakClick}
              disabled={ttsPlaybackState === 'loading'}
              className={`flex-shrink-0 p-1 rounded-md transition-colors duration-150 ${
                isSpeaking
                  ? 'text-kira bg-kira/10'
                  : 'text-text-dim hover:text-kira hover:bg-kira/5'
              } disabled:opacity-50`}
              title={
                ttsPlaybackState === 'loading'
                  ? 'Generating speech...'
                  : isSpeaking
                  ? 'Speaking...'
                  : 'Read aloud'
              }
              aria-label={
                isSpeaking
                  ? 'Stop speech playback'
                  : 'Read this message aloud'
              }
              aria-pressed={isSpeaking}
            >
              {ttsPlaybackState === 'loading' ? (
                <Loader2 size={16} className="animate-spin" aria-hidden="true" />
              ) : isSpeaking ? (
                <Volume2 size={16} aria-hidden="true" />
              ) : (
                <VolumeX size={16} aria-hidden="true" />
              )}
            </button>
          )}
        </div>

        {/* TTS error message (Production item #5 — role="status" for screen readers) */}
        {ttsError && (
          <p className="mt-1 text-xs text-intent/80" role="status" aria-live="assertive">
            {ttsError}
          </p>
        )}

        {/* Browser fallback notification (Production item #5 — visual transcript display when TTS fails) */}
        {isUsingBrowserFallback && (
          <div className="mt-2 px-2 py-1 rounded bg-yellow-500/10 border border-yellow-500/20 text-[10px] text-yellow-400/80" role="status" aria-live="polite">
            Using browser voice recognition (lower quality)
          </div>
        )}

        {/* Retry button */}
        {isError && retryable && (
          <button
            onClick={onRetry}
            className="mt-2 text-xs text-kira hover:underline font-medium"
          >
            Try again
          </button>
        )}
      </div>
    </motion.div>
  )
}

// features/chat/hooks/useBrowserVoiceFallback.ts
// ─────────────────────────────────────────────
// Browser-native voice fallback when backend TTS fails
//
// WHY: When Pollinations or ElevenLabs TTS endpoints are down, slow,
// or rate-limited, users should still be able to hear Kira's responses.
// Browser SpeechSynthesis API provides lower-quality but functional TTS.
//
// Features:
// - Automatic fallback when backend TTS fails
// - User notification when using browser fallback
// - Supports pause, resume, stop
// - ARIA announcements for state changes
// ─────────────────────────────────────────────

'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { logger } from '@/lib/logger'

export type BrowserTTSState = 'idle' | 'loading' | 'playing' | 'paused' | 'error'

interface UseBrowserVoiceFallbackOptions {
  onStateChange?: (state: BrowserTTSState) => void
  onEnd?: () => void
}

interface UseBrowserVoiceFallbackReturn {
  state: BrowserTTSState
  isUsingFallback: boolean
  speak: (text: string) => void
  stop: () => void
  pause: () => void
  resume: () => void
  available: boolean
}

/**
 * Check if browser SpeechSynthesis API is available
 */
function isSpeechSynthesisAvailable(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

/**
 * Browser-native TTS fallback hook.
 *
 * WHY: Provides graceful degradation (Production item #8) when backend
 * TTS services are unavailable. Shows notification to user so they
 * know they're using lower-quality fallback.
 *
 * @example
 * const { speak, stop, isUsingFallback } = useBrowserVoiceFallback({
 *   onStateChange: (state) => console.log('TTS state:', state),
 * })
 * speak("Hello world")
 */
export function useBrowserVoiceFallback({
  onStateChange,
  onEnd,
}: UseBrowserVoiceFallbackOptions = {}): UseBrowserVoiceFallbackReturn {
  const [state, setState] = useState<BrowserTTSState>('idle')
  const [isUsingFallback, setIsUsingFallback] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)
  const available = isSpeechSynthesisAvailable()

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  /**
   * Update state and notify listeners
   */
  const updateState = useCallback((newState: BrowserTTSState) => {
    setState(newState)
    onStateChange?.(newState)
  }, [onStateChange])

  /**
   * Speak text using browser SpeechSynthesis API.
   *
   * Shows user notification that browser fallback is active
   * (lower quality than backend TTS).
   */
  const speak = useCallback((text: string) => {
    if (!text || !text.trim()) {
      logger.warn('[browser-tts] speak called with empty text')
      return
    }

    if (!available) {
      logger.error('[browser-tts] SpeechSynthesis not available')
      updateState('error')
      return
    }

    // Stop any current playback
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }

    updateState('loading')
    setIsUsingFallback(true)

    try {
      const utterance = new SpeechSynthesisUtterance(text)

      // Configure voice settings
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0

      // Try to pick a good English voice
      const voices = window.speechSynthesis.getVoices()
      const englishVoice = voices.find(v => v.lang.startsWith('en'))
      if (englishVoice) {
        utterance.voice = englishVoice
      }

      // Event handlers
      utterance.onstart = () => {
        updateState('playing')
        logger.info('[browser-tts] speaking started (browser fallback)')
      }

      utterance.onend = () => {
        updateState('idle')
        setIsUsingFallback(false)
        onEnd?.()
        logger.info('[browser-tts] speaking completed')
      }

      utterance.onerror = (event) => {
        updateState('error')
        setIsUsingFallback(false)
        logger.error(`[browser-tts] error: ${event.error}`)
      }

      utterance.onpause = () => {
        updateState('paused')
      }

      utterance.onresume = () => {
        updateState('playing')
      }

      utteranceRef.current = utterance
      window.speechSynthesis.speak(utterance)

    } catch (err) {
      logger.error('[browser-tts] speak failed', { err })
      updateState('error')
      setIsUsingFallback(false)
    }
  }, [available, updateState, onEnd])

  /**
   * Stop current playback
   */
  const stop = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    updateState('idle')
    setIsUsingFallback(false)
    utteranceRef.current = null
  }, [updateState])

  /**
   * Pause current playback
   */
  const pause = useCallback(() => {
    if (window.speechSynthesis && state === 'playing') {
      window.speechSynthesis.pause()
    }
  }, [state])

  /**
   * Resume paused playback
   */
  const resume = useCallback(() => {
    if (window.speechSynthesis && state === 'paused') {
      window.speechSynthesis.resume()
    }
  }, [state])

  return {
    state,
    isUsingFallback,
    speak,
    stop,
    pause,
    resume,
    available,
  }
}

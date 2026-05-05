// features/chat/hooks/useVoiceOutput.ts
// TTS playback hook — calls /tts endpoint, manages Audio API
// 'use client' — uses browser Audio API + fetch

'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { apiTTS } from '@/lib/api'
import { logger } from '@/lib/logger'

export type PlaybackState = 'idle' | 'loading' | 'playing' | 'paused' | 'stopped' | 'error'

interface UseVoiceOutputOptions {
  token: string
  voiceId?: string
  onPlaybackEnd?: () => void
}

/**
 * Voice output hook — handles TTS request, audio streaming, and playback
 * Uses native Audio API for streaming playback of MP3 from backend
 */
export function useVoiceOutput({ token, voiceId, onPlaybackEnd }: UseVoiceOutputOptions) {
  const [playbackState, setPlaybackState] = useState<PlaybackState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [currentText, setCurrentText] = useState<string>('')

  const audioRef = useRef<HTMLAudioElement | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const sourceUrlRef = useRef<string | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop()
      if (sourceUrlRef.current) {
        URL.revokeObjectURL(sourceUrlRef.current)
        sourceUrlRef.current = null
      }
    }
  }, [])

  /**
   * Speak text using TTS — fetches audio blob then plays it
   */
  const speak = useCallback(async (text: string, options?: { useBrowserOnly?: boolean }) => {
    if (!text || !text.trim()) {
      logger.warn('[voice-output] speak called with empty text')
      return
    }

    // Stop any current playback
    stop()

    setError(null)
    setCurrentText(text)

    // Option to bypass backend (e.g. for testing or offline)
    if (options?.useBrowserOnly) {
      _speakWithBrowser(text)
      return
    }

    setPlaybackState('loading')

    try {
      const abortController = new AbortController()
      abortRef.current = abortController

      const audioBlob = await apiTTS(text, {
        token,
        voiceId,
        signal: abortController.signal,
      })

      if (abortController.signal.aborted) {
        logger.info('[voice-output] TTS request aborted')
        return
      }

      // Create object URL for playback
      const url = URL.createObjectURL(audioBlob)
      sourceUrlRef.current = url

      const audio = new Audio(url)
      audioRef.current = audio

      audio.onplay = () => setPlaybackState('playing')
      audio.onpause = () => setPlaybackState('paused')
      audio.onended = () => {
        setPlaybackState('idle')
        if (sourceUrlRef.current) {
          URL.revokeObjectURL(sourceUrlRef.current)
          sourceUrlRef.current = null
        }
        onPlaybackEnd?.()
      }
      audio.onerror = () => {
        logger.warn('[voice-output] Audio element error — falling back to browser voice')
        _speakWithBrowser(text)
      }

      await audio.play()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        logger.info('[voice-output] TTS request aborted by user')
        setPlaybackState('idle')
        return
      }

      logger.warn('[voice-output] TTS backend failed — falling back to browser voice', { err })
      _speakWithBrowser(text)
    }
  }, [token, voiceId, onPlaybackEnd])

  /**
   * Browser-native fallback using SpeechSynthesis API
   * Used when backend TTS fails or for zero-cost immediate playback
   */
  const _speakWithBrowser = useCallback((text: string) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setError('Voice playback not supported in this browser')
      setPlaybackState('error')
      return
    }

    // Stop any current browser speech
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    
    // Select a pleasant voice if available
    const voices = window.speechSynthesis.getVoices()
    const preferredVoice = voices.find(v => v.name.includes('Google') || v.name.includes('Premium')) || voices[0]
    if (preferredVoice) utterance.voice = preferredVoice

    utterance.onstart = () => setPlaybackState('playing')
    utterance.onend = () => {
      setPlaybackState('idle')
      onPlaybackEnd?.()
    }
    utterance.onerror = () => {
      setPlaybackState('error')
      setError('Browser speech synthesis failed')
    }

    window.speechSynthesis.speak(utterance)
  }, [onPlaybackEnd])

  /**
   * Pause current playback
   */
  const pause = useCallback(() => {
    if (audioRef.current && playbackState === 'playing') {
      audioRef.current.pause()
    }
  }, [playbackState])

  /**
   * Resume paused playback
   */
  const resume = useCallback(() => {
    if (audioRef.current && playbackState === 'paused') {
      audioRef.current.play().catch((err) => {
        logger.error('[voice-output] Resume failed', { err })
        setPlaybackState('error')
      })
    }
  }, [playbackState])

  /**
   * Stop and cleanup
   */
  const stop = useCallback(() => {
    // Abort any in-flight TTS request
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }

    // Stop browser speech synthesis if active
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }

    // Stop audio playback
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current = null
    }

    // Revoke object URL
    if (sourceUrlRef.current) {
      URL.revokeObjectURL(sourceUrlRef.current)
      sourceUrlRef.current = null
    }

    setPlaybackState('idle')
    setCurrentText('')
  }, [])

  /**
   * Toggle play/pause
   */
  const togglePlayPause = useCallback(() => {
    if (playbackState === 'playing') {
      pause()
    } else if (playbackState === 'paused') {
      resume()
    }
  }, [playbackState, pause, resume])

  return {
    playbackState,
    error,
    currentText,
    speak,
    pause,
    resume,
    stop,
    togglePlayPause,
    setError,
  }
}

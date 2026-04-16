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
  const speak = useCallback(async (text: string) => {
    if (!text || !text.trim()) {
      logger.warn('[voice-output] speak called with empty text')
      return
    }

    // Stop any current playback
    stop()

    setError(null)
    setCurrentText(text)
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
        // Revoke object URL after playback completes
        if (sourceUrlRef.current) {
          URL.revokeObjectURL(sourceUrlRef.current)
          sourceUrlRef.current = null
        }
        onPlaybackEnd?.()
      }
      audio.onerror = () => {
        setPlaybackState('error')
        setError('Audio playback failed')
        logger.error('[voice-output] Audio element error')
      }

      await audio.play()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        logger.info('[voice-output] TTS request aborted by user')
        setPlaybackState('idle')
        return
      }

      logger.error('[voice-output] TTS failed', { err })
      setPlaybackState('error')
      setError(err instanceof Error ? err.message : 'TTS failed')
    }
  }, [token, voiceId, onPlaybackEnd])

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

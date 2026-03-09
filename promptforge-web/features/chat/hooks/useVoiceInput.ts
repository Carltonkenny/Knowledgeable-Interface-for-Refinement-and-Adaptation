// features/chat/hooks/useVoiceInput.ts
// Client component hook — MediaRecorder → /transcribe
// 'use client' — uses browser MediaRecorder API

'use client'

import { useState, useRef, useEffect } from 'react'
import { apiTranscribe } from '@/lib/api'
import { logger } from '@/lib/logger'

interface UseVoiceInputProps {
  onTranscript: (text: string) => void
  token: string
}

/**
 * Voice recording hook
 * Uses MediaRecorder API to record audio, then transcribes via backend
 */
export function useVoiceInput({ onTranscript, token }: UseVoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop()
      }
    }
  }, [])

  /**
   * Start recording
   */
  async function startRecording() {
    setError(null)

    // Check browser support
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      setError('Microphone not supported in this browser.')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        // Create audio blob
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
        
        // Transcribe
        try {
          const result = await apiTranscribe(audioBlob, token)
          onTranscript(result.transcript)
        } catch (err) {
          logger.error('Transcription failed', { err })
          setError('Transcription failed. Try typing instead.')
        }

        // Clean up stream
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      logger.error('Microphone access denied', { err })
      setError('Microphone access denied. Please enable in browser settings.')
    }
  }

  /**
   * Stop recording (auto-transcribes)
   */
  function stopRecording() {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  /**
   * Toggle recording
   */
  function toggleRecording() {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return {
    isRecording,
    startRecording,
    stopRecording,
    toggleRecording,
    error,
    setError,
  }
}

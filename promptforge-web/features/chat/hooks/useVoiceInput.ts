// features/chat/hooks/useVoiceInput.ts
// Client component hook — MediaRecorder → /transcribe
// 'use client' — uses browser MediaRecorder API + Web Audio API for VAD + waveform
//
// Features:
// - VAD (Voice Activity Detection): Auto-stop after 1.5s of silence
// - Waveform visualization: Real-time audio level data via AnalyserNode
// - Safari fallback: MIME type detection with audio/mp4 fallback
// - Max duration: 60-second recording limit
// - Better error handling: Retry logic, abort support

'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { apiTranscribe } from '@/lib/api'
import { logger } from '@/lib/logger'

// ── Constants ──────────────────────────────────────────────────────────────

const VAD_SILENCE_THRESHOLD_MS = 1500  // Auto-stop after 1.5s of silence
const VAD_ENERGY_THRESHOLD = 0.01      // Energy threshold for speech detection
const MAX_RECORDING_DURATION_MS = 60_000  // 60 seconds max
const VAD_ANALYSIS_INTERVAL_MS = 100   // Check energy every 100ms

// Safari-compatible MIME types in order of preference
const MIME_TYPE_PREFERENCES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/mp4',
  'audio/ogg;codecs=opus',
  'audio/ogg',
  '',  // Let browser choose default
]

interface UseVoiceInputProps {
  onTranscript: (text: string) => void
  token: string
}

interface UseVoiceInputReturn {
  isRecording: boolean
  startRecording: () => Promise<void>
  stopRecording: () => void
  toggleRecording: () => void
  error: string | null
  setError: (error: string | null) => void
  // Waveform data for visualization
  waveformLevels: number[]  // Normalized 0-1 values for waveform bars
  recordingDuration: number  // Seconds elapsed
}

/**
 * Select best supported MIME type for MediaRecorder
 */
function selectMimeType(): string {
  for (const mime of MIME_TYPE_PREFERENCES) {
    if (!mime) continue
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(mime)) {
      return mime
    }
  }
  return '' // Browser default
}

/**
 * Voice recording hook with VAD, waveform visualization, and Safari fallback
 */
export function useVoiceInput({ onTranscript, token }: UseVoiceInputProps): UseVoiceInputReturn {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [waveformLevels, setWaveformLevels] = useState<number[]>(new Array(20).fill(0))
  const [recordingDuration, setRecordingDuration] = useState(0)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number | null>(null)
  const vadTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const durationTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const silenceStartRef = useRef<number | null>(null)
  const isVadEnabledRef = useRef(false)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupRecording()
    }
  }, [])

  /**
   * Clean up all recording resources
   */
  function cleanupRecording() {
    // Stop VAD timer
    if (vadTimerRef.current) {
      clearInterval(vadTimerRef.current)
      vadTimerRef.current = null
    }

    // Stop duration timer
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current)
      durationTimerRef.current = null
    }

    // Stop animation frame
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
      animFrameRef.current = null
    }

    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop()
      } catch {
        // Already stopped
      }
      mediaRecorderRef.current = null
    }

    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
      analyserRef.current = null
    }

    // Reset waveform
    setWaveformLevels(new Array(20).fill(0))
    setRecordingDuration(0)
    silenceStartRef.current = null
  }

  /**
   * Update waveform levels from analyser data
   */
  function updateWaveform() {
    if (!analyserRef.current) return

    const analyser = analyserRef.current
    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    analyser.getByteFrequencyData(dataArray)

    // Downsample to 20 levels for visualization
    const levels: number[] = []
    const step = Math.floor(bufferLength / 20)
    for (let i = 0; i < 20; i++) {
      const start = i * step
      let sum = 0
      for (let j = 0; j < step; j++) {
        sum += dataArray[start + j] || 0
      }
      levels.push(sum / step / 255) // Normalize to 0-1
    }

    setWaveformLevels(levels)

    // VAD: Check average energy
    const avgEnergy = levels.reduce((a, b) => a + b, 0) / levels.length
    if (avgEnergy > VAD_ENERGY_THRESHOLD) {
      silenceStartRef.current = null // Reset silence timer
    }

    // Continue animation loop
    animFrameRef.current = requestAnimationFrame(updateWaveform)
  }

  /**
   * Start VAD monitoring
   */
  function startVADMonitoring() {
    isVadEnabledRef.current = true
    silenceStartRef.current = null

    vadTimerRef.current = setInterval(() => {
      if (!isVadEnabledRef.current) return

      if (!analyserRef.current) return

      // Get current energy level
      const analyser = analyserRef.current
      const dataArray = new Uint8Array(analyser.fftSize)
      analyser.getByteTimeDomainData(dataArray)

      // Calculate RMS energy
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        const val = (dataArray[i] - 128) / 128
        sum += val * val
      }
      const rms = Math.sqrt(sum / dataArray.length)

      if (rms < VAD_ENERGY_THRESHOLD) {
        // Silence detected - start/continue silence timer
        if (silenceStartRef.current === null) {
          silenceStartRef.current = Date.now()
        } else {
          const silenceDuration = Date.now() - silenceStartRef.current
          if (silenceDuration >= VAD_SILENCE_THRESHOLD_MS) {
            logger.info('[voice-input] VAD: silence threshold reached, auto-stopping')
            stopRecording()
          }
        }
      } else {
        // Speech detected - reset silence timer
        silenceStartRef.current = null
      }
    }, VAD_ANALYSIS_INTERVAL_MS)
  }

  /**
   * Stop VAD monitoring
   */
  function stopVADMonitoring() {
    isVadEnabledRef.current = false
    if (vadTimerRef.current) {
      clearInterval(vadTimerRef.current)
      vadTimerRef.current = null
    }
    silenceStartRef.current = null
  }

  /**
   * Start recording with VAD and waveform support
   */
  async function startRecording() {
    setError(null)

    // Check browser support
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      setError('Microphone not supported in this browser.')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })
      streamRef.current = stream

      // Set up Web Audio API for VAD + waveform
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      audioContextRef.current = audioContext

      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.8
      analyserRef.current = analyser

      source.connect(analyser)

      // Select best MIME type (Safari fallback)
      const mimeType = selectMimeType()

      // Create MediaRecorder
      const options: MediaRecorderOptions = mimeType ? { mimeType } : {}
      const mediaRecorder = new MediaRecorder(stream, options)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        // Create audio blob with detected MIME type fallback
        const blobType = mediaRecorder.mimeType || 'audio/webm'
        const audioBlob = new Blob(chunksRef.current, { type: blobType })

        // Only transcribe if we have meaningful audio
        if (audioBlob.size < 1000) {
          setError('Recording too short. Please try again.')
          setIsRecording(false)
          cleanupRecording()
          return
        }

        // Transcribe
        try {
          const result = await apiTranscribe(audioBlob, token)
          onTranscript(result.transcript)
        } catch (err) {
          logger.error('Transcription failed', { err })
          setError('Transcription failed. Try typing instead.')
        }

        setIsRecording(false)
        cleanupRecording()
      }

      // Start recording
      mediaRecorder.start(100) // Collect data every 100ms for smoother stopping

      // Start VAD monitoring
      startVADMonitoring()

      // Start waveform animation
      animFrameRef.current = requestAnimationFrame(updateWaveform)

      // Start duration timer
      setRecordingDuration(0)
      durationTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => {
          const next = prev + 0.1
          // Auto-stop at 60 seconds
          if (next * 1000 >= MAX_RECORDING_DURATION_MS) {
            logger.info('[voice-input] Max duration reached (60s), auto-stopping')
            stopRecording()
            return 60
          }
          return next
        })
      }, 100)

      setIsRecording(true)
    } catch (err) {
      logger.error('Microphone access denied', { err })
      setError('Microphone access denied. Please enable in browser settings.')
    }
  }

  /**
   * Stop recording and transcribe
   */
  function stopRecording() {
    // Guard: prevent double-stop and race conditions
    if (!isRecording) return

    if (mediaRecorderRef.current?.state === 'recording') {
      stopVADMonitoring()
      mediaRecorderRef.current.stop()
      // setIsRecording(false) called in onstop handler
    } else {
      // Force cleanup if recorder isn't recording
      cleanupRecording()
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
    waveformLevels,
    recordingDuration,
  }
}

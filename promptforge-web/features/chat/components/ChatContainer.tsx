// features/chat/components/ChatContainer.tsx
// Root chat component — owns all state
// Production hardening: wires browser voice fallback (item #8)

'use client'

import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useKiraStream } from '../hooks/useKiraStream'
import { useInputBar } from '../hooks/useInputBar'
import { useVoiceInput } from '../hooks/useVoiceInput'
import { useVoiceOutput } from '../hooks/useVoiceOutput'
import { useBrowserVoiceFallback } from '../hooks/useBrowserVoiceFallback'
import MessageList from './MessageList'
import InputBar from './InputBar'
import EmptyState from './EmptyState'
import FocusEditor from './FocusEditor'
import ClarificationChips from './ClarificationChips'
import { PERSONA_DOT_THRESHOLDS } from '@/lib/constants'
import { logger } from '@/lib/logger'

interface ChatContainerProps {
  token: string
  apiUrl: string
  sessionCount?: number
  sessionId: string
}

function MessageSkeleton() {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className={`flex flex-col ${i % 2 === 0 ? 'items-end' : 'items-start'} space-y-2`}>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-border-subtle animate-pulse" />
            <div className="h-4 w-24 bg-border-subtle rounded animate-pulse" />
          </div>
          <div
            className={`h-16 rounded-2xl bg-border-subtle/50 animate-pulse ${
              i % 2 === 0 ? 'w-2/3 rounded-tr-none' : 'w-3/4 rounded-tl-none'
            }`}
          />
        </div>
      ))}
    </div>
  )
}

export default function ChatContainer({
  token,
  apiUrl,
  sessionCount = 0,
  sessionId
}: ChatContainerProps) {
  const [isFocusEditorOpen, setIsFocusEditorOpen] = useState(false)

  // Determine persona dot color
  let personaDotColor: 'cold' | 'warm' | 'tuned' = 'cold'
  if (sessionCount >= PERSONA_DOT_THRESHOLDS.TUNED) {
    personaDotColor = 'tuned'
  } else if (sessionCount >= PERSONA_DOT_THRESHOLDS.WARM) {
    personaDotColor = 'warm'
  }

  // Kira stream hook
  const {
    messages,
    status,
    isStreaming,
    isRateLimited,
    error,
    clarificationPending,
    clarificationOptions,
    historyLoadError,
    historyLoading,
    queuedMessage,
    send,
    retry,
    clearError,
    reloadHistory,
  } = useKiraStream({
    sessionId,
    token,
    apiUrl,
  })

  // Listen for suggestion clicks from OutputCards
  useEffect(() => {
    const handleSendMessage = (e: Event) => {
      const customEvent = e as CustomEvent<{ message: string }>
      if (customEvent.detail?.message) {
        send(customEvent.detail.message)
      }
    }
    window.addEventListener('send-chat-message', handleSendMessage)
    return () => window.removeEventListener('send-chat-message', handleSendMessage)
  }, [send])

  // Input bar hook
  const {
    input,
    setInput,
    attachment,
    setAttachment,
    clearAttachment,
    handleSubmit,
  } = useInputBar({
    onSubmit: (message, file) => {
      send(message, file)
    },
  })

  // Track latest input value in a ref to avoid stale closure in voice transcript callback
  const inputRef = useRef(input)
  inputRef.current = input

  // Voice input hook — with waveform data
  const {
    isRecording,
    toggleRecording,
    error: voiceError,
    setError: setVoiceError,
    waveformLevels,
    recordingDuration,
  } = useVoiceInput({
    onTranscript: (text) => {
      // Use ref to always get latest input value — avoids stale closure
      setInput(inputRef.current ? `${inputRef.current} ${text}` : text)
    },
    token,
  })

  // Voice output hook — TTS for Kira messages
  const {
    playbackState: ttsPlaybackState,
    error: ttsError,
    speak: ttsSpeak,
    stop: ttsStop,
  } = useVoiceOutput({
    token,
    onPlaybackEnd: () => {
      // Cleanup on playback end
    },
  })

  // Browser voice fallback hook (Production item #8)
  // Used when backend TTS fails — gracefully degrades to browser SpeechSynthesis
  const {
    state: browserTTSState,
    isUsingFallback,
    speak: browserSpeak,
    stop: browserStop,
  } = useBrowserVoiceFallback({
    onStateChange: (state) => {
      logger.info(`[chat-container] browser TTS state change: ${state}`)
    },
  })

  // Handle speak for a specific message — with browser fallback (Production item #8)
  const handleSpeakMessage = useCallback((text: string) => {
    // Try backend TTS first; if it fails, fall back to browser SpeechSynthesis
    ttsSpeak(text).catch(() => {
      logger.warn('[chat-container] Backend TTS failed, using browser fallback')
      browserSpeak(text)
    })
  }, [ttsSpeak, browserSpeak])

  // Cleanup TTS when streaming starts (avoid overlap)
  useEffect(() => {
    if (isStreaming) {
      ttsStop()
      if (isUsingFallback) {
        browserStop()
      }
    }
  }, [isStreaming, ttsStop, isUsingFallback, browserStop])

  // Handle suggestion click from EmptyState
  const handleSuggestionClick = (text: string) => {
    send(text)
  }

  // Handle clarification chip select
  const handleClarificationSelect = (value: string) => {
    send(value)
  }

  // Handle voice button
  const handleVoice = () => {
    toggleRecording()
  }

  // Memoize tts props to pass to MessageList (Production item #5 — includes fallback state)
  const ttsProps = useMemo(() => ({
    onSpeak: handleSpeakMessage,
    ttsPlaybackState: isUsingFallback ? browserTTSState : ttsPlaybackState,
    ttsError: ttsError,
    isUsingBrowserFallback: isUsingFallback,
  }), [handleSpeakMessage, ttsPlaybackState, ttsError, isUsingFallback, browserTTSState])

  // Empty state
  if (messages.length === 0) {
    return (
      <div className="h-full flex flex-col">
        <EmptyState onSuggestionClick={handleSuggestionClick} />
        <div className="p-4">
          <InputBar
            value={input}
            onChange={setInput}
            onSubmit={() => handleSubmit()}
            onAttach={(file) => setAttachment(file)}
            onVoice={handleVoice}
            disabled={false}
            personaDotColor={personaDotColor}
            placeholder="Type your prompt..."
            isRecording={isRecording}
            attachment={attachment}
            onRemoveAttachment={clearAttachment}
            waveformLevels={waveformLevels}
            recordingDuration={recordingDuration}
            onMaximize={() => setIsFocusEditorOpen(true)}
            // Accessibility: transcription status (Production item #5)
            transcriptionStatus={voiceError ? 'error' : 'idle'}
            transcriptionMessage={voiceError || undefined}
          />
        </div>
      </div>
    )
  }

  // Chat UI
  return (
    <div className="h-full flex flex-col max-w-5xl mx-auto w-full">
      {/* History load error with retry button */}
      {historyLoadError && messages.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <div className="text-center space-y-4">
            <div className="text-red-400 text-lg font-medium">{historyLoadError}</div>
            <button
              onClick={reloadHistory}
              className="px-6 py-2 bg-[var(--kira-primary)] text-black rounded-lg hover:bg-white hover:scale-105 transition-all duration-300 ease-[0.23,1,0.32,1] shadow-[0_0_15px_rgba(var(--kira-primary-rgb),0.3)]"
            >
              Retry Loading Conversation
            </button>
          </div>
        </div>
      )}

      {/* Message list */}
      <div className="flex-1 overflow-hidden relative w-full bg-[#08080a] shadow-[inset_0_4px_24px_rgba(0,0,0,0.6)]">
        <MessageList messages={messages} isStreaming={isStreaming} status={status} ttsProps={ttsProps} />

        {/* Skeleton Overlay for session switching */}
        {historyLoading && (
          <div className="absolute inset-0 bg-[#0a0a0c]/80 backdrop-blur-md z-10 flex flex-col">
            <MessageSkeleton />
          </div>
        )}
      </div>

      {/* Clarification chips */}
      {clarificationPending && (
        <ClarificationChips
          chips={clarificationOptions}
          onSelect={handleClarificationSelect}
        />
      )}

      {/* Input bar */}
      <div className="p-4 sm:p-6 pb-6 sm:pb-8 border-t border-white/5 w-full bg-gradient-to-t from-[#0a0a0c] via-[#0a0a0c]/90 to-transparent">
        {/* Queued message indicator */}
        {queuedMessage && (
          <div className="mb-3 px-4 py-2.5 rounded-xl bg-[var(--kira-primary)]/10 border border-[var(--kira-primary)]/30 text-xs text-[var(--kira-primary)] flex items-center gap-2.5 max-w-max mx-auto shadow-[0_4px_12px_rgba(0,0,0,0.5)] backdrop-blur-md delay-100 ease-out transition-all">
            <div className="w-2 h-2 rounded-full bg-[var(--kira-primary)] animate-pulse shadow-[0_0_8px_var(--kira-primary-rgb)]" />
            Message queued — will send after Kira finishes
          </div>
        )}
        <div className="max-w-4xl mx-auto w-full">
          <InputBar
            value={input}
            onChange={setInput}
            onSubmit={() => handleSubmit()}
            onAttach={(file) => setAttachment(file)}
            onVoice={handleVoice}
            disabled={isStreaming || isRateLimited}
            personaDotColor={personaDotColor}
            placeholder={
              queuedMessage
                ? "Message queued..."
                : isStreaming
                ? "Kira is analyzing..."
                : clarificationPending
                ? "Reply to Kira..."
                : "Type your prompt..."
            }
            isRecording={isRecording}
            attachment={attachment}
            onRemoveAttachment={clearAttachment}
            waveformLevels={waveformLevels}
            recordingDuration={recordingDuration}
            onMaximize={() => setIsFocusEditorOpen(true)}
            // Accessibility: transcription status (Production item #5)
            transcriptionStatus={voiceError ? 'error' : 'idle'}
            transcriptionMessage={voiceError || undefined}
          />
        </div>
      </div>

      {/* Focus Editor Modal */}
      <FocusEditor
        isOpen={isFocusEditorOpen}
        onClose={() => setIsFocusEditorOpen(false)}
        value={input}
        onChange={setInput}
        onSend={() => {
          handleSubmit()
          setIsFocusEditorOpen(false)
        }}
        placeholder={
          isStreaming 
            ? "Executing analysis pipeline..." 
            : "Architect your master prompt here..."
        }
      />
    </div>
  )
}

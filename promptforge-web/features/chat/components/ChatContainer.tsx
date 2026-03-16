// features/chat/components/ChatContainer.tsx
// Root chat component — owns all state

'use client'

import { useState, useEffect } from 'react'
import { useSessionId } from '../hooks/useSessionId'
import { useKiraStream } from '../hooks/useKiraStream'
import { useInputBar } from '../hooks/useInputBar'
import { useVoiceInput } from '../hooks/useVoiceInput'
import MessageList from './MessageList'
import InputBar from './InputBar'
import EmptyState from './EmptyState'
import ClarificationChips from './ClarificationChips'
import { PERSONA_DOT_THRESHOLDS } from '@/lib/constants'

interface ChatContainerProps {
  token: string
  apiUrl: string
  sessionCount?: number
  sessionId: string
}

export default function ChatContainer({ 
  token, 
  apiUrl, 
  sessionCount = 0,
  sessionId 
}: ChatContainerProps) {

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
    send,
    retry,
    clearError,
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

  // Voice input hook
  const {
    isRecording,
    toggleRecording,
    error: voiceError,
    setError: setVoiceError,
  } = useVoiceInput({
    onTranscript: (text) => {
      // Insert transcribed text into input
      setInput(input ? `${input} ${text}` : text)
    },
    token,
  })

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
          />
        </div>
      </div>
    )
  }

  // Chat UI
  return (
    <div className="h-full flex flex-col">
      {/* Message list */}
      <MessageList messages={messages} isStreaming={isStreaming} />

      {/* Clarification chips */}
      {clarificationPending && (
        <ClarificationChips
          chips={clarificationOptions}
          onSelect={handleClarificationSelect}
        />
      )}

      {/* Attachment pill */}
      {attachment && (
        <div className="px-4">
          <ClarificationChips
            chips={[]}
            onSelect={() => {}}
          />
        </div>
      )}

      {/* Input bar */}
      <div className="p-4 border-t border-border-subtle">
        <InputBar
          value={input}
          onChange={setInput}
          onSubmit={() => handleSubmit()}
          onAttach={(file) => setAttachment(file)}
          onVoice={handleVoice}
          disabled={isStreaming || isRateLimited}
          personaDotColor={personaDotColor}
          placeholder={clarificationPending ? "Answer Kira..." : "Type your prompt..."}
          isRecording={isRecording}
          attachment={attachment}
          onRemoveAttachment={clearAttachment}
        />
      </div>
    </div>
  )
}

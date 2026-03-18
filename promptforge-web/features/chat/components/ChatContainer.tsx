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
      {/* History load error with retry button */}
      {historyLoadError && messages.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <div className="text-center space-y-4">
            <div className="text-text-error text-lg font-medium">{historyLoadError}</div>
            <button
              onClick={reloadHistory}
              className="px-6 py-2 bg-brand-primary text-white rounded-lg hover:bg-brand-primary/90 transition-colors"
            >
              Retry Loading Conversation
            </button>
          </div>
        </div>
      )}

      {/* Message list */}
      <div className="flex-1 overflow-hidden relative">
        <MessageList messages={messages} isStreaming={isStreaming} status={status} />
        
        {/* Skeleton Overlay for session switching */}
        {historyLoading && (
          <div className="absolute inset-0 bg-bg-primary/80 backdrop-blur-sm z-10 flex flex-col">
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

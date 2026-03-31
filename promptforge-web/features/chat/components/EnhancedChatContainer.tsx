// features/chat/components/EnhancedChatContainer.tsx
// Root chat component — owns all state with enhanced UI

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
import { motion } from 'framer-motion'
import { Activity, Zap, Brain, Shield, Clock, CheckCircle } from 'lucide-react'

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

// Optimization status indicator component
function OptimizationStatus({ isStreaming, cacheHit, memoriesApplied }: { isStreaming: boolean; cacheHit: boolean; memoriesApplied: number }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 px-4 py-2 bg-layer2/50 backdrop-blur-sm border-b border-border-default"
    >
      {/* Cache Status */}
      <div className="flex items-center gap-1.5 text-[11px] text-text-dim">
        {cacheHit ? (
          <>
            <Zap size={12} className="text-kira" />
            <span>Cache Hit</span>
          </>
        ) : isStreaming ? (
          <>
            <Activity size={12} className="text-kira animate-pulse" />
            <span>Processing...</span>
          </>
        ) : (
          <>
            <CheckCircle size={12} className="text-text-dim" />
            <span>Ready</span>
          </>
        )}
      </div>

      {/* Memory Status */}
      {memoriesApplied > 0 && (
        <>
          <div className="w-px h-3 bg-border-subtle" />
          <div className="flex items-center gap-1.5 text-[11px] text-text-dim">
            <Brain size={12} className="text-[var(--domain)]" />
            <span>{memoriesApplied} memories</span>
          </div>
        </>
      )}

      {/* Quality Gate Status */}
      {isStreaming && (
        <>
          <div className="w-px h-3 bg-border-subtle" />
          <div className="flex items-center gap-1.5 text-[11px] text-text-dim">
            <Shield size={12} className="text-kira" />
            <span>Quality Gate Active</span>
          </div>
        </>
      )}
    </motion.div>
  )
}

// Enhanced persona indicator with tooltip
function PersonaIndicator({ color, sessionCount }: { color: 'cold' | 'warm' | 'tuned'; sessionCount: number }) {
  const dotColors = {
    cold: { bg: 'bg-[var(--dot-cold)]', label: 'Cold', desc: "Kira doesn't know you yet" },
    warm: { bg: 'bg-[var(--dot-warm)]', label: 'Warm', desc: 'Kira is learning your patterns' },
    tuned: { bg: 'bg-[var(--dot-tuned)]', label: 'Tuned', desc: 'Kira knows your work deeply' },
  }

  const config = dotColors[color]

  return (
    <div className="relative group">
      <div className={`w-2.5 h-2.5 rounded-full ${config.bg} transition-colors duration-300`} />
      
      {/* Enhanced Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-layer3 border border-border-strong rounded-lg text-[11px] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-all pointer-events-none z-50 shadow-lg">
        <div className="font-medium text-text-bright mb-0.5">{config.label} Sync</div>
        <div className="text-text-dim">{config.desc}</div>
        <div className="text-text-dim mt-1">Sessions: {sessionCount}</div>
        {/* Arrow */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 w-2 h-2 bg-layer3 border-r border-t border-border-strong rotate-45" />
      </div>
    </div>
  )
}

export default function EnhancedChatContainer({
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
    cacheHit,
    memoriesApplied,
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
    onSubmit: () => send(input),
  })

  // Voice input hook
  const {
    isRecording,
    startRecording,
    stopRecording,
  } = useVoiceInput({
    onTranscript: (transcript) => {
      setInput(transcript)
    },
  })

  // Handle suggestion clicks
  const handleSuggestionClick = (suggestion: string) => {
    send(suggestion)
  }

  // Loading state
  if (historyLoading) {
    return <MessageSkeleton />
  }

  // Error state
  if (historyLoadError) {
    return (
      <div className="flex-1 flex items-center justify-center text-text-dim">
        <div className="text-center space-y-4">
          <p>Failed to load conversation history</p>
          <button
            onClick={reloadHistory}
            className="px-4 py-2 bg-kira text-white rounded-lg hover:shadow-glow transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-bg">
      {/* Optimization Status Bar */}
      <OptimizationStatus 
        isStreaming={isStreaming} 
        cacheHit={cacheHit || false}
        memoriesApplied={memoriesApplied || 0}
      />

      {/* Messages or Empty State */}
      {messages.length === 0 && !clarificationPending ? (
        <EmptyState onSuggestionClick={handleSuggestionClick} />
      ) : (
        <MessageList
          messages={messages}
          isStreaming={isStreaming}
          error={error}
          onRetry={retry}
          onClearError={clearError}
        />
      )}

      {/* Clarification Chips */}
      {clarificationPending && clarificationOptions && (
        <ClarificationChips
          options={clarificationOptions}
          onChoose={(option) => send(option)}
        />
      )}

      {/* Rate Limit Warning */}
      {isRateLimited && (
        <div className="mx-4 mb-4 p-3 bg-intent/10 border border-intent rounded-lg text-intent text-sm">
          You've reached your rate limit. Please wait before sending more messages.
        </div>
      )}

      {/* Input Bar */}
      <div className="border-t border-border-default bg-layer2 p-4">
        <div className="max-w-4xl mx-auto">
          <InputBar
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            onAttach={setAttachment}
            onVoice={isRecording ? stopRecording : startRecording}
            disabled={isStreaming || isRateLimited}
            personaDotColor={personaDotColor}
            placeholder={
              isStreaming
                ? "Kira is thinking..."
                : clarificationPending
                ? "Answer Kira's question..."
                : "Paste your rough prompt idea here..."
            }
            isRecording={isRecording}
            attachment={attachment}
            onRemoveAttachment={clearAttachment}
          />

          {/* Helper Text */}
          <div className="mt-2 flex items-center justify-between text-[11px] text-text-dim">
            <div className="flex items-center gap-2">
              <span>Press Enter to send, Shift+Enter for new line</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock size={10} />
              <span>Avg response: 2.8s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

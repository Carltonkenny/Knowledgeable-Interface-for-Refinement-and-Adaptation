// features/chat/components/MessageList.tsx
// Scrollable list of messages + output cards

'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import UserMessage from './UserMessage'
import KiraMessage from './KiraMessage'
import ThinkAccordion from './ThinkAccordion'
import OutputCard from './OutputCard'
import MemoryCitations from './MemoryCitations'
import Boneyard from '@/components/ui/Boneyard'
import type { ChatMessage, ProcessingStatus } from '../types'

interface TTSProps {
  onSpeak: (text: string) => void
  ttsPlaybackState: 'idle' | 'loading' | 'playing' | 'paused' | 'stopped' | 'error'
  ttsError: string | null
}

interface MessageListProps {
  messages: ChatMessage[]
  isStreaming: boolean
  status: ProcessingStatus
  ttsProps?: TTSProps
}

export default function MessageList({ messages, isStreaming, status, ttsProps }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return null
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 shadow-[inset_0_2px_10px_rgba(0,0,0,0.3)] bg-[#050507]">
      <div className="max-w-4xl mx-auto space-y-8">
        {messages.map((message) => {
          switch (message.type) {
            case 'user':
              return message.content ? (
                <div key={message.id} className="flex justify-end">
                  <div className="max-w-[85%] sm:max-w-[75%]">
                    <UserMessage content={message.content} />
                  </div>
                </div>
              ) : null

            case 'kira':
            case 'error':
              return (
                <div key={message.id} className="max-w-[90%] sm:max-w-[85ch]">
                  <KiraMessage
                    message={message.content || ''}
                    isError={message.isError}
                    isStreaming={message.isStreaming}
                    retryable={message.retryable}
                    onSpeak={ttsProps?.onSpeak}
                    ttsPlaybackState={ttsProps?.ttsPlaybackState}
                    ttsError={ttsProps?.ttsError}
                  />
                </div>
              )

            case 'output':
              return message.result ? (
                <div key={message.id} className="w-full">
                  <OutputCard
                    promptId={message.id}
                    sessionId={message.sessionId || ''}
                    result={message.result}
                  />
                  {/* Memory citations — shown below output card when memories were applied */}
                  {message.memoryCitations && message.memoryCitations.length > 0 && (
                    <MemoryCitations citations={message.memoryCitations} />
                  )}
                </div>
              ) : null

            default:
              return null
          }
        })}
      </div>

      {/* Animated Accordion for Agent Thoughts */}
      {status && (status.state === 'kira_reading' || status.state === 'swarm_running' || status.state === 'complete') && (
        <ThinkAccordion status={status} />
      )}

      {/* OutputCard Skeleton while waiting for result */}
      {isStreaming && status && status.isSwarmMode && (
        <motion.div
           layoutId="output-card-skeleton"
           className="mb-6 w-full max-w-2xl mx-auto"
        >
          <div className="rounded-[11px] p-px bg-border-subtle/30 overflow-hidden">
            <div className="bg-layer1 rounded-[10px] p-5 h-40 flex flex-col gap-4">
               {/* Boneyard: Skeleton Header */}
               <div className="flex gap-3 items-center">
                 <Boneyard height="h-3" width="w-24" />
                 <Boneyard height="h-4" width="w-20" />
                 <Boneyard height="h-3" width="w-10" />
               </div>
               {/* Boneyard: Skeleton Body */}
               <Boneyard variant="text" count={3} className="mt-2" />
               {/* Boneyard: Skeleton Chips */}
               <div className="flex gap-2 mt-auto pt-2">
                 <Boneyard height="h-6" width="w-32" />
                 <Boneyard height="h-6" width="w-32" />
               </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Auto-scroll anchor */}
      <div ref={bottomRef} />
    </div>
  )
}

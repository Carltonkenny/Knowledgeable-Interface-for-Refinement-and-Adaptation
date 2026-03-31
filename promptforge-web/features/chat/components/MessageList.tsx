// features/chat/components/MessageList.tsx
// Scrollable list of messages + output cards

'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import UserMessage from './UserMessage'
import KiraMessage from './KiraMessage'
import ThinkAccordion from './ThinkAccordion'
import OutputCard from './OutputCard'
import type { ChatMessage, ProcessingStatus } from '../types'

interface MessageListProps {
  messages: ChatMessage[]
  isStreaming: boolean
  status: ProcessingStatus
}

export default function MessageList({ messages, isStreaming, status }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return null
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      {messages.map((message) => {
        switch (message.type) {
          case 'user':
            return message.content ? (
              <UserMessage key={message.id} content={message.content} />
            ) : null

          case 'kira':
          case 'error':
            return (
              <KiraMessage
                key={message.id}
                message={message.content || ''}
                isError={message.isError}
                isStreaming={message.isStreaming}
                retryable={message.retryable}
              />
            )

          case 'output':
            return message.result ? (
              <OutputCard
                key={message.id}
                promptId={message.id}
                sessionId={message.sessionId || ''}
                result={message.result}
              />
            ) : null

          default:
            return null
        }
      })}

      {/* Animated Accordion for Agent Thoughts */}
      {status && (status.state === 'kira_reading' || status.state === 'swarm_running' || status.state === 'complete') && (
        <ThinkAccordion status={status} />
      )}

      {/* OutputCard Skeleton while waiting for result */}
      {isStreaming && status && (status.state === 'swarm_running' || status.state === 'kira_reading') && (
        <motion.div
           layoutId="output-card-skeleton"
           className="mb-6 w-full max-w-2xl mx-auto"
        >
          <div className="rounded-[11px] p-px bg-border-subtle/30 overflow-hidden">
            <div className="bg-layer1 rounded-[10px] p-5 h-40 animate-pulse flex flex-col gap-4">
               {/* Skeleton Header */}
               <div className="flex gap-3 items-center">
                 <div className="h-3 w-24 bg-layer3/50 rounded-full" />
                 <div className="h-4 w-20 bg-layer3/50 rounded-full" />
                 <div className="h-3 w-10 bg-layer3/50 rounded-full" />
               </div>
               {/* Skeleton Body */}
               <div className="space-y-2.5 mt-2">
                 <div className="h-2.5 bg-layer3/40 rounded-full w-[90%]" />
                 <div className="h-2.5 bg-layer3/40 rounded-full w-[85%]" />
                 <div className="h-2.5 bg-layer3/40 rounded-full w-[70%]" />
               </div>
               {/* Skeleton Chips */}
               <div className="flex gap-2 mt-auto pt-2">
                 <div className="h-6 w-32 bg-layer3/30 rounded-md" />
                 <div className="h-6 w-32 bg-layer3/30 rounded-md" />
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

// features/chat/components/MessageList.tsx
// Scrollable list of messages + output cards

'use client'

import { useEffect, useRef } from 'react'
import UserMessage from './UserMessage'
import KiraMessage from './KiraMessage'
import StatusChips from './StatusChips'
import OutputCard from './OutputCard'
import type { ChatMessage } from '../types'

interface MessageListProps {
  messages: ChatMessage[]
  isStreaming: boolean
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
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
                result={message.result}
                onCopy={() => {
                  navigator.clipboard.writeText(message.result!.improved_prompt)
                }}
                isCopied={false}
              />
            ) : null

          default:
            return null
        }
      })}

      {/* Status chips during streaming */}
      {isStreaming && (
        <StatusChips
          status={{
            state: 'swarm_running',
            agentsComplete: new Set(),
            agentsSkipped: new Set(),
          }}
        />
      )}

      {/* Auto-scroll anchor */}
      <div ref={bottomRef} />
    </div>
  )
}

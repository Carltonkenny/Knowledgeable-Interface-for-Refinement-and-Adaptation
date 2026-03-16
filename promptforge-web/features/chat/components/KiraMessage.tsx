// features/chat/components/KiraMessage.tsx
// Kira message with avatar and streaming typewriter effect

'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface KiraMessageProps {
  message: string
  isError?: boolean
  isStreaming?: boolean
  retryable?: boolean
  onRetry?: () => void
}

export default function KiraMessage({
  message,
  isError,
  isStreaming,
  retryable,
  onRetry,
}: KiraMessageProps) {
  const [displayedText, setDisplayedText] = useState('')
  
  // Typewriter effect for streaming messages
  useEffect(() => {
    if (!isStreaming) {
      // Show full message immediately when not streaming
      setDisplayedText(message)
      return
    }
    
    // Streaming typewriter effect
    let currentIndex = 0
    setDisplayedText('')
    
    const typeInterval = setInterval(() => {
      if (currentIndex < message.length) {
        // Add chunk of 2-3 chars for faster typing
        const chunkSize = Math.min(3, message.length - currentIndex)
        setDisplayedText(message.slice(0, currentIndex + chunkSize))
        currentIndex += chunkSize
      } else {
        clearInterval(typeInterval)
      }
    }, 10) // 10ms per chunk = fast typing
    
    return () => clearInterval(typeInterval)
  }, [message, isStreaming])

  // Parse simple bold markdown (**text**)
  const parseBold = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-text-bright font-semibold">{part.slice(2, -2)}</strong>
      }
      return part
    })
  }

  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex gap-3 mb-4 ${isError ? 'border border-intent/20 bg-intent/5 rounded-xl p-4' : ''}`}
    >
      {/* Kira Avatar */}
      <div className="w-8 h-8 rounded-lg border border-kira/30 bg-kira/10 flex items-center justify-center flex-shrink-0 shadow-card">
        <span className="text-kira font-bold font-mono text-sm leading-none">K</span>
      </div>

      {/* Message */}
      <div className="flex-1">
        <p className="text-text-default text-sm leading-relaxed">
          {parseBold(displayedText)}
          {isStreaming && displayedText.length < message.length && (
            <span className="inline-block w-0.5 h-4 bg-kira ml-1 animate-pulse" />
          )}
        </p>

        {/* Retry button */}
        {isError && retryable && (
          <button
            onClick={onRetry}
            className="mt-2 text-xs text-kira hover:underline font-medium"
          >
            Try again
          </button>
        )}
      </div>
    </motion.div>
  )
}

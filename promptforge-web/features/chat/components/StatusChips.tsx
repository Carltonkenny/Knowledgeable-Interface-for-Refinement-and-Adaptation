// features/chat/components/StatusChips.tsx
// Processing chips row with 600ms minimum display time

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Chip } from '@/components/ui'
import type { ProcessingStatus } from '../types'

interface StatusChipsProps {
  status: ProcessingStatus
}

export default function StatusChips({ status }: StatusChipsProps) {
  const [currentStatus, setCurrentStatus] = useState<string | undefined>('Sleeping') // Initial state
  const queueRef = useRef<string[]>([])
  const isDisplayingRef = useRef(false)
  const isMountedRef = useRef(false)

  // When statusText changes, queue it up (unless it's empty)
  useEffect(() => {
    isMountedRef.current = true
    if (status.statusText) {
      queueRef.current.push(status.statusText)
      processQueue()
    }
    return () => { isMountedRef.current = false }
  }, [status.statusText])

  const processQueue = () => {
    if (isDisplayingRef.current || queueRef.current.length === 0) return

    isDisplayingRef.current = true
    const nextStatus = queueRef.current.shift()
    setCurrentStatus(nextStatus)

    setTimeout(() => {
      isDisplayingRef.current = false
      if (isMountedRef.current) {
        processQueue() // Pick up next in queue if any
      }
    }, 600) // Minimum 600ms display
  }

  // If we are fully done processing upstream and queue is empty, fade out entirely
  if (status.state === 'idle' || status.state === 'complete') {
     if (queueRef.current.length === 0 && !isDisplayingRef.current) {
       return null
     }
  }

  return (
    <div className="flex items-center gap-2 mb-4 h-8 overflow-hidden pl-1">
      <AnimatePresence mode="wait">
        {currentStatus && (
          <motion.div
            key={currentStatus}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <Chip variant="kira" active>
              {currentStatus}
            </Chip>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

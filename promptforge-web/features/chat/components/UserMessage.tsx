// features/chat/components/UserMessage.tsx
// User message bubble

import { motion } from 'framer-motion'

interface UserMessageProps {
  content: string
}

export default function UserMessage({ content }: UserMessageProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="flex justify-end mb-4"
    >
      <div className="max-w-[80%] bg-[var(--surface-hover)] border border-border-default shadow-card rounded-2xl rounded-br-sm px-4 py-3">
        <p className="text-text-bright text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
      </div>
    </motion.div>
  )
}

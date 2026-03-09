// features/chat/components/UserMessage.tsx
// User message bubble

interface UserMessageProps {
  content: string
}

export default function UserMessage({ content }: UserMessageProps) {
  return (
    <div className="flex justify-end mb-4">
      <div className="max-w-[80%] bg-layer2 border border-border-strong rounded-2xl rounded-br-sm px-4 py-3">
        <p className="text-text-default text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  )
}

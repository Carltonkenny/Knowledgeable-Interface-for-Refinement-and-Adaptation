// features/chat/components/AttachmentPill.tsx
// File attachment pill above input

interface AttachmentPillProps {
  file: File
  onRemove: () => void
}

export default function AttachmentPill({ file, onRemove }: AttachmentPillProps) {
  const icon = file.type.startsWith('image/') ? '🖼️' : '📄'
  const maxSize = 24
  const displayName = file.name.length > maxSize
    ? file.name.slice(0, maxSize) + '...'
    : file.name

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-layer1 border border-border-strong inline-flex">
      <span className="text-lg">{icon}</span>
      <span className="text-[11px] text-text-default font-display">{displayName}</span>
      <button
        onClick={onRemove}
        className="text-text-dim hover:text-intent text-[14px] font-bold"
      >
        ×
      </button>
    </div>
  )
}

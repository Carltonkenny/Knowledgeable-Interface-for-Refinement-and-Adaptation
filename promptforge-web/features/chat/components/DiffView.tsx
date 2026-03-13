// features/chat/components/DiffView.tsx
// Diff display (additions/removals inline)

import type { DiffItem } from '@/lib/api'

interface DiffViewProps {
  diff?: DiffItem[]
}

export default function DiffView({ diff }: DiffViewProps) {
  // Safe guard for null/undefined/empty diff
  if (!diff || !Array.isArray(diff) || diff.length === 0) {
    return (
      <div className="text-sm text-text-dim italic">
        No diff available - prompt was generated without modifications
      </div>
    )
  }

  return (
    <div className="text-sm leading-relaxed">
      {diff.map((item, index) => {
        if (item.type === 'add') {
          return (
            <span
              key={index}
              className="bg-context/15 text-[#6ee7b7] rounded px-0.5"
            >
              {item.text}
            </span>
          )
        }
        if (item.type === 'remove') {
          return (
            <span
              key={index}
              className="line-through text-text-dim opacity-60"
            >
              {item.text}
            </span>
          )
        }
        return (
          <span key={index} className="text-text-default">
            {item.text}
          </span>
        )
      })}
    </div>
  )
}

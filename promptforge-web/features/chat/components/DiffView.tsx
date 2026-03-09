// features/chat/components/DiffView.tsx
// Diff display (additions/removals inline)

import type { DiffItem } from '@/lib/api'

interface DiffViewProps {
  diff: DiffItem[]
}

export default function DiffView({ diff }: DiffViewProps) {
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

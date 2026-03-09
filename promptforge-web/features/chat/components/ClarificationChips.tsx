// features/chat/components/ClarificationChips.tsx
// Quick-reply chips for Kira's questions

interface ClarificationChipsProps {
  chips: string[]
  onSelect: (value: string) => void
}

export default function ClarificationChips({ chips, onSelect }: ClarificationChipsProps) {
  return (
    <div className="flex gap-2 mb-4 flex-wrap justify-center">
      {chips.map((chip, index) => (
        <button
          key={index}
          onClick={() => onSelect(chip)}
          className="px-4 py-2 rounded-full border border-[var(--kira-dim)] bg-[var(--kira-glow)] text-[12px] text-kira hover:bg-[var(--kira-dim)] transition-colors"
        >
          {chip}
        </button>
      ))}
    </div>
  )
}

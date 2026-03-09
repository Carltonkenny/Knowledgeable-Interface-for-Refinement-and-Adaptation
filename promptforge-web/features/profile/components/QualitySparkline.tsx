// features/profile/components/QualitySparkline.tsx
// 30-day quality chart (placeholder)

export default function QualitySparkline() {
  // Placeholder — would fetch real data in production
  const data = [3, 4, 3, 5, 4, 4, 5, 4, 5, 5, 4, 5]

  return (
    <div className="h-16 flex items-end gap-1">
      {data.map((value, index) => (
        <div
          key={index}
          className="flex-1 bg-kira rounded-t transition-all"
          style={{ height: `${(value / 5) * 100}%` }}
        />
      ))}
    </div>
  )
}

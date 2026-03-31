'use client'

import { Info } from 'lucide-react'

interface HeatmapData {
  date: string
  count: number
}

interface PromptHeatmapProps {
  data: HeatmapData[]
  isLoading: boolean
}

export default function PromptHeatmap({ data, isLoading }: PromptHeatmapProps) {
  if (isLoading) {
    return (
      <div className="bg-layer2 rounded-xl p-5 border border-border-subtle animate-pulse h-48">
        <div className="h-6 w-48 bg-layer3 rounded-md mb-6" />
        <div className="flex gap-1 h-32 overflow-hidden items-end">
          {Array.from({ length: 50 }).map((_, i) => (
            <div key={i} className="flex-1 bg-layer3 rounded-sm" style={{ height: `${Math.random() * 100}%` }} />
          ))}
        </div>
      </div>
    )
  }

  // Pre-calculate intensities (0-4)
  const maxCount = Math.max(...data.map(d => d.count), 1)
  
  const getIntensity = (count: number) => {
    if (count === 0) return 0
    const ratio = count / maxCount
    if (ratio <= 0.25) return 1
    if (ratio <= 0.5) return 2
    if (ratio <= 0.75) return 3
    return 4
  }

  const intensityColors = [
    'bg-layer3/30 border-transparent', // 0
    'bg-kira/20 border-kira/10',       // 1
    'bg-kira/40 border-kira/20',       // 2
    'bg-kira/70 border-kira/30',       // 3
    'bg-kira shadow-[0_0_10px_rgba(var(--color-kira),0.4)] border-kira/50' // 4
  ]

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle overflow-hidden">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-layer3 text-text-bright">
            <Info size={18} />
          </div>
          <div>
            <h3 className="text-base font-medium text-text-bright tracking-tight">Prompt Activity</h3>
            <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
              365-Day Forging Consistency
            </p>
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex items-center gap-1.5 grayscale opacity-60">
          <span className="text-[10px] font-mono text-text-dim mr-1">LESS</span>
          {[0, 1, 2, 3, 4].map(i => (
            <div key={i} className={`w-2.5 h-2.5 rounded-sm ${intensityColors[i]}`} />
          ))}
          <span className="text-[10px] font-mono text-text-dim ml-1">MORE</span>
        </div>
      </div>

      <div className="relative group">
        <div className="flex gap-1 overflow-x-auto pb-4 custom-scrollbar no-scrollbar scroll-smooth">
          {/* We simplify the grid to columns (weeks) for high-performance React rendering */}
          <div className="grid grid-flow-col grid-rows-7 gap-1 min-w-max">
            {data.slice(-371).map((day, idx) => {
              const intensity = getIntensity(day.count)
              const dateStr = new Date(day.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
              return (
                <div
                  key={idx}
                  title={`${day.count} prompts - ${dateStr}`}
                  className={`w-3 h-3 rounded-sm border transition-all duration-300 hover:scale-125 hover:z-10 cursor-pointer ${intensityColors[intensity]}`}
                />
              )
            })}
          </div>
        </div>

        {/* Gloss Overlay */}
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-layer2 via-transparent to-layer2 opacity-0 group-hover:opacity-10 transition-opacity duration-700" />
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-4 text-[10px] font-mono text-text-dim uppercase">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-success" />
            <span>Peak Activity: {maxCount} prompts/day</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-kira" />
            <span>Consistency: High</span>
          </div>
        </div>
      </div>
    </div>
  )
}

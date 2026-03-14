'use client'

import { Activity } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import type { QualityTrendPoint } from '@/lib/api'

interface QualityTrendProps {
  trend: QualityTrendPoint[]
  isLoading: boolean
}

export default function QualityTrend({ trend, isLoading }: QualityTrendProps) {
  if (isLoading) {
    return (
      <div className="bg-layer2 rounded-xl p-5 border border-border-subtle animate-pulse h-48">
        <div className="h-6 w-40 bg-layer3 rounded-md mb-4" />
        <div className="h-24 w-full bg-layer3 rounded-lg" />
      </div>
    )
  }

  // Calculate moving average or basic trend indicator
  const latestScores = trend.slice(-5)
  const averageRecent = latestScores.length > 0 
    ? latestScores.reduce((acc, pt) => acc + pt.score, 0) / latestScores.length 
    : 0

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-green-500/10 text-green-500">
            <Activity size={18} />
          </div>
          <div>
            <h3 className="text-base font-medium text-text-bright">Quality Horizon</h3>
            <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
              Recent Prompt Evolution
            </p>
          </div>
        </div>
        
        {trend.length > 0 && (
          <div className="text-right">
            <span className="text-2xl font-bold text-text-bright">
              {averageRecent.toFixed(1)}
            </span>
            <span className="text-xs text-text-muted ml-1">/ 5.0</span>
            <p className="text-[10px] text-text-dim uppercase tracking-wider">
              Recent Avg
            </p>
          </div>
        )}
      </div>

      {trend.length < 2 ? (
        <div className="flex flex-col items-center justify-center py-6 text-text-dim border border-dashed border-border-subtle rounded-lg bg-layer1/50 h-[100px]">
          <Activity size={20} className="mb-2 opacity-30" />
          <p className="text-sm">Not enough data for trend analysis.</p>
        </div>
      ) : (
        <div className="h-[100px] w-full mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trend}>
              <XAxis dataKey="index" hide />
              <YAxis domain={[0, 5]} hide />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div className="bg-layer1 border border-border-subtle p-2 rounded-lg shadow-xl">
                        <p className="text-text-bright font-mono text-sm">
                          Score: <span className="text-kira">{data.score.toFixed(1)}</span>
                        </p>
                        <p className="text-text-dim text-xs mt-1">
                          {new Date(data.date).toLocaleDateString()}
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke="var(--color-kira)"
                strokeWidth={2}
                dot={{ r: 3, fill: 'var(--color-layer1)', strokeWidth: 2 }}
                activeDot={{ r: 5, fill: 'var(--color-kira)' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

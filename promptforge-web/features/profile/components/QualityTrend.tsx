'use client'

import { Activity, TrendingUp } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts'
import type { QualityTrendPoint } from '@/lib/api'

interface QualityTrendProps {
  trend: QualityTrendPoint[]
  isLoading: boolean
}

const SCORE_COLORS = {
  5: 'var(--color-success)',
  4: 'var(--color-kira)',
  3: 'var(--color-warning)',
  2: 'var(--color-intent)',
  1: 'var(--color-error)',
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

  // Calculate score distribution
  const scoreDistribution = [5, 4, 3, 2, 1].map(score => ({
    score,
    count: trend.filter(t => Math.round(t.score) === score).length,
    percentage: trend.length > 0 ? (trend.filter(t => Math.round(t.score) === score).length / trend.length) * 100 : 0,
  })).filter(d => d.count > 0)

  const totalPrompts = trend.length

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
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-text-bright">
                {averageRecent.toFixed(1)}
              </span>
              <span className="text-xs text-text-muted">/ 5.0</span>
            </div>
            <p className="text-[10px] text-text-dim uppercase tracking-wider">
              Recent Avg ({latestScores.length} prompts)
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
        <div className="space-y-3">
          {/* Score Distribution Bars */}
          <div className="mb-3">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp size={12} className="text-text-dim" />
              <span className="text-[10px] font-mono text-text-dim uppercase tracking-wider">
                Score Distribution ({totalPrompts} total)
              </span>
            </div>
            <div className="flex items-end gap-1 h-12">
              {scoreDistribution.map((d) => (
                <div
                  key={d.score}
                  className="flex-1 flex flex-col items-center gap-1"
                  style={{ flex: d.count }}
                >
                  <div
                    className="w-full rounded-t transition-all hover:opacity-80"
                    style={{
                      height: `${(d.count / totalPrompts) * 100}%`,
                      minHeight: '4px',
                      backgroundColor: SCORE_COLORS[d.score as keyof typeof SCORE_COLORS],
                    }}
                    title={`Score ${d}: ${d.count} prompts (${d.percentage.toFixed(0)}%)`}
                  />
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-1">
              {scoreDistribution.map((d) => (
                <div
                  key={d.score}
                  className="flex flex-col items-center"
                  style={{ flex: d.count }}
                >
                  <span className="text-[9px] font-mono text-text-dim">{d.score}</span>
                  <span className="text-[8px] font-mono text-text-muted">{d.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Trend Line Chart */}
          <div className="h-[80px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <XAxis dataKey="index" hide />
                <YAxis domain={[0, 5]} hide />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload
                      const scoreColor = SCORE_COLORS[Math.round(data.score) as keyof typeof SCORE_COLORS] || 'var(--color-kira)'
                      return (
                        <div className="bg-layer1 border border-border-subtle p-2 rounded-lg shadow-xl">
                          <div className="flex items-center gap-2 mb-1">
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: scoreColor }}
                            />
                            <p className="text-text-bright font-mono text-sm">
                              Score: <span style={{ color: scoreColor }}>{data.score.toFixed(1)}</span>
                            </p>
                          </div>
                          <p className="text-text-dim text-xs mt-1">
                            {new Date(data.date).toLocaleDateString()}
                          </p>
                          <p className="text-text-dim text-[10px] mt-1">
                            Specificity: {data.specificity ?? 'N/A'} · Clarity: {data.clarity ?? 'N/A'} · Actionability: {data.actionability ?? 'N/A'}
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
        </div>
      )}
    </div>
  )
}

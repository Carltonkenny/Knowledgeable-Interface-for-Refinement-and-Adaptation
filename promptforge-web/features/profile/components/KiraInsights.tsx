'use client'

import { Brain, TrendingUp, TrendingDown, Minus, Target, Zap, Eye } from 'lucide-react'

interface KiraInsightsProps {
  dominantDomains: string[]
  preferredTone: string
  clarificationRate: number
  domainConfidence: number
  promptQualityTrend: string
  notablePatterns: string[]
}

const toneLabels: Record<string, string> = {
  direct: 'Direct & professional',
  casual: 'Casual & conversational',
  technical: 'Technical & precise',
}

const trendIcons: Record<string, React.ReactNode> = {
  improving: <TrendingUp size={14} className="text-green-400" />,
  declining: <TrendingDown size={14} className="text-red-400" />,
  stable: <Minus size={14} className="text-yellow-400" />,
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="w-full h-1.5 bg-layer3 rounded-full overflow-hidden">
      <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export default function KiraInsights({
  dominantDomains,
  preferredTone,
  clarificationRate,
  domainConfidence,
  promptQualityTrend,
  notablePatterns,
}: KiraInsightsProps) {
  const hasData = dominantDomains.length > 0 || promptQualityTrend !== 'stable' || domainConfidence > 0.5

  if (!hasData) {
    return (
      <div className="bg-layer2 rounded-xl p-5 border border-border-subtle">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-kira/10">
            <Brain size={18} className="text-kira" />
          </div>
          <div>
            <h3 className="text-base font-medium text-text-bright">Kira's Insights</h3>
            <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
              What Kira Has Learned
            </p>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center py-6 text-text-dim border border-dashed border-border-subtle rounded-lg bg-layer1/50">
          <Brain size={24} className="mb-2 opacity-30" />
          <h4 className="text-sm font-semibold text-text-bright mb-2">Still Learning</h4>
          <p className="text-xs text-center max-w-[240px]">
            Kira analyzes your patterns as you forge prompts. After a few sessions, you'll see your domains, quality trends, and preferences here.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-kira/10">
          <Brain size={18} className="text-kira" />
        </div>
        <div>
          <h3 className="text-base font-medium text-text-bright">Kira's Insights</h3>
          <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold">
            What Kira Has Learned
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Dominant Domains */}
        {dominantDomains.length > 0 && (
          <div className="flex items-start gap-3">
            <div className="p-1.5 rounded bg-blue-500/10 text-blue-400 mt-0.5">
              <Target size={14} />
            </div>
            <div className="flex-1">
              <div className="text-[10px] text-text-dim uppercase tracking-wider font-semibold mb-1">
                Your Domains
              </div>
              <div className="flex flex-wrap gap-1.5">
                {dominantDomains.map((d, i) => (
                  <span
                    key={i}
                    className="text-xs font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20"
                  >
                    {d}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Quality Trend */}
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded bg-layer3 text-text-bright mt-0.5">
            {trendIcons[promptQualityTrend] || trendIcons.stable}
          </div>
          <div className="flex-1">
            <div className="text-[10px] text-text-dim uppercase tracking-wider font-semibold mb-1">
              Quality Trend
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-sm font-medium ${
                promptQualityTrend === 'improving' ? 'text-green-400' :
                promptQualityTrend === 'declining' ? 'text-red-400' :
                'text-yellow-400'
              }`}>
                {promptQualityTrend.charAt(0).toUpperCase() + promptQualityTrend.slice(1)}
              </span>
            </div>
          </div>
        </div>

        {/* Domain Confidence */}
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded bg-layer3 text-text-bright mt-0.5">
            <Eye size={14} />
          </div>
          <div className="flex-1">
            <div className="text-[10px] text-text-dim uppercase tracking-wider font-semibold mb-1">
              Domain Confidence
            </div>
            <ConfidenceBar value={domainConfidence} />
            <div className="text-[10px] text-text-muted mt-1">
              {Math.round(domainConfidence * 100)}% — {domainConfidence >= 0.8 ? 'Kira skips domain detection for speed' : 'Kira still learning your patterns'}
            </div>
          </div>
        </div>

        {/* Preferred Tone */}
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded bg-layer3 text-text-bright mt-0.5">
            <Zap size={14} />
          </div>
          <div className="flex-1">
            <div className="text-[10px] text-text-dim uppercase tracking-wider font-semibold mb-1">
              Preferred Tone
            </div>
            <span className="text-sm font-medium text-text-bright">
              {toneLabels[preferredTone] || preferredTone}
            </span>
          </div>
        </div>

        {/* Clarification Rate */}
        {clarificationRate > 0 && (
          <div className="flex items-start gap-3">
            <div className="p-1.5 rounded bg-layer3 text-text-bright mt-0.5">
              <Target size={14} />
            </div>
            <div className="flex-1">
              <div className="text-[10px] text-text-dim uppercase tracking-wider font-semibold mb-1">
                Clarification Rate
              </div>
              <span className="text-sm font-medium text-text-bright">
                {Math.round(clarificationRate * 100)}% of requests needed clarification
              </span>
            </div>
          </div>
        )}

        {/* Notable Patterns */}
        {notablePatterns.length > 0 && (
          <div className="flex items-start gap-3">
            <div className="p-1.5 rounded bg-layer3 text-text-bright mt-0.5">
              <Brain size={14} />
            </div>
            <div className="flex-1">
              <div className="text-[10px] text-text-dim uppercase tracking-wider font-semibold mb-1">
                Notable Patterns
              </div>
              <ul className="text-xs text-text-muted space-y-0.5">
                {notablePatterns.slice(0, 5).map((p, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-kira mt-0.5">•</span>
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

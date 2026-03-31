// features/history/components/HistoryAnalyticsDashboard.tsx
'use client'

import { useState } from 'react'
import {
  ResponsiveContainer, RadarChart, PolarGrid,
  PolarAngleAxis, Radar, Legend, Tooltip
} from 'recharts'
import { Target, Clock, PieChart, Trophy, Landmark, Sparkles, Maximize2, X, ArrowUpRight } from 'lucide-react'
import type { HistoryAnalytics } from '@/lib/api'

interface HistoryAnalyticsDashboardProps {
  analytics: HistoryAnalytics | null
  isLoading: boolean
  onDomainSelect?: (domain: string) => void
}

export default function HistoryAnalyticsDashboard({
  analytics,
  isLoading,
  onDomainSelect,
}: HistoryAnalyticsDashboardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-28 bg-layer2/50 border border-border rounded-2xl animate-pulse"
          />
        ))}
      </div>
    )
  }

  const currentAnalytics = analytics || {
    total_prompts: 0,
    hours_saved: 0,
    unique_domains: 0,
    avg_quality: 0,
    domain_distribution: {},
    quality_trend: []
  }

  // Only show Empty State if CERTAIN no data exists
  if (!isLoading && currentAnalytics.total_prompts === 0) {
    return (
      <div className="bg-layer2/30 border border-border/50 p-8 rounded-3xl mb-10 flex flex-col items-center justify-center text-center animate-in fade-in duration-700">
        <Landmark className="w-12 h-12 text-text-dim mb-4 opacity-20" />
        <h3 className="text-lg font-bold text-text-dim uppercase tracking-widest italic">Memory Palace Vault Empty</h3>
        <p className="text-xs text-text-dim/60 mt-2 max-w-xs">Awaiting your first prompt to compute your expertise topology.</p>
      </div>
    )
  }

  // Base raw data for the list
  const rawDomainData = Object.entries(currentAnalytics.domain_distribution)
    .sort((a, b) => b[1].count - a[1].count)
    .map(([name, data]) => {
      const maxCount = Math.max(...Object.values(currentAnalytics.domain_distribution).map(d => d.count), 1)
      return {
        name: name.length > 15 ? name.substring(0, 15) + '...' : name,
        full_name: name,
        volume: (data.count / maxCount) * 100,
        skill: (data.avg_quality / 5) * 100,
        raw_count: data.count,
        raw_quality: data.avg_quality,
        isReal: true
      }
    })

  // Prepare chart data: Inject placeholders if 1 or 2 domains so the single domain heavily bulges out
  const chartDomainData = [...rawDomainData]
  
  if (chartDomainData.length === 1) {
    chartDomainData.push(
      { name: 'Creative', full_name: 'Creative', volume: 15, skill: 15, raw_count: 0, raw_quality: 0, isReal: false },
      { name: 'Technical', full_name: 'Technical', volume: 15, skill: 15, raw_count: 0, raw_quality: 0, isReal: false },
      { name: 'Business', full_name: 'Business', volume: 15, skill: 15, raw_count: 0, raw_quality: 0, isReal: false }
    )
  } else if (chartDomainData.length === 2) {
    chartDomainData.push(
      { name: 'Creative', full_name: 'Creative', volume: 15, skill: 15, raw_count: 0, raw_quality: 0, isReal: false },
      { name: 'General', full_name: 'General', volume: 15, skill: 15, raw_count: 0, raw_quality: 0, isReal: false }
    )
  }

  return (
    <div className="space-y-6 mb-10 relative">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Prompts */}
        <div className="bg-layer2 border border-border p-5 rounded-2xl flex items-center justify-between shadow-sm hover:border-text-dim/30 transition-colors">
          <div>
            <p className="text-text-dim text-[10px] font-bold mb-1 uppercase tracking-[0.2em]">Prompts Logged</p>
            <p className="text-2xl font-bold text-text font-mono">{currentAnalytics.total_prompts}</p>
          </div>
          <div className="bg-kira/10 p-2.5 rounded-xl border border-kira/20">
            <Sparkles className="w-5 h-5 text-kira" />
          </div>
        </div>

        {/* Time Saved */}
        <div className="bg-layer2 border border-border p-5 rounded-2xl flex items-center justify-between shadow-sm hover:border-text-dim/30 transition-colors">
          <div>
            <p className="text-text-dim text-[10px] font-bold mb-1 uppercase tracking-[0.2em]">Time Saved</p>
            <p className="text-2xl font-bold text-text font-mono">{currentAnalytics.hours_saved}h</p>
          </div>
          <div className="bg-green-500/10 p-2.5 rounded-xl border border-green-500/20">
            <Clock className="w-5 h-5 text-green-400" />
          </div>
        </div>

        {/* Unique Domains */}
        <div className="bg-layer2 border border-border p-5 rounded-2xl flex items-center justify-between shadow-sm hover:border-text-dim/30 transition-colors">
          <div>
            <p className="text-text-dim text-[10px] font-bold mb-1 uppercase tracking-[0.2em]">Niche Expertise</p>
            <p className="text-2xl font-bold text-text font-mono">{currentAnalytics.unique_domains}</p>
          </div>
          <div className="bg-purple-500/10 p-2.5 rounded-xl border border-purple-500/20">
            <PieChart className="w-5 h-5 text-purple-400" />
          </div>
        </div>

        {/* Avg Quality */}
        <div className="bg-layer2 border border-border p-5 rounded-2xl flex items-center justify-between shadow-sm hover:border-text-dim/30 transition-colors">
          <div>
            <p className="text-text-dim text-[10px] font-bold mb-1 uppercase tracking-[0.2em]">Average Quality</p>
            <div className="flex items-baseline gap-1">
              <p className="text-2xl font-bold text-text font-mono">{currentAnalytics.avg_quality.toFixed(1)}</p>
              <span className="text-text-dim text-xs font-mono">/ 5.0</span>
            </div>
          </div>
          <div className="bg-blue-500/10 p-2.5 rounded-xl border border-blue-500/20">
            <Trophy className="w-5 h-5 text-blue-400" />
          </div>
        </div>
      </div>

      <div 
        onClick={() => setIsModalOpen(true)}
        onMouseEnter={() => setIsModalOpen(true)}
        onMouseLeave={() => {
          // Add a tiny delay so moving mouse directly from card to modal doesn't flicker
          setTimeout(() => {
            if (!document.querySelector('.expertise-modal-box:hover')) {
              setIsModalOpen(false)
            }
          }, 100)
        }}
        className="bg-layer2/50 p-6 rounded-3xl border border-border/50 hover:border-kira/50 hover:bg-layer2 hover:shadow-[0_0_30px_rgba(46,196,182,0.15)] cursor-pointer transition-all flex flex-col relative group overflow-hidden"
      >
        {/* Ultra-modern animated grid background (only visible on over) */}
        <div 
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" 
          style={{ 
            backgroundImage: `linear-gradient(to right, rgba(46,196,182,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(46,196,182,0.05) 1px, transparent 1px)`, 
            backgroundSize: '24px 24px' 
          }} 
        />
        <div className="absolute inset-0 bg-gradient-to-t from-layer2/80 via-transparent to-transparent pointer-events-none z-0" />

        <div className="flex items-center justify-between mb-4 relative z-10">
          <div className="flex flex-col">
             <h4 className="text-[10px] font-bold text-text uppercase tracking-[0.2em]">Expertise Map</h4>
             <span className="text-[8px] text-text-dim font-mono uppercase mt-0.5">Topological Analysis</span>
          </div>
          
          <div className="p-2 rounded-xl bg-bg text-text-dim group-hover:text-kira group-hover:bg-kira/10 border border-border group-hover:border-kira/30 transition-all flex items-center gap-2 shadow-sm group-hover:shadow-[0_0_10px_rgba(46,196,182,0.2)]">
            <span className="text-[10px] font-bold uppercase tracking-widest hidden md:inline">Tap to Expand</span>
            <ArrowUpRight size={16} className="group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </div>
        </div>

        <div className="w-full h-[250px] relative z-10 transition-transform duration-700 ease-out group-hover:scale-[1.04]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartDomainData}>
              <PolarGrid stroke="#30364D" className="opacity-50" />
              <PolarAngleAxis
                dataKey="name"
                tick={{ fill: '#64748B', fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1A1D2D', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', fontSize: '10px' }}
                formatter={(value: any, name: any, props: any) => {
                  if (!props.payload.isReal) return ['No Data', name]
                  if (name === 'Activity Volume') return [`${Math.round(value)}% Density`, 'Volume']
                  if (name === 'Skill Competence') return [`${(props.payload.skill / 100 * 5).toFixed(1)} / 5.0`, 'Skill Score']
                  return [value, name]
                }}
              />
              <Radar
                 name="Activity Volume"
                 dataKey="volume"
                 stroke="#8338EC"
                 fill="#8338EC"
                 fillOpacity={0.6}
                 isAnimationActive={false}
              />
              <Radar
                 name="Skill Competence"
                 dataKey="skill"
                 stroke="#2EC4B6"
                 fill="#2EC4B6"
                 fillOpacity={0.4}
                 isAnimationActive={false}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── EXPANDED EXPERTISE MODAL ────────────────────────────────────── */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 shrink-0">
          <div 
            className="absolute inset-0 bg-bg/90 backdrop-blur-xl animate-in fade-in duration-300"
            onClick={() => setIsModalOpen(false)}
            onMouseEnter={() => setIsModalOpen(false)}
          />
          
          <div 
            className="expertise-modal-box relative bg-layer2 border border-kira/30 w-full max-w-5xl h-[85vh] rounded-[2rem] shadow-2xl shadow-kira/10 flex flex-col md:flex-row overflow-hidden animate-in zoom-in-95 duration-300 delay-100 ease-out"
            onMouseEnter={(e) => e.stopPropagation()}
            onMouseLeave={() => setIsModalOpen(false)}
          >
            <button 
              onClick={(e) => { e.stopPropagation(); setIsModalOpen(false); }}
              className="absolute top-4 right-4 md:top-6 md:right-6 p-2 bg-layer3/80 hover:bg-kira hover:text-bg text-text-dim rounded-full transition-all z-10 border border-border"
            >
              <X size={20} />
            </button>

            {/* Modal Left pane: Large Radar Chart */}
            <div className="flex-[3] p-6 md:p-10 border-b md:border-b-0 md:border-r border-border/50 flex flex-col bg-bg/40">
              <div className="mb-6 flex items-center gap-4">
                <div className="p-3 bg-kira/10 rounded-2xl border border-kira/20 shadow-inner shadow-kira/20">
                  <Target className="w-6 h-6 text-kira" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold font-mono tracking-tight text-text">Expertise Map</h3>
                  <p className="text-[10px] text-text-dim uppercase tracking-widest mt-1">Multi-dimensional analysis</p>
                </div>
              </div>
              <p className="text-xs text-text-dim/80 mb-8 max-w-md leading-relaxed">
                A visual representation of your prompt engineering mastery. 
                Even isolated single-domain bounds form sharp spikes, highlighting localized focus.
              </p>
              
              <div className="flex-1 min-h-[300px] md:min-h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartDomainData}>
                    <PolarGrid stroke="#30364D" className="opacity-60" />
                    <PolarAngleAxis
                      dataKey="name"
                      tick={{ fill: '#E2E8F0', fontSize: 13, fontWeight: 'bold' }}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'rgba(26, 29, 45, 0.95)', backdropFilter: 'blur(10px)', borderRadius: '16px', border: '1px solid rgba(46, 196, 182, 0.3)', padding: '16px' }}
                      itemStyle={{ padding: '4px 0', fontSize: '13px', fontWeight: 'bold', fontFamily: 'monospace' }}
                      formatter={(value: any, name: any, props: any) => {
                        if (!props.payload.isReal) return ['Synthesized Baseline (Ignore)', name]
                        if (name === 'Activity Volume') return [`${Math.round(value)}% Peak Density`, 'Volume']
                        if (name === 'Skill Competence') return [`Score: ${(props.payload.skill / 100 * 5).toFixed(1)} / 5.0`, 'Skill Quotient']
                        return [value, name]
                      }}
                    />
                    <Radar
                       name="Activity Volume"
                       dataKey="volume"
                       stroke="#8338EC"
                       strokeWidth={2}
                       fill="#8338EC"
                       fillOpacity={0.5}
                       isAnimationActive={true}
                    />
                    <Radar
                       name="Skill Competence"
                       dataKey="skill"
                       stroke="#2EC4B6"
                       strokeWidth={2}
                       fill="#2EC4B6"
                       fillOpacity={0.5}
                       isAnimationActive={true}
                    />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '20px', fontFamily: 'monospace' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Modal Right pane: Interactive List */}
            <div className="w-full md:w-[380px] shrink-0 p-6 md:p-8 overflow-y-auto bg-layer2/30 flex flex-col">
              <h3 className="text-[10px] font-bold font-mono uppercase tracking-[0.2em] text-text-dim mb-6 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-kira shadow-[0_0_10px_rgba(46,196,182,0.8)] animate-pulse" />
                Domain Index
              </h3>
              
              <div className="space-y-3 flex-1 pb-10">
                {rawDomainData.length === 0 ? (
                  <div className="text-center py-10 opacity-50 font-mono text-xs">No active vectors detected.</div>
                ) : (
                  rawDomainData.map((d, i) => (
                    <div 
                      key={d.full_name}
                      onClick={(e) => {
                        e.stopPropagation()
                        onDomainSelect?.(d.full_name)
                        setIsModalOpen(false)
                      }}
                      className="group relative p-5 rounded-[1.25rem] bg-layer3/40 border border-border hover:border-kira/50 hover:bg-kira/5 cursor-pointer flex flex-col gap-3 transition-all duration-300 hover:shadow-lg hover:shadow-kira/5 overflow-hidden"
                    >
                      <div className="flex items-center justify-between z-10">
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-sm bg-bg border border-border flex items-center justify-center text-[10px] font-mono font-bold text-text-dim group-hover:text-kira transition-colors">
                            {String(i + 1).padStart(2, '0')}
                          </div>
                          <div>
                            <p className="text-sm font-bold text-text mb-0.5 group-hover:text-kira transition-colors">{d.name}</p>
                            <p className="text-[9px] text-text-dim uppercase tracking-widest font-mono">{d.raw_count} prompts</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-base font-mono font-bold text-white">{d.raw_quality.toFixed(1)}</p>
                          <p className="text-[9px] text-text-dim uppercase tracking-widest">Quotient</p>
                        </div>
                      </div>

                      {/* Micro Progress Bar inside card */}
                      <div className="w-full h-1 bg-layer2 rounded-full overflow-hidden z-10">
                        <div 
                          className="h-full bg-kira transition-all duration-1000 group-hover:bg-purple-400" 
                          style={{ width: `${d.skill}%` }}
                        />
                      </div>

                      {/* Hover glow effect */}
                      <div className="absolute inset-0 bg-gradient-to-r from-kira/0 via-kira/5 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

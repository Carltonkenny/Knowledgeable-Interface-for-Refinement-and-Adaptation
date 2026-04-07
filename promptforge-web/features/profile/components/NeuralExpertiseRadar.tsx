'use client'

import { useState, useMemo } from 'react'
import { Target, Zap, ShieldAlert, Award } from 'lucide-react'
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Tooltip } from 'recharts'
import { DomainStat } from '@/lib/api'

interface NeuralExpertiseRadarProps {
  xpTotal: number
  tier: string
  domains: DomainStat[]
}

const TIER_THRESHOLDS = {
  'Bronze': { max: 500, label: 'Analyst', color: 'from-orange-400 to-amber-600', ring: '#F59E0B' },
  'Silver': { max: 2000, label: 'Practitioner', color: 'from-gray-300 to-gray-500', ring: '#94A3B8' },
  'Gold': { max: 5000, label: 'Architect', color: 'from-yellow-300 to-yellow-600', ring: '#EAB308' },
  'Kira-Class (Forge-Master)': { max: 10000, label: 'Forge-Master', color: 'from-kira to-blue-600', ring: '#2EC4B6' }
}

// Ensure exactly 12 domains for the professional topology
const DOMAINS_LIST = [
  "Technical Architecture",
  "Full-Stack Development",
  "Data Intelligence",
  "Creative Synthesis",
  "Strategic Business",
  "Instructional Design",
  "Persona Engineering",
  "Security & Research",
  "Legal & Compliance",
  "Project Management",
  "Scientific Computing",
  "Meta-Prompting"
]

export default function NeuralExpertiseRadar({ xpTotal, tier, domains }: NeuralExpertiseRadarProps) {
  const [isHovered, setIsHovered] = useState(false)

  // Map user data to the fixed 12-point topology
  const chartData = useMemo(() => {
    return DOMAINS_LIST.map(domainName => {
      const match = domains.find(d => d.domain.toLowerCase() === domainName.toLowerCase())
      if (match) {
        return {
          name: domainName.split(" ")[0], // Short name for the label
          fullName: domainName,
          volume: match.interaction_count,
          skill: match.confidence * 100,
          isReal: true
        }
      }
      return {
        name: domainName.split(" ")[0],
        fullName: domainName,
        volume: 0,
        skill: 0,
        isReal: false
      }
    })
  }, [domains])

  const currentTierData = TIER_THRESHOLDS[tier as keyof typeof TIER_THRESHOLDS] || TIER_THRESHOLDS['Bronze']
  const nextTierMax = currentTierData.max
  const xpPercentage = Math.min(100, Math.max(0, (xpTotal / nextTierMax) * 100))
  
  // SVG Ring calculations
  const radius = 120
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (xpPercentage / 100) * circumference

  return (
    <div 
      className="bg-layer2 rounded-2xl border border-border-subtle p-6 flex flex-col h-full relative overflow-hidden group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="absolute top-0 right-0 w-64 h-64 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-kira/5 to-transparent rounded-bl-full pointer-events-none transition-opacity duration-700 opacity-50 group-hover:opacity-100" />
      
      <div className="flex items-center justify-between mb-8 z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-kira/10 text-kira shadow-inner shadow-kira/20">
            <Target size={20} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-text-bright font-mono">Neural Expertise</h2>
            <p className="text-xs text-text-dim tracking-wider uppercase">Identity Topology</p>
          </div>
        </div>
        
        {/* Tier Badge */}
        <div className={`px-4 py-1.5 rounded-full bg-gradient-to-r ${currentTierData.color} shadow-[0_0_15px_rgba(0,0,0,0.5)]`}>
          <span className="text-xs font-bold text-bg tracking-widest uppercase">{tier}</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col md:flex-row items-center justify-center gap-8 relative z-10">
        
        {/* The XP Ring + Radar Core */}
        <div className="relative w-[300px] h-[300px] flex items-center justify-center">
          
          {/* Glowing Outer Ring (SVG) */}
          <svg className="absolute inset-0 w-full h-full -rotate-90 drop-shadow-[0_0_10px_rgba(46,196,182,0.4)]">
            <circle
              cx="150"
              cy="150"
              r={radius}
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="6"
              fill="none"
            />
            <circle
              cx="150"
              cy="150"
              r={radius}
              stroke={currentTierData.ring}
              strokeWidth="6"
              fill="none"
              strokeLinecap="round"
              style={{
                strokeDasharray: circumference,
                strokeDashoffset: isHovered ? strokeDashoffset - 10 : strokeDashoffset,
                transition: "stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)"
              }}
            />
          </svg>

          {/* Core Radar Chart */}
          <div className="w-[240px] h-[240px] z-10">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
                <PolarGrid stroke="#30364D" className="opacity-40" />
                <PolarAngleAxis
                  dataKey="name"
                  tick={{ fill: '#64748B', fontSize: 9 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1A1D2D', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', fontSize: '10px' }}
                  formatter={(value: any, name: any, props: any) => {
                    if (!props.payload.isReal) return ['Empty', name]
                    if (name === 'Activity Volume') return [`${Math.round(value)} requests`, 'Volume']
                    return [value, name]
                  }}
                />
                <Radar
                   name="Activity Volume"
                   dataKey="volume"
                   stroke={currentTierData.ring}
                   fill={currentTierData.ring}
                   fillOpacity={0.4}
                   isAnimationActive={true}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          
        </div>

        {/* Data Metrics Column */}
        <div className="flex flex-col gap-6 flex-1 w-full mt-4 md:mt-0 px-4">
          <div className="bg-bg/50 border border-border/50 rounded-xl p-4 transition-all duration-300 group-hover:border-kira/30">
            <div className="flex items-center justify-between font-mono">
              <span className="text-xs text-text-dim uppercase">Total XP</span>
              <span className="text-lg font-bold text-kira">{xpTotal.toLocaleString()}</span>
            </div>
            <div className="w-full h-1 bg-layer1 rounded-full mt-3 overflow-hidden">
              <div 
                className="h-full bg-kira transition-all duration-1000 ease-out"
                style={{ width: `${xpPercentage}%` }}
              />
            </div>
            <div className="flex items-center justify-between mt-2 text-[10px] text-text-muted font-mono">
              <span>Tier Progress</span>
              <span>{nextTierMax.toLocaleString()} Limit</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-bg/50 border border-border/50 p-4 rounded-xl flex flex-col justify-center">
              <Award className="text-text-dim mb-2 h-5 w-5" />
              <span className="text-xl font-bold text-text-bright">{domains.length} / 12</span>
              <span className="text-[10px] uppercase text-text-dim mt-1">Unique Domains</span>
            </div>
            <div className="bg-bg/50 border border-border/50 p-4 rounded-xl flex flex-col justify-center">
              <Zap className="text-text-dim mb-2 h-5 w-5" />
              <span className="text-xl font-bold text-text-bright">{tier.split(' ')[0]}</span>
              <span className="text-[10px] uppercase text-text-dim mt-1">Status Clearance</span>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  )
}

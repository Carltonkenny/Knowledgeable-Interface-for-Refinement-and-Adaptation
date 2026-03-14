// features/history/components/HistoryAnalyticsDashboard.tsx
'use client'

import { Activity, Trophy, Clock, PieChart, TrendingUp } from 'lucide-react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart as RePieChart, Pie, Cell
} from 'recharts'
import type { HistoryAnalytics } from '@/lib/api'

interface HistoryAnalyticsDashboardProps {
  analytics: HistoryAnalytics | null
  isLoading: boolean
}

const COLORS = ['#2EC4B6', '#3A86FF', '#8338EC', '#FF006E', '#FB5607']

export default function HistoryAnalyticsDashboard({
  analytics,
  isLoading,
}: HistoryAnalyticsDashboardProps) {
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

  if (!analytics) return null

  // Prepare domain data for PieChart
  const pieData = Object.entries(analytics.domain_distribution)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-6 mb-10">
      {/* Top Row: Core Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Prompts */}
        <div className="bg-layer2 border border-border p-5 rounded-2xl flex items-center justify-between shadow-sm">
          <div>
            <p className="text-text-dim text-xs font-semibold mb-1 uppercase tracking-wider">Total Prompts</p>
            <p className="text-2xl font-bold text-text">{analytics.total_prompts}</p>
          </div>
          <div className="bg-kira/10 p-2.5 rounded-xl border border-kira/20">
            <Activity className="w-5 h-5 text-kira" />
          </div>
        </div>

        {/* Time Saved */}
        <div className="bg-layer2 border border-border p-5 rounded-2xl flex items-center justify-between shadow-sm">
          <div>
            <p className="text-text-dim text-xs font-semibold mb-1 uppercase tracking-wider">Hours Saved</p>
            <p className="text-2xl font-bold text-text">{analytics.hours_saved}h</p>
          </div>
          <div className="bg-green-500/10 p-2.5 rounded-xl border border-green-500/20">
            <Clock className="w-5 h-5 text-green-400" />
          </div>
        </div>

        {/* Unique Domains */}
        <div className="bg-layer2 border border-border p-5 rounded-2xl flex items-center justify-between shadow-sm">
          <div>
            <p className="text-text-dim text-xs font-semibold mb-1 uppercase tracking-wider">Active Domains</p>
            <p className="text-2xl font-bold text-text">{analytics.unique_domains}</p>
          </div>
          <div className="bg-purple-500/10 p-2.5 rounded-xl border border-purple-500/20">
            <PieChart className="w-5 h-5 text-purple-400" />
          </div>
        </div>

        {/* Avg Quality */}
        <div className="bg-layer2 border border-border p-5 rounded-2xl flex items-center justify-between shadow-sm">
          <div>
            <p className="text-text-dim text-xs font-semibold mb-1 uppercase tracking-wider">Avg Quality</p>
            <div className="flex items-baseline gap-1">
              <p className="text-2xl font-bold text-text">{analytics.avg_quality.toFixed(1)}</p>
              <span className="text-text-dim text-xs">/ 5.0</span>
            </div>
          </div>
          <div className="bg-blue-500/10 p-2.5 rounded-xl border border-blue-500/20">
            <Trophy className="w-5 h-5 text-blue-400" />
          </div>
        </div>
      </div>

      {/* Second Row: Visual Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Domain Distribution (Pie Chart) */}
        <div className="bg-layer2 border border-border p-6 rounded-3xl shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <PieChart className="w-5 h-5 text-purple-400" />
            <h3 className="font-bold text-text">Domain Distribution</h3>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RePieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1A1D2B', borderRadius: '12px', border: '1px solid #30364D' }}
                  itemStyle={{ color: '#E2E8F0' }}
                />
              </RePieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-2">
            {pieData.slice(0, 5).map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                <span className="text-[10px] font-bold text-text-dim uppercase tracking-wider">{entry.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quality Trend (Line Chart) */}
        <div className="bg-layer2 border border-border p-6 rounded-3xl shadow-sm overflow-hidden relative">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="w-5 h-5 text-kira" />
            <h3 className="font-bold text-text">Quality Evolution</h3>
          </div>
          
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.quality_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30364D" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  stroke="#64748B" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  tickFormatter={(val: string) => val.split('-').slice(1).join('/')}
                />
                <YAxis 
                  stroke="#64748B" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  domain={[0, 5]}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1A1D2B', borderRadius: '12px', border: '1px solid #30364D' }}
                  itemStyle={{ color: '#E2E8F0' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="avg_quality" 
                  stroke="#2EC4B6" 
                  strokeWidth={3} 
                  dot={{ r: 4, fill: '#2EC4B6', strokeWidth: 0 }}
                  activeDot={{ r: 6, fill: '#2EC4B6', stroke: '#1A1D2B', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

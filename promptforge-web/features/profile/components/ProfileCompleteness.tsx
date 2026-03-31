'use client'

import { Award, CheckCircle2 } from 'lucide-react'

interface ProfileCompletenessProps {
  profile: {
    bio?: string | null
    location?: string | null
    job_title?: string | null
    company?: string | null
    website?: string | null
    github?: string | null
    twitter?: string | null
    linkedin?: string | null
    avatar_url?: string | null
    phone?: string | null
  }
}

export default function ProfileCompleteness({ profile }: ProfileCompletenessProps) {
  const fields = [
    { key: 'bio', label: 'Bio', weight: 20 },
    { key: 'location', label: 'Location', weight: 10 },
    { key: 'job_title', label: 'Job Title', weight: 15 },
    { key: 'company', label: 'Company', weight: 10 },
    { key: 'website', label: 'Website', weight: 10 },
    { key: 'github', label: 'GitHub', weight: 10 },
    { key: 'twitter', label: 'Twitter', weight: 5 },
    { key: 'linkedin', label: 'LinkedIn', weight: 10 },
    { key: 'avatar_url', label: 'Avatar', weight: 10 },
  ]

  const completedFields = fields.filter(field => profile[field.key as keyof typeof profile])
  const totalScore = fields.reduce((sum, field) => sum + field.weight, 0)
  const currentScore = fields.reduce((sum, field) => {
    return sum + (profile[field.key as keyof typeof profile] ? field.weight : 0)
  }, 0)
  const percentage = Math.round((currentScore / totalScore) * 100)

  const getLevel = (pct: number) => {
    if (pct >= 90) return { label: 'All-Star', color: 'text-kira', bg: 'bg-kira/10' }
    if (pct >= 70) return { label: 'Professional', color: 'text-yellow-400', bg: 'bg-yellow-400/10' }
    if (pct >= 50) return { label: 'Intermediate', color: 'text-blue-400', bg: 'bg-blue-400/10' }
    return { label: 'Beginner', color: 'text-text-dim', bg: 'bg-layer3' }
  }

  const level = getLevel(percentage)

  return (
    <div className="bg-layer2 rounded-2xl border border-border-subtle p-5 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${level.bg} ${level.color}`}>
            <Award size={18} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-bright">Profile Strength</h3>
            <p className="text-[10px] text-text-dim uppercase tracking-wider">{level.label}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-text-bright">{percentage}%</p>
          <p className="text-[10px] text-text-dim">Complete</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-2 bg-layer3 rounded-full overflow-hidden mb-4">
        <div
          className={`h-full bg-gradient-to-r from-kira to-purple-500 transition-all duration-1000`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Field Checklist */}
      <div className="grid grid-cols-2 gap-2">
        {fields.map((field) => {
          const isComplete = !!profile[field.key as keyof typeof profile]
          return (
            <div
              key={field.key}
              className={`flex items-center gap-2 text-xs ${isComplete ? 'text-text-dim' : 'text-text-dim/50'}`}
            >
              <CheckCircle2 size={12} className={isComplete ? 'text-kira' : 'text-text-dim/30'} />
              <span>{field.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

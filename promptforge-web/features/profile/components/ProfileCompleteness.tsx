'use client'

import { Award, CheckCircle2, ArrowRight } from 'lucide-react'

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

const guidanceMessages: Record<string, string> = {
  bio: "🎯 Start with your bio — it's the fastest way to level up",
  location: "📍 Add your location for regional prompt patterns",
  job_title: "💼 What's your role? Kira adapts to your expertise level",
  company: "🏢 Where do you work? Helps with industry-specific prompts",
  website: "🌐 Got a portfolio? Link it for brand-aligned outputs",
  github: "💻 Connect GitHub so Kira learns your coding style",
  twitter: "🐦 Add Twitter for tone & communication preferences",
  linkedin: "🔗 LinkedIn helps Kira understand your professional context",
  avatar_url: "👤 Add a profile picture to personalize your experience",
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

  const emptyFields = fields.filter(field => !profile[field.key as keyof typeof profile])
  const nextAction = emptyFields[0]

  const getLevel = (pct: number) => {
    if (pct >= 90) return { label: 'All-Star', color: 'text-kira', bg: 'bg-kira/10' }
    if (pct >= 70) return { label: 'Professional', color: 'text-yellow-400', bg: 'bg-yellow-400/10' }
    if (pct >= 50) return { label: 'Intermediate', color: 'text-blue-400', bg: 'bg-blue-400/10' }
    return { label: 'Beginner', color: 'text-text-dim', bg: 'bg-layer3' }
  }

  const level = getLevel(percentage)

  const getGuidanceMessage = () => {
    if (percentage === 0) return guidanceMessages.bio
    if (percentage < 50 && nextAction) {
      return guidanceMessages[nextAction.key] || "⚡ Add more fields to reach full sync"
    }
    if (percentage < 90 && nextAction) {
      return `✨ Almost there! Add your ${nextAction.label?.toLowerCase()} to level up`
    }
    return "🎉 Profile fully synced! Kira knows everything about you"
  }

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
      <div className="h-2 bg-layer3 rounded-full overflow-hidden mb-3">
        <div
          className={`h-full bg-gradient-to-r from-kira to-purple-500 transition-all duration-1000`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Guidance Message */}
      {percentage < 100 && (
        <div className="mb-4 px-3 py-2 rounded-lg bg-kira/5 border border-kira/20 text-xs text-kira flex items-start gap-2">
          <ArrowRight size={14} className="mt-0.5 flex-shrink-0" />
          <span>{getGuidanceMessage()}</span>
        </div>
      )}

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

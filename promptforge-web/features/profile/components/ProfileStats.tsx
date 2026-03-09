// features/profile/components/ProfileStats.tsx
// What Kira knows + quality trend

interface ProfileStatsProps {
  profile: {
    primary_use: string
    audience: string
    ai_frustration: string
  } | null
  sessionCount: number
}

export default function ProfileStats({ profile, sessionCount }: ProfileStatsProps) {
  if (!profile) {
    return (
      <div className="text-center py-12">
        <p className="text-text-dim">No profile data yet.</p>
      </div>
    )
  }

  // Kira's confidence based on session count
  let confidence = "Still learning"
  let confidenceColor = "text-text-dim"
  
  if (sessionCount >= 30) {
    confidence = "High — rarely needs more"
    confidenceColor = "text-success"
  } else if (sessionCount >= 10) {
    confidence = "Getting warm"
    confidenceColor = "text-domain"
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-mono text-[10px] tracking-wider uppercase text-text-dim mb-2">
          What Kira knows
        </h3>
        
        <div className="space-y-3">
          <div>
            <span className="text-text-dim text-sm">Your main areas</span>
            <p className="text-text-bright">{profile.primary_use}</p>
          </div>
          
          <div>
            <span className="text-text-dim text-sm">Your audience</span>
            <p className="text-text-bright">{profile.audience}</p>
          </div>
          
          <div>
            <span className="text-text-dim text-sm">AI frustration</span>
            <p className="text-text-bright">{profile.ai_frustration}</p>
          </div>
          
          <div>
            <span className="text-text-dim text-sm">Kira's confidence</span>
            <p className={`${confidenceColor} font-medium`}>{confidence}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// features/profile/hooks/useProfile.ts
// Profile data + session count

'use client'

import { useState, useEffect } from 'react'
import { getSupabaseClient } from '@/lib/supabase'
import { PERSONA_DOT_THRESHOLDS } from '@/lib/constants'

interface UserProfileData {
  primary_use: string
  audience: string
  ai_frustration: string
  frustration_detail?: string
  session_count: number
  created_at: string
}

export function useProfile(userId: string) {
  const [profile, setProfile] = useState<UserProfileData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadProfile() {
      const supabase = getSupabaseClient()
      
      const { data, error } = await supabase
        .from('user_profiles')
        .select('*')
        .eq('user_id', userId)
        .maybeSingle()  // Returns null if no row exists (not 406 error)

      if (!error && data) {
        setProfile(data)
      }
      
      setIsLoading(false)
    }

    loadProfile()
  }, [userId])

  const sessionCount = profile?.session_count ?? 0

  const trustLevel: 0 | 1 | 2 = sessionCount >= PERSONA_DOT_THRESHOLDS.TUNED
    ? 2
    : sessionCount >= PERSONA_DOT_THRESHOLDS.WARM
    ? 1
    : 0

  const personaDotColor: 'cold' | 'warm' | 'tuned' =
    sessionCount >= PERSONA_DOT_THRESHOLDS.TUNED
      ? 'tuned'
      : sessionCount >= PERSONA_DOT_THRESHOLDS.WARM
      ? 'warm'
      : 'cold'

  return {
    profile,
    sessionCount,
    trustLevel,
    personaDotColor,
    isLoading,
  }
}

// promptforge-web/lib/memory/sessionManager.ts
import { getSupabaseClient } from '@/lib/supabase'

/**
 * SessionContinuityManager - handles transfer of context between chat sessions.
 */
export class SessionContinuityManager {
  /**
   * Load context from previous session to establish continuity.
   */
  static async establishSessionContinuity(sessionId: string, userId: string) {
    const previousSession = await this.getLastSession(userId, sessionId)
    if (previousSession) {
      const context = await this.getMemoryContext(previousSession.id)
      return context
    }
    return null
  }

  /**
   * Get the last active session for a user (excluding current).
   */
  private static async getLastSession(userId: string, currentSessionId: string) {
    const supabase = getSupabaseClient()
    const { data, error } = await supabase
      .from('chat_sessions')
      .select('id')
      .eq('user_id', userId)
      .neq('id', currentSessionId)
      .is('deleted_at', null)
      .order('last_activity', { ascending: false })
      .limit(1)
      .maybeSingle()

    if (error || !data) return null
    return data
  }

  /**
   * Retrieve key memory insights from a specific session history.
   */
  static async getMemoryContext(sessionId: string) {
    const supabase = getSupabaseClient()
    const { data, error } = await supabase
      .from('conversations')
      .select('message, role, message_type')
      .eq('session_id', sessionId)
      .eq('message_type', 'output')
      .order('created_at', { ascending: false })
      .limit(10)

    if (error) {
      console.warn(`[session-continuity] Failed to retrieve session context: ${error.message}`)
      return []
    }
    return data || []
  }
}

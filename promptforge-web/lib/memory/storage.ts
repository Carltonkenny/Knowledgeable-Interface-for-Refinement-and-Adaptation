// promptforge-web/lib/memory/storage.ts
import { getSupabaseClient } from '@/lib/supabase'

export interface PersistentMemory {
  id: string
  user_id: string
  content: string
  domain: string
  quality_score: number
  created_at: string
  updated_at: string
  embedding?: number[] // For vector search
}

export class MemoryStorage {
  private supabase = getSupabaseClient()

  /**
   * Store memory with vector embedding
   */
  async storeMemory(memory: Omit<PersistentMemory, 'id' | 'created_at' | 'updated_at'>) {
    const id = crypto.randomUUID()
    const now = new Date().toISOString()

    const { data, error } = await this.supabase
      .from('langmem_memories')
      .insert({
        id,
        user_id: memory.user_id,
        content: memory.content,
        domain: memory.domain,
        quality_score: memory.quality_score,
        embedding: memory.embedding,
        created_at: now,
        updated_at: now
      })
      .select()

    if (error) throw new Error(`Failed to store memory: ${error.message}`)
    return data?.[0] as PersistentMemory
  }

  /**
   * Retrieve relevant memories using semantic search.
   * Requires 'get_relevant_memories' RPC function in Supabase.
   */
  async getRelevantMemories(userId: string, query: string, limit: number = 5) {
    const { data, error } = await this.supabase
      .rpc('get_relevant_memories', {
        user_id: userId,
        query_text: query,
        limit_count: limit
      })

    if (error) {
      // Fallback to basic keyword search if RPC or vector extension is missing
      const { data: keywordData, error: keywordError } = await this.supabase
        .from('langmem_memories')
        .select('*')
        .eq('user_id', userId)
        .ilike('content', `%${query.substring(0, 30)}%`)
        .limit(limit)
      
      if (keywordError) {
        throw new Error(`Failed to retrieve memories: ${keywordError.message}`)
      }
      return (keywordData || []) as PersistentMemory[]
    }
    
    return (data || []) as PersistentMemory[]
  }
}

// promptforge-web/lib/memory/atomizer.ts
import { MemoryStorage } from './storage'

/**
 * MemoryAtomizer - processes raw input into atomic knowledge units.
 */
export class MemoryAtomizer {
  /**
   * Clean and distill raw input into atomic knowledge units via backend LLM.
   */
  static async atomizeInput(input: string, userId: string, token: string): Promise<{
    core_memories: Array<{
      content: string
      domain: string
      quality_score: number
    }>
  }> {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL
    
    const response = await fetch(`${apiUrl}/semantic-distill`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        input,
        user_id: userId
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to atomize input: ${errorText || response.statusText}`)
    }

    return await response.json()
  }

  /**
   * Store atomized memories into persistent storage.
   */
  static async storeAtomizedMemories(memories: any[], userId: string, memoryStorage: MemoryStorage) {
    for (const memory of memories) {
      await memoryStorage.storeMemory({
        user_id: userId,
        content: memory.content,
        domain: memory.domain,
        quality_score: memory.quality_score,
        // embedding: await generateEmbedding(memory.content) // Implementation deferred
      })
    }
  }
}

/**
 * Placeholder for vector embedding generation.
 * In production, this would call OpenAI/Gemini embedding API.
 */
async function generateEmbedding(text: string): Promise<number[]> {
  // Dummy embedding for now
  return Array(1536).fill(0).map(() => Math.random())
}

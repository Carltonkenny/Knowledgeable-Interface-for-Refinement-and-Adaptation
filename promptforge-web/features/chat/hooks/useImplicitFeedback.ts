/**
 * Implicit Feedback Tracking Hook
 * 
 * Tracks user behavior signals without interrupting flow.
 * Sends feedback to backend asynchronously (user never waits).
 * 
 * @packageFeatures chat
 * @RULES.md Compliance:
 * - Type hints mandatory (TypeScript strict mode)
 * - Silent fail (network errors don't break UX)
 * - No blocking operations
 * 
 * Feedback Types & Weights:
 * - copy: +0.08 (user found value - PRIMARY success signal)
 * - edit (light, <40%): +0.02 (user engaged, minor tweaks)
 * - edit (heavy, >40%): -0.03 (prompt needed work)
 * - save: +0.10 (user wants to reuse - STRONGEST signal)
 */

import { useCallback } from 'react';

interface FeedbackPayload {
  session_id: string;
  prompt_id: string;
  feedback_type: 'copy' | 'edit' | 'save';
  edit_distance?: number;
  timestamp: string;
}

/**
 * Calculate Levenshtein edit distance between two strings.
 * Used to detect how much user modified the improved prompt.
 * 
 * @param str1 - Original string
 * @param str2 - Modified string
 * @returns Edit distance (0 = identical, higher = more different)
 */
function levenshteinDistance(str1: string, str2: string): number {
  const matrix: number[][] = Array(str2.length + 1)
    .fill(null)
    .map(() => Array(str1.length + 1).fill(0));

  for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
  for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;

  for (let j = 1; j <= str2.length; j++) {
    for (let i = 1; i <= str1.length; i++) {
      if (str1[i - 1] === str2[j - 1]) {
        matrix[j][i] = matrix[j - 1][i - 1];
      } else {
        matrix[j][i] = Math.min(
          matrix[j - 1][i - 1] + 1,
          matrix[j][i - 1] + 1,
          matrix[j - 1][i] + 1
        );
      }
    }
  }

  return matrix[str2.length][str1.length];
}

/**
 * Hook for implicit feedback tracking.
 * 
 * @param sessionId - Current session ID
 * @param promptId - Current prompt ID (from response)
 * @param improvedPrompt - The improved prompt text (for edit tracking)
 * @returns Object with tracking functions
 */
export function useImplicitFeedback(
  sessionId: string,
  promptId: string | null,
  improvedPrompt: string | null
) {
  /**
   * Send feedback to backend (async, silent fail).
   */
  const sendFeedback = useCallback(async (payload: FeedbackPayload) => {
    try {
      const response = await fetch('http://localhost:8000/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Auth header added by interceptor if logged in
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        console.warn('[feedback] failed to send:', response.statusText);
      }
    } catch (error) {
      console.warn('[feedback] network error:', error);
      // Silent fail - feedback is non-critical
    }
  }, []);

  /**
   * Track when user copies the improved prompt.
   * Signal: Strong positive (+0.08 quality score)
   * 
   * RULES.md: This is the PRIMARY success metric.
   */
  const trackCopy = useCallback(() => {
    if (!promptId) return;
    
    sendFeedback({
      session_id: sessionId,
      prompt_id: promptId,
      feedback_type: 'copy',
      timestamp: new Date().toISOString(),
    });
  }, [sessionId, promptId, sendFeedback]);

  /**
   * Track when user saves the prompt to library.
   * Signal: Very strong positive (+0.10 quality score)
   * 
   * RULES.md: Strongest signal - user wants to reuse.
   */
  const trackSave = useCallback(() => {
    if (!promptId) return;
    
    sendFeedback({
      session_id: sessionId,
      prompt_id: promptId,
      feedback_type: 'save',
      timestamp: new Date().toISOString(),
    });
  }, [sessionId, promptId, sendFeedback]);

  /**
   * Track when user edits the improved prompt before copying.
   * Signal: Positive if light edit (+0.02), negative if heavy (-0.03)
   * 
   * @param edited - User's edited version
   */
  const trackEdit = useCallback((edited: string) => {
    if (!promptId || !improvedPrompt) return;
    
    const distance = levenshteinDistance(improvedPrompt, edited);
    const editRatio = improvedPrompt.length > 0 ? distance / improvedPrompt.length : 0;
    
    sendFeedback({
      session_id: sessionId,
      prompt_id: promptId,
      feedback_type: 'edit',
      edit_distance: editRatio,
      timestamp: new Date().toISOString(),
    });
  }, [sessionId, promptId, improvedPrompt, sendFeedback]);

  return {
    trackCopy,
    trackSave,
    trackEdit,
  };
}

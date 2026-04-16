// lib/errors.ts
// All errors pass through here. No component ever displays a raw error string.

import { ApiError } from './api'
import { KIRA_ERROR_MESSAGES } from './constants'

export type KiraErrorType =
  | 'network'
  | 'rate_limit'
  | 'auth'
  | 'validation'
  | 'server'
  | 'unknown'

export interface KiraError {
  type: KiraErrorType
  userMessage: string  // What Kira says in the UI — never a raw error
  retryable: boolean
}

export function mapError(err: unknown): KiraError {
  if (err instanceof ApiError) {
    if (err.status === 401 || err.status === 403) {
      return { type: 'auth', userMessage: KIRA_ERROR_MESSAGES.AUTH, retryable: false }
    }
    if (err.status === 422) {
      return { type: 'validation', userMessage: KIRA_ERROR_MESSAGES.VALIDATION, retryable: false }
    }
    if (err.status === 429) {
      return { type: 'rate_limit', userMessage: KIRA_ERROR_MESSAGES.RATE_LIMIT, retryable: true }
    }
    if (err.status >= 500) {
      return { type: 'server', userMessage: KIRA_ERROR_MESSAGES.SERVER, retryable: true }
    }
  }
  if (err instanceof TypeError && err.message === 'Failed to fetch') {
    return { type: 'network', userMessage: KIRA_ERROR_MESSAGES.NETWORK, retryable: true }
  }
  return { type: 'unknown', userMessage: KIRA_ERROR_MESSAGES.UNKNOWN, retryable: true }
}

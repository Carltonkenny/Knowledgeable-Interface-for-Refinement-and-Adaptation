// lib/logger.ts
// Centralised frontend error logging. Every caught error goes through here.
// Swap internals once when you add Sentry — no component changes needed.
//
// RULES.md Compliance:
// - Structured logging with context
// - Error serialization (handles Error objects properly)
// - Environment-aware (dev vs prod)

type LogContext = Record<string, unknown>

/**
 * Serializes error for logging (handles Error objects, preserves stack)
 */
function serializeError(error: unknown): Record<string, unknown> {
  if (!error) {
    return { message: 'Error object was null or undefined' }
  }
  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
    }
  }
  if (typeof error === 'string') {
    return { message: error }
  }
  if (typeof error === 'object') {
    // Handle API errors with status/message properties
    return {
      ...error,
      type: error?.constructor?.name || 'unknown',
    }
  }
  return { error: String(error) }
}

export const logger = {
  error(message: string, context?: LogContext, error?: unknown) {
    const serializedError = error ? serializeError(error) : {}
    const logContext = {
      ...context,
      ...serializedError,
      timestamp: new Date().toISOString(),
    }
    
    console.error('[PromptForge]', message, logContext)
    
    // Production hook — add Sentry here when ready, nothing else changes
    if (process.env.NODE_ENV === 'production') {
      // Future: Sentry.captureException(error, { extra: { message, ...context } })
    }
  },

  warn(message: string, context?: LogContext) {
    const logContext = {
      ...context,
      timestamp: new Date().toISOString(),
    }
    console.warn('[PromptForge]', message, logContext)
  },

  info(message: string, context?: LogContext) {
    const logContext = {
      ...context,
      timestamp: new Date().toISOString(),
    }
    
    if (process.env.NODE_ENV === 'development') {
      console.info('[PromptForge]', message, logContext)
    }
  },
  
  debug(message: string, context?: LogContext) {
    if (process.env.NODE_ENV === 'development') {
      console.debug('[PromptForge]', message, context ?? '')
    }
  },
}

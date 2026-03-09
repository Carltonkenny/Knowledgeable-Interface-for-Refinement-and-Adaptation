// lib/logger.ts
// Centralised frontend error logging. Every caught error goes through here.
// Swap internals once when you add Sentry — no component changes needed.

type LogContext = Record<string, unknown>

export const logger = {
  error(message: string, context?: LogContext, error?: unknown) {
    console.error('[PromptForge]', message, context ?? '', error ?? '')
    // Production hook — add Sentry here when ready, nothing else changes
    if (process.env.NODE_ENV === 'production') {
      // Future: Sentry.captureException(error, { extra: { message, ...context } })
    }
  },

  warn(message: string, context?: LogContext) {
    console.warn('[PromptForge]', message, context ?? '')
  },

  info(message: string, context?: LogContext) {
    if (process.env.NODE_ENV === 'development') {
      console.info('[PromptForge]', message, context ?? '')
    }
  },
}

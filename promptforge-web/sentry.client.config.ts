// Sentry client configuration (browser)
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  
  // Enable tracing for performance monitoring
  tracesSampleRate: 1.0, // 100% of traces in dev, reduce in prod
  
  // Enable Session Replay
  replaysSessionSampleRate: 1.0,
  replaysOnErrorSampleRate: 1.0,
  
  // Integrations
  integrations: [
    Sentry.replayIntegration({
      maskAllText: false,
      blockAllMedia: false,
    }),
  ],
  
  // Environment
  environment: process.env.NODE_ENV || 'development',
});

// Sentry client configuration (browser)
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  
  // Enable tracing for performance monitoring
  tracesSampleRate: 0.1, // 10% of traces — protects free tier quota
  
  // Enable Session Replay
  replaysSessionSampleRate: 0.1, // 10% of sessions — saves quota
  replaysOnErrorSampleRate: 1.0, // 100% of error sessions — always capture errors
  
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

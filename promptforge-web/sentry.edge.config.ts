// Sentry edge configuration (Vercel Edge Runtime)
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Enable tracing for performance monitoring
  tracesSampleRate: 0.1, // 10% of traces — protects free tier quota

  // Environment
  environment: process.env.NODE_ENV || 'production',
});

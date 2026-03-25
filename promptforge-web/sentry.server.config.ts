// Sentry server configuration (Node.js)
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  
  // Enable tracing for performance monitoring
  tracesSampleRate: 1.0, // 100% of traces in dev, reduce in prod
  
  // Environment
  environment: process.env.NODE_ENV || 'development',
});

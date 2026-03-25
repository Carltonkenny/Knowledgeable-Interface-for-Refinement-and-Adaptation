import { withSentryConfig } from "@sentry/nextjs";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default withSentryConfig(nextConfig, {
  // Sentry configuration
  org: "student-cjs",
  project: "javascript-nextjs",
  
  // Disable source map upload in development
  disableLogger: true,
  
  // Silent mode for quieter builds
  silent: true,
});

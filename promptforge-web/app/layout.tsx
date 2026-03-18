// app/layout.tsx
// Root layout — Server component
// Imports globals.css, sets metadata

import '@/styles/globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'PromptForge — Prompt intelligence for serious work',
  description: 'Kira learns how you think. Every session, your prompts get sharper.',
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning data-scroll-behavior="smooth">
      <body suppressHydrationWarning>{children}</body>
    </html>
  )
}

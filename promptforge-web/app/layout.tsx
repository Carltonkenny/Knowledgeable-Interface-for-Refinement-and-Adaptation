// app/layout.tsx
// Root layout — Server component
// Imports globals.css, sets metadata

import '@/styles/globals.css'
import type { Metadata } from 'next'
import { Toaster } from 'sonner'

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
      <body suppressHydrationWarning>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-kira focus:text-white focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-kira-light"
        >
          Skip to main content
        </a>
        {children}
        <Toaster 
          position="bottom-right"
          duration={4000}
          closeButton
          theme="dark"
          toastOptions={{
            style: {
              background: 'var(--layer-2)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-bright)',
              fontFamily: 'monospace',
              fontSize: '13px',
            },
          }}
        />
      </body>
    </html>
  )
}

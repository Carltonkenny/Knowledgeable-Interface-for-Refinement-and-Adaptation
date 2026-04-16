// features/landing/components/BottomCTA.tsx
// Bottom CTA section with interactive buttons
// Client Component — buttons have onClick handlers

'use client'

import { Button } from '@/components/ui'
import { ROUTES } from '@/lib/constants'

export function BottomCTA() {
  return (
    <section className="py-24 md:py-32 px-5 md:px-12 relative">
      <div className="gradient-line absolute top-0 left-[10%] right-[10%]" />

      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-kira/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-4xl mx-auto text-center relative z-10">
        <h2 className="text-[28px] md:text-[36px] font-bold tracking-tight text-text-bright mb-4">
          Ready to engineer better prompts?
        </h2>
        <p className="text-[14px] md:text-[15px] text-text-dim mb-8 max-w-xl mx-auto">
          Join developers and power users who get sharper results every day.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-5">
          <Button
            variant="primary"
            size="lg"
            className="btn-glow glow-kira w-full sm:w-auto"
            onClick={() => (window.location.href = ROUTES.SIGNUP)}
          >
            Get started free →
          </Button>
        </div>
        <p className="font-mono text-[10px] text-text-dim">
          Also available as MCP for Cursor and Claude Desktop
        </p>
      </div>
    </section>
  )
}

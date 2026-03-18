// features/landing/components/PricingSection.tsx
// Free + Pro (COMING SOON) cards
// Server component

'use client'

import { Button } from '@/components/ui'
import { ROUTES } from '@/lib/constants'

export function PricingSection() {
  return (
    <section id="pricing" className="py-16 px-12 border-t border-border-subtle">
      <div className="max-w-4xl mx-auto">
        {/* Eyebrow */}
        <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4">
          // 05  Pricing
        </p>

        {/* Title */}
        <h2 className="text-[28px] font-bold tracking-tight text-text-bright mb-4">
          Simple. Honest. Free tier is real.
        </h2>

        {/* Cards */}
        <div className="grid grid-cols-2 gap-6 mt-10">
          {/* FREE card */}
          <div className="border border-border-default rounded-xl bg-layer1 p-6">
            <span className="font-mono text-[10px] tracking-wider uppercase text-text-dim">
              FREE
            </span>
            <p className="text-[36px] font-bold text-text-bright mt-2 mb-6">$0</p>

            <ul className="space-y-3 mb-8">
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-success">✓</span>
                Unlimited prompt improvement
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-success">✓</span>
                Kira orchestration
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-success">✓</span>
                Quality scoring
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-success">✓</span>
                Profile building
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-success">✓</span>
                Basic memory
              </li>
            </ul>

            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={() => (window.location.href = ROUTES.SIGNUP)}
            >
              Start free
            </Button>
            <p className="font-mono text-[10px] text-text-dim text-center mt-3">
              No credit card. Genuinely useful.
            </p>
          </div>

          {/* PRO card (COMING SOON) */}
          <div className="border border-kira rounded-xl bg-[var(--kira-glow)] p-6 relative">
            {/* COMING SOON badge */}
            <div className="absolute top-4 right-4">
              <span className="font-mono text-[9px] tracking-wider uppercase text-[var(--coming)] bg-[var(--coming-dim)] border border-[var(--coming)] px-2 py-0.5 rounded">
                COMING SOON
              </span>
            </div>

            <span className="font-mono text-[10px] tracking-wider uppercase text-text-dim">
              PRO
            </span>
            <div className="mt-2 mb-1">
              <span className="text-[36px] font-bold text-text-bright opacity-50">$20</span>
              <span className="text-[13px] text-text-dim opacity-50"> /month</span>
            </div>
            <p className="font-mono text-[9px] text-text-dim mb-6">Coming soon</p>

            <ul className="space-y-3 mb-8">
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-kira">✦</span>
                Everything in Free
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-kira">✦</span>
                Prompt history library
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-kira">✦</span>
                MCP (Cursor / Claude Desktop)
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-kira">✦</span>
                Push Further variants ✦
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-kira">✦</span>
                Full profile depth
              </li>
              <li className="text-[13px] text-text-default flex items-center gap-2">
                <span className="text-kira">✦</span>
                Priority queue
              </li>
            </ul>

            <Button
              variant="waitlist"
              size="lg"
              className="w-full"
              onClick={() => {}}
            >
              Join Pro waitlist →
            </Button>
            <p className="font-mono text-[10px] text-text-dim text-center mt-3">
              Free forever until Pro launches.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

// features/landing/components/PricingSection.tsx
// Glass pricing cards with glow hover + gradient border on Pro
// Client Component — buttons have onClick handlers

'use client'

import { Button } from '@/components/ui'
import { ROUTES } from '@/lib/constants'

const FREE_FEATURES = [
  'Unlimited prompt improvement',
  'Kira orchestration',
  'Quality scoring',
  'Profile building',
  'Basic memory',
]

const PRO_FEATURES = [
  'Everything in Free',
  'Prompt history library',
  'MCP (Cursor / Claude Desktop)',
  'Push Further variants ✦',
  'Full profile depth',
  'Priority queue',
]

export function PricingSection() {
  return (
    <section id="pricing" className="py-20 md:py-28 px-5 md:px-12 relative">
      <div className="gradient-line absolute top-0 left-[10%] right-[10%]" />

      <div className="max-w-4xl mx-auto">
        {/* Eyebrow */}
        <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4 animate-fade-in-up">
          // 05  Pricing
        </p>

        {/* Title */}
        <h2 className="text-[24px] md:text-[28px] font-bold tracking-tight text-text-bright mb-4 animate-fade-in-up animate-stagger-1">
          Simple. Honest. Free tier is real.
        </h2>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-10">
          {/* FREE card */}
          <div className="glass-card p-6 md:p-8 animate-fade-in-up animate-stagger-2">
            <span className="font-mono text-[10px] tracking-wider uppercase text-text-dim">
              FREE
            </span>
            <p className="text-[36px] md:text-[42px] font-bold text-text-bright mt-2 mb-6">$0</p>

            <ul className="space-y-3 mb-8">
              {FREE_FEATURES.map((f) => (
                <li key={f} className="text-[13px] text-text-default flex items-center gap-2.5">
                  <span className="text-success text-sm">✓</span>
                  {f}
                </li>
              ))}
            </ul>

            <Button
              variant="primary"
              size="lg"
              className="w-full btn-glow"
              onClick={() => (window.location.href = ROUTES.SIGNUP)}
            >
              Start free
            </Button>
            <p className="font-mono text-[10px] text-text-dim text-center mt-3">
              No credit card. Genuinely useful.
            </p>
          </div>

          {/* PRO card */}
          <div className="glass-card glass-card-active p-6 md:p-8 relative overflow-hidden animate-fade-in-up animate-stagger-3">
            {/* Gradient shimmer on border */}
            <div className="absolute inset-0 rounded-2xl pointer-events-none"
              style={{
                background: 'linear-gradient(135deg, rgba(99,102,241,0.08) 0%, transparent 50%, rgba(139,92,246,0.06) 100%)',
              }}
            />

            {/* COMING SOON badge */}
            <div className="absolute top-4 right-4 z-10">
              <span className="font-mono text-[9px] tracking-wider uppercase text-[var(--coming)] bg-[var(--coming-dim)] border border-[var(--coming)]/30 px-2.5 py-1 rounded-md">
                COMING SOON
              </span>
            </div>

            <div className="relative z-10">
              <span className="font-mono text-[10px] tracking-wider uppercase text-text-dim">
                PRO
              </span>
              <div className="mt-2 mb-1">
                <span className="text-[36px] md:text-[42px] font-bold text-text-bright opacity-50">$20</span>
                <span className="text-[13px] text-text-dim opacity-50"> /month</span>
              </div>
              <p className="font-mono text-[9px] text-text-dim mb-6">Coming soon</p>

              <ul className="space-y-3 mb-8">
                {PRO_FEATURES.map((f) => (
                  <li key={f} className="text-[13px] text-text-default flex items-center gap-2.5">
                    <span className="text-kira text-sm">✦</span>
                    {f}
                  </li>
                ))}
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
      </div>
    </section>
  )
}

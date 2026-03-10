// features/landing/components/HeroSection.tsx
// Hero section with headline, subhead, CTAs, LiveDemoWidget
// 'use client' — contains interactive demo widget

'use client'

import { Button } from '@/components/ui'
import { ROUTES } from '@/lib/constants'
import { LiveDemoWidget } from './LiveDemoWidget'

export function HeroSection() {
  return (
    <section
      id="hero"
      className="relative min-h-screen flex flex-col items-center justify-center pt-20 px-6"
      style={{
        background: `
          radial-gradient(ellipse 70% 50% at 15% 0%, rgba(99,102,241,0.10) 0%, transparent 60%),
          radial-gradient(ellipse 50% 40% at 85% 100%, rgba(139,92,246,0.07) 0%, transparent 60%),
          radial-gradient(ellipse 30% 30% at 5% 60%, rgba(236,72,153,0.04) 0%, transparent 50%)
        `,
      }}
    >
      {/* Eyebrow */}
      <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-6">
        // the prompt intelligence layer
      </p>

      {/* H1 */}
      <h1 className="text-[56px] md:text-[56px] text-[36px] font-bold tracking-tight text-text-bright leading-[1.05] text-center mb-6">
        Your prompts,
        <br />
        <em className="gradient-text">precisely</em> engineered.
      </h1>

      {/* Sub */}
      <p className="text-[17px] text-text-dim font-light leading-[1.7] text-center max-w-2xl mb-10">
        Kira learns how you think. The more you use it, the better it serves you.
        Switching away means starting over.
      </p>

      {/* CTAs */}
      <div className="flex items-center gap-4 mb-16">
        <Button
          variant="primary"
          size="lg"
          onClick={() => (window.location.href = ROUTES.SIGNUP)}
        >
          Start for free
        </Button>
        <Button
          variant="ghost"
          size="lg"
          onClick={() => {
            document.getElementById('live-demo')?.scrollIntoView({ behavior: 'smooth' })
          }}
        >
          Watch it work ↓
        </Button>
      </div>

      {/* Live Demo Widget */}
      <div id="live-demo">
        <LiveDemoWidget />
      </div>
    </section>
  )
}

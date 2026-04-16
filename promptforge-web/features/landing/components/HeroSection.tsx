// features/landing/components/HeroSection.tsx
// Premium hero with aurora mesh, animated gradient text, stats bar, LiveDemoWidget
// Client Component — buttons have onClick handlers

'use client'

import { Button } from '@/components/ui'
import { ROUTES } from '@/lib/constants'
import { LiveDemoWidget } from './LiveDemoWidget'

const HERO_STATS = [
  { value: '500+', label: 'prompts engineered daily' },
  { value: '4.2s', label: 'avg response time' },
  { value: '99.9%', label: 'uptime' },
]

export function HeroSection() {
  return (
    <section
      id="hero"
      className="relative min-h-screen flex flex-col items-center justify-center pt-20 pb-10 px-5 md:px-6 overflow-hidden"
    >
      {/* Aurora background */}
      <div className="aurora-bg">
        <div className="aurora-orb aurora-orb-1" />
        <div className="aurora-orb aurora-orb-2" />
        <div className="aurora-orb aurora-orb-3" />
      </div>

      {/* Content — sits above aurora */}
      <div className="relative z-10 flex flex-col items-center">
        {/* Eyebrow */}
        <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] md:text-[11px] mb-6 opacity-80">
          // the prompt intelligence layer
        </p>

        {/* H1 */}
        <h1 className="text-[36px] md:text-[56px] lg:text-[64px] font-bold tracking-tight text-text-bright leading-[1.05] text-center mb-6">
          Your prompts,
          <br />
          <em className="gradient-text not-italic">precisely</em> engineered.
        </h1>

        {/* Sub */}
        <p className="text-[15px] md:text-[17px] text-text-dim font-light leading-[1.7] text-center max-w-2xl mb-10">
          Kira learns how you think. Every session, your prompts get sharper.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center gap-4 mb-12">
          <Button
            variant="primary"
            size="lg"
            className="btn-glow glow-kira w-full sm:w-auto"
            onClick={() => (window.location.href = ROUTES.SIGNUP)}
          >
            Start for free
          </Button>
          <Button
            variant="ghost"
            size="lg"
            className="w-full sm:w-auto"
            onClick={() => {
              document.getElementById('live-demo')?.scrollIntoView({ behavior: 'smooth' })
            }}
          >
            Watch it work ↓
          </Button>
        </div>

        {/* Stats bar */}
        <div className="flex flex-wrap items-center justify-center gap-6 md:gap-10 mb-16">
          {HERO_STATS.map((stat, i) => (
            <div key={i} className="flex items-center gap-3">
              {i > 0 && <span className="hidden md:block w-px h-8 bg-border-default" />}
              <div className={`text-center ${i > 0 ? 'md:pl-4' : ''}`}>
                <span className="block font-mono text-xl md:text-2xl font-bold text-text-bright">
                  {stat.value}
                </span>
                <span className="block font-mono text-[10px] text-text-dim tracking-wider uppercase">
                  {stat.label}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Live Demo Widget */}
        <div id="live-demo" className="w-full max-w-2xl">
          <LiveDemoWidget />
        </div>
      </div>
    </section>
  )
}

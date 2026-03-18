// app/(marketing)/page.tsx
// Landing page — Client Component (has interactive CTA button)

'use client'

import { LandingNav } from '@/features/landing/components/LandingNav'
import { HeroSection } from '@/features/landing/components/HeroSection'
import { KiraVoiceSection } from '@/features/landing/components/KiraVoiceSection'
import { HowItWorksSection } from '@/features/landing/components/HowItWorksSection'
import { MoatSection } from '@/features/landing/components/MoatSection'
import { PricingSection } from '@/features/landing/components/PricingSection'
import { LandingFooter } from '@/features/landing/components/LandingFooter'
import { ScrollRevealProvider } from '@/features/landing/components/ScrollRevealProvider'
import { Button } from '@/components/ui'
import { ROUTES } from '@/lib/constants'

function BottomCTA() {
  return (
    <section className="py-20 px-12 border-t border-border-subtle">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-[36px] font-bold tracking-tight text-text-bright mb-4">
          Ready to engineer better prompts?
        </h2>
        <p className="text-[15px] text-text-dim mb-8 max-w-xl mx-auto">
          Join developers and power users who get sharper results every day.
        </p>
        <div className="flex items-center justify-center gap-4 mb-4">
          <Button
            variant="primary"
            size="lg"
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

export default function LandingPage() {
  return (
    <>
      <ScrollRevealProvider />
      <LandingNav />
      <main>
        <HeroSection />
        <KiraVoiceSection />
        <HowItWorksSection />
        <MoatSection />
        <PricingSection />
        <BottomCTA />
      </main>
      <LandingFooter />
    </>
  )
}

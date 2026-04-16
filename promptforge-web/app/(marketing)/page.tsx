// app/(marketing)/page.tsx
// Landing page — Server Component
// Premium glassmorphism redesign with all sections
// Performance: Server-rendered HTML paints instantly, only interactive parts (LiveDemoWidget, LandingNav) are client components

import { LandingNav } from '@/features/landing/components/LandingNav'
import { HeroSection } from '@/features/landing/components/HeroSection'
import { KiraVoiceSection } from '@/features/landing/components/KiraVoiceSection'
import { SocialProofSection } from '@/features/landing/components/SocialProofSection'
import { HowItWorksSection } from '@/features/landing/components/HowItWorksSection'
import { IntegrationsSection } from '@/features/landing/components/IntegrationsSection'
import { MoatSection } from '@/features/landing/components/MoatSection'
import { PricingSection } from '@/features/landing/components/PricingSection'
import { FAQSection } from '@/features/landing/components/FAQSection'
import { LandingFooter } from '@/features/landing/components/LandingFooter'
import { BottomCTA } from '@/features/landing/components/BottomCTA'

export default function LandingPage() {
  return (
    <>
      {/* Grain overlay for texture */}
      <div className="grain-overlay" />

      <LandingNav />
      <main id="main-content">
        <HeroSection />
        <KiraVoiceSection />
        <SocialProofSection />
        <HowItWorksSection />
        <IntegrationsSection />
        <MoatSection />
        <PricingSection />
        <FAQSection />
        <BottomCTA />
      </main>
      <LandingFooter />
    </>
  )
}

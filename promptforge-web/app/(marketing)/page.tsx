// app/(marketing)/page.tsx
// Landing page — SERVER COMPONENT (no 'use client')
// Assembles all section components

import { LandingNav } from '@/features/landing/components/LandingNav'
import { HeroSection } from '@/features/landing/components/HeroSection'
import { KiraVoiceSection } from '@/features/landing/components/KiraVoiceSection'
import { HowItWorksSection } from '@/features/landing/components/HowItWorksSection'
import { MoatSection } from '@/features/landing/components/MoatSection'
import { PricingSection } from '@/features/landing/components/PricingSection'
import { LandingFooter } from '@/features/landing/components/LandingFooter'
import { ScrollRevealProvider } from '@/features/landing/components/ScrollRevealProvider'

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
      </main>
      <LandingFooter />
    </>
  )
}

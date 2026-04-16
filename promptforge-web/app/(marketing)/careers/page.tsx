// app/(marketing)/careers/page.tsx
// Careers — Coming Soon placeholder

import { LandingNav } from '@/features/landing/components/LandingNav'
import { LandingFooter } from '@/features/landing/components/LandingFooter'

export const metadata = {
  title: 'Careers — PromptForge',
  description: 'Join the PromptForge team. We\'re building the prompt intelligence layer.',
}

export default function CareersPage() {
  return (
    <>
      <div className="grain-overlay" />
      <LandingNav />
      <main className="pt-24 pb-16 px-5 md:px-12 min-h-screen flex items-center justify-center">
        <div className="max-w-lg w-full text-center">
          <div className="glass-card p-10 md:p-14">
            <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-kira/10 border border-kira/20 flex items-center justify-center">
              <span className="text-3xl">🚀</span>
            </div>
            <h1 className="text-[28px] md:text-[32px] font-bold tracking-tight text-text-bright mb-3">
              Careers
            </h1>
            <p className="gradient-text-static font-mono text-[12px] tracking-wider uppercase mb-6">
              Coming Soon
            </p>
            <p className="text-[14px] text-text-dim leading-relaxed mb-4">
              We&apos;re a small team building something big. When we&apos;re hiring, 
              you&apos;ll find openings here.
            </p>
            <p className="text-[13px] text-text-muted mb-8">
              Interested? Reach out at <span className="text-kira">careers@promptforge.dev</span>
            </p>
            <a
              href="/"
              className="inline-block text-[14px] text-kira hover:text-kira-light transition-colors"
            >
              ← Back to PromptForge
            </a>
          </div>
        </div>
      </main>
      <LandingFooter />
    </>
  )
}

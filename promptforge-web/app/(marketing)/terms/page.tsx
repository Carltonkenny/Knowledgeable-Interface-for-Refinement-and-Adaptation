// app/(marketing)/terms/page.tsx
// Terms & Conditions placeholder

import { LandingNav } from '@/features/landing/components/LandingNav'
import { LandingFooter } from '@/features/landing/components/LandingFooter'

export const metadata = {
  title: 'Terms & Conditions — PromptForge',
  description: 'PromptForge terms and conditions of service.',
}

const SECTIONS = [
  {
    title: '1. Acceptance of Terms',
    content: 'By accessing and using PromptForge ("the Service"), you accept and agree to be bound by these Terms and Conditions. If you do not agree to these terms, please do not use the Service.',
  },
  {
    title: '2. Description of Service',
    content: 'PromptForge is an AI-powered prompt engineering platform that improves and refines user prompts using a multi-agent system. The Service includes prompt improvement, quality scoring, profile building, and memory features.',
  },
  {
    title: '3. User Accounts',
    content: 'You must create an account to use the full features of PromptForge. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.',
  },
  {
    title: '4. Acceptable Use',
    content: 'You agree not to use the Service for any unlawful purpose, to generate harmful or abusive content, to attempt to reverse-engineer the system, or to circumvent any security measures or rate limits.',
  },
  {
    title: '5. Intellectual Property',
    content: 'Your prompts and content remain your property. PromptForge does not claim ownership of any content you submit. The Service, including its software, design, and documentation, is protected by intellectual property laws.',
  },
  {
    title: '6. Data and Privacy',
    content: 'Your use of the Service is also governed by our Privacy Policy. We store your data securely using industry-standard encryption and Row Level Security policies. We do not sell or share your personal data with third parties.',
  },
  {
    title: '7. Service Availability',
    content: 'We strive to maintain 99.9% uptime but do not guarantee uninterrupted access. We reserve the right to modify, suspend, or discontinue the Service at any time with reasonable notice.',
  },
  {
    title: '8. Limitation of Liability',
    content: 'PromptForge is provided "as is" without warranties of any kind. We shall not be liable for any indirect, incidental, or consequential damages arising from your use of the Service.',
  },
  {
    title: '9. Changes to Terms',
    content: 'We may update these Terms from time to time. We will notify registered users of material changes via email. Continued use of the Service after changes constitutes acceptance of the updated Terms.',
  },
  {
    title: '10. Contact',
    content: 'For questions about these Terms, please contact us at legal@promptforge.dev (placeholder).',
  },
]

export default function TermsPage() {
  return (
    <>
      <div className="grain-overlay" />
      <LandingNav />
      <main className="pt-24 pb-16 px-5 md:px-12 min-h-screen">
        <div className="max-w-3xl mx-auto">
          <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4">
            // Legal
          </p>
          <h1 className="text-[32px] md:text-[42px] font-bold tracking-tight text-text-bright mb-4">
            Terms &amp; Conditions
          </h1>
          <p className="text-[13px] text-text-dim mb-12">
            Last updated: April 2026
          </p>

          <div className="space-y-8">
            {SECTIONS.map((s) => (
              <section key={s.title} className="glass-card p-6">
                <h2 className="text-[16px] font-semibold text-text-bright mb-3">{s.title}</h2>
                <p className="text-[14px] text-text-dim leading-relaxed">{s.content}</p>
              </section>
            ))}
          </div>

          <div className="mt-12 text-center">
            <a href="/" className="text-[14px] text-kira hover:text-kira-light transition-colors">
              ← Back to PromptForge
            </a>
          </div>
        </div>
      </main>
      <LandingFooter />
    </>
  )
}

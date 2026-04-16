// app/(marketing)/privacy/page.tsx
// Privacy Policy placeholder

import { LandingNav } from '@/features/landing/components/LandingNav'
import { LandingFooter } from '@/features/landing/components/LandingFooter'

export const metadata = {
  title: 'Privacy Policy — PromptForge',
  description: 'How PromptForge collects, uses, and protects your data.',
}

const SECTIONS = [
  {
    title: '1. Information We Collect',
    content: 'We collect information you provide when creating an account (email, name), prompts you submit for improvement, profile data built from your usage patterns (domains, writing style, preferences), and basic analytics data (page views, feature usage).',
  },
  {
    title: '2. How We Use Your Information',
    content: 'We use your data to provide and improve the Service, build your personalized Kira profile, deliver quality scoring and prompt improvement, send service-related communications, and improve our AI models and user experience.',
  },
  {
    title: '3. Data Storage and Security',
    content: 'All data is stored in Supabase with 38 Row Level Security (RLS) policies ensuring user-level data isolation. Embeddings are stored using pgvector with 768-dimensional Gemini embeddings. All connections use TLS encryption.',
  },
  {
    title: '4. Data Sharing',
    content: 'We do not sell, rent, or share your personal data with third parties. We may share anonymized, aggregated data for analytical purposes. We use Sentry for error tracking (no PII transmitted).',
  },
  {
    title: '5. Your Rights',
    content: 'You have the right to access your personal data, request correction of inaccurate data, request deletion of your data, export your data, and opt out of non-essential data collection.',
  },
  {
    title: '6. Data Retention',
    content: 'We retain your data for as long as your account is active. Profile and memory data is retained to provide continuity across sessions. You can request full data deletion at any time through the Danger Zone in your profile settings.',
  },
  {
    title: '7. Cookies',
    content: 'We use essential cookies for authentication and session management. We do not use advertising or tracking cookies. See our Cookie Policy for full details.',
  },
  {
    title: '8. Third-Party Services',
    content: 'We use the following third-party services: Supabase (database and authentication), Sentry (error monitoring), and LLM providers (prompt processing). Each has their own privacy policies.',
  },
  {
    title: "9. Children's Privacy",
    content: 'PromptForge is not intended for children under 13. We do not knowingly collect personal information from children.',
  },
  {
    title: '10. Changes to This Policy',
    content: 'We may update this Privacy Policy periodically. We will notify registered users of material changes. Continued use constitutes acceptance.',
  },
  {
    title: '11. Contact',
    content: 'For privacy-related inquiries, contact us at privacy@promptforge.dev (placeholder).',
  },
]

export default function PrivacyPage() {
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
            Privacy Policy
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

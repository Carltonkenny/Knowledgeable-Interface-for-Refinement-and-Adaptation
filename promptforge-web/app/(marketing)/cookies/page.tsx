// app/(marketing)/cookies/page.tsx
// Cookie Policy placeholder

import { LandingNav } from '@/features/landing/components/LandingNav'
import { LandingFooter } from '@/features/landing/components/LandingFooter'

export const metadata = {
  title: 'Cookie Policy — PromptForge',
  description: 'How PromptForge uses cookies and similar technologies.',
}

const COOKIES = [
  {
    name: 'sb-access-token',
    purpose: 'Authentication — stores your Supabase session token',
    type: 'Essential',
    duration: 'Session',
  },
  {
    name: 'sb-refresh-token',
    purpose: 'Authentication — refreshes your session when it expires',
    type: 'Essential',
    duration: '7 days',
  },
  {
    name: 'pf_session_id',
    purpose: 'Session tracking — links your chat to your conversation',
    type: 'Essential',
    duration: 'Session',
  },
  {
    name: 'pf_demo_uses',
    purpose: 'Demo gate — tracks how many demo prompts you\'ve used',
    type: 'Functional',
    duration: 'Persistent',
  },
  {
    name: 'pf_newsletter',
    purpose: 'Newsletter — remembers if you\'ve already subscribed',
    type: 'Functional',
    duration: 'Persistent',
  },
]

export default function CookiePage() {
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
            Cookie Policy
          </h1>
          <p className="text-[13px] text-text-dim mb-12">
            Last updated: April 2026
          </p>

          {/* Overview */}
          <section className="glass-card p-6 mb-8">
            <h2 className="text-[16px] font-semibold text-text-bright mb-3">What are cookies?</h2>
            <p className="text-[14px] text-text-dim leading-relaxed">
              Cookies are small text files stored on your device when you visit a website. 
              PromptForge uses only essential and functional cookies — we do not use any 
              advertising, tracking, or third-party marketing cookies.
            </p>
          </section>

          {/* Cookie table */}
          <section className="glass-card p-6 mb-8 overflow-x-auto">
            <h2 className="text-[16px] font-semibold text-text-bright mb-4">Cookies we use</h2>
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="text-left py-3 pr-4 text-text-dim font-mono text-[10px] uppercase tracking-wider">Name</th>
                  <th className="text-left py-3 pr-4 text-text-dim font-mono text-[10px] uppercase tracking-wider">Purpose</th>
                  <th className="text-left py-3 pr-4 text-text-dim font-mono text-[10px] uppercase tracking-wider">Type</th>
                  <th className="text-left py-3 text-text-dim font-mono text-[10px] uppercase tracking-wider">Duration</th>
                </tr>
              </thead>
              <tbody>
                {COOKIES.map((c) => (
                  <tr key={c.name} className="border-b border-border-subtle last:border-0">
                    <td className="py-3 pr-4 font-mono text-kira text-[12px]">{c.name}</td>
                    <td className="py-3 pr-4 text-text-default">{c.purpose}</td>
                    <td className="py-3 pr-4 text-text-dim">{c.type}</td>
                    <td className="py-3 text-text-dim">{c.duration}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {/* Managing cookies */}
          <section className="glass-card p-6 mb-8">
            <h2 className="text-[16px] font-semibold text-text-bright mb-3">Managing cookies</h2>
            <p className="text-[14px] text-text-dim leading-relaxed">
              You can manage cookies through your browser settings. Note that disabling essential 
              cookies may prevent you from using PromptForge&apos;s authentication features. 
              Since we only use essential and functional cookies, there is no cookie consent 
              banner — these cookies are required for the Service to function.
            </p>
          </section>

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

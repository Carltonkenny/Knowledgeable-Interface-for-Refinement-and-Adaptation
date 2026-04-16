// features/landing/components/LandingFooter.tsx
// Multi-column footer with newsletter, social links, legal pages
// Server Component — newsletter form extracted to NewsletterForm client component

import { NewsletterForm } from './NewsletterForm'

const FOOTER_LINKS = {
  Product: [
    { label: 'How it works', href: '#how-it-works' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'Live Demo', href: '#live-demo' },
    { label: 'Changelog', href: '#' },
  ],
  Company: [
    { label: 'About', href: '/about' },
    { label: 'Blog', href: '/blog' },
    { label: 'Careers', href: '/careers' },
  ],
  Legal: [
    { label: 'Terms & Conditions', href: '/terms' },
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Cookie Policy', href: '/cookies' },
  ],
}

const SOCIAL_LINKS = [
  { label: 'GitHub', icon: '⌘', href: '#' },
  { label: 'X / Twitter', icon: '𝕏', href: '#' },
  { label: 'Discord', icon: '⬡', href: '#' },
]

export function LandingFooter() {
  return (
    <footer className="relative pt-20 pb-8 px-5 md:px-12">
      {/* Top gradient line */}
      <div className="gradient-line absolute top-0 left-[10%] right-[10%]" />

      <div className="max-w-6xl mx-auto">
        {/* Main footer grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 md:gap-12 mb-16">
          {/* Brand column */}
          <div className="col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <span className="text-xl">⬡</span>
              <span className="font-display font-bold text-text-bright text-base">
                PromptForge
              </span>
            </div>
            <p className="text-[13px] text-text-dim leading-relaxed mb-6 max-w-xs">
              Stateful vector memory for Large Language Models. Engineered for complex architectures.
            </p>

            {/* Social links */}
            <div className="flex items-center gap-3">
              {SOCIAL_LINKS.map((s) => (
                <a
                  key={s.label}
                  href={s.href}
                  aria-label={s.label}
                  className="w-9 h-9 rounded-lg glass flex items-center justify-center text-text-dim hover:text-text-bright hover:border-border-bright transition-all duration-200"
                >
                  <span className="text-sm">{s.icon}</span>
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([category, links]) => (
            <div key={category}>
              <p className="font-mono text-[10px] tracking-wider uppercase text-text-dim mb-4">
                {category}
              </p>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-[13px] text-text-dim hover:text-text-bright transition-colors duration-200"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Newsletter */}
        <div className="glass-card p-6 md:p-8 mb-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <h3 className="text-[15px] font-semibold text-text-bright mb-1">
                Stay in the loop
              </h3>
              <p className="text-[13px] text-text-dim">
                Quarterly engineering updates and architectural insights. No spam.
              </p>
            </div>

            <NewsletterForm />
          </div>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-6 border-t border-border-subtle">
          <p className="font-mono text-[10px] text-text-dim">
            © 2026 PromptForge. All rights reserved.
          </p>
          <p className="font-mono text-[10px] text-text-muted">
            Engineered by Carlton Kenny.
          </p>
        </div>
      </div>
    </footer>
  )
}

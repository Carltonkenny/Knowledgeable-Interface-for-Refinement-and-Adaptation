// features/landing/components/LandingFooter.tsx
// Simple footer with logo, links, legal
// Server component

export function LandingFooter() {
  return (
    <footer className="py-12 px-12 border-t border-border-subtle">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="text-xl">⬡</span>
            <span className="font-display font-bold text-text-dim text-sm">
              PromptForge
            </span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-4">
              <span className="font-mono text-[10px] tracking-wider uppercase text-text-dim">
                Product
              </span>
              <a href="#how-it-works" className="text-[12px] text-text-dim hover:text-text-bright transition-colors">
                How it works
              </a>
              <a href="#pricing" className="text-[12px] text-text-dim hover:text-text-bright transition-colors">
                Pricing
              </a>
            </div>

            <div className="flex items-center gap-4">
              <span className="font-mono text-[10px] tracking-wider uppercase text-text-dim">
                Legal
              </span>
              <a href="#" className="text-[12px] text-text-dim hover:text-text-bright transition-colors">
                Privacy
              </a>
              <a href="#" className="text-[12px] text-text-dim hover:text-text-bright transition-colors">
                Terms
              </a>
            </div>
          </div>

          {/* Copyright */}
          <p className="font-mono text-[10px] text-text-dim">
            © 2026 PromptForge
          </p>
        </div>
      </div>
    </footer>
  )
}

// features/landing/components/LandingNav.tsx
// Top nav with logo + CTAs
// Scroll-aware: transparent at top, frosted on scroll

'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui'
import { ROUTES } from '@/lib/constants'

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-200 ${
        scrolled
          ? 'backdrop-blur-md bg-bg/90 border-b border-border-subtle'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">⬡</span>
          <span className="font-display font-bold text-text-bright text-lg">
            PromptForge
          </span>
        </div>

        {/* Nav links — desktop */}
        <div className="hidden md:flex items-center gap-8">
          <a
            href="#how-it-works"
            className="text-sm text-text-default hover:text-text-bright transition-colors"
          >
            How it works
          </a>
          <a
            href="#pricing"
            className="text-sm text-text-default hover:text-text-bright transition-colors"
          >
            Pricing
          </a>
        </div>

        {/* CTAs */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => (window.location.href = ROUTES.LOGIN)}>
            Sign in
          </Button>
          <Button variant="primary" size="sm" onClick={() => (window.location.href = ROUTES.SIGNUP)}>
            Start free →
          </Button>
        </div>
      </div>
    </nav>
  )
}

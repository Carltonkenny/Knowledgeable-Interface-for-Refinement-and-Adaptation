// features/landing/components/NewsletterForm.tsx
// Client component for the newsletter subscription form in the footer
// Extracted from LandingFooter to allow footer to be a Server Component

'use client'

import { useState } from 'react'

export function NewsletterForm() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !email.includes('@')) return

    setStatus('loading')
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/newsletter/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, source: 'footer' })
      })

      if (!response.ok) throw new Error('Failed to subscribe')

      setStatus('success')
      setEmail('')
      // Store in localStorage to not re-show
      localStorage.setItem('pf_newsletter', 'subscribed')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'success') {
    return (
      <p className="font-mono text-[13px] text-success flex items-center gap-2">
        <span>✓</span> You&apos;re in! We&apos;ll keep you posted.
      </p>
    )
  }

  return (
    <form onSubmit={handleSubscribe} className="flex gap-2 w-full md:w-auto" suppressHydrationWarning>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="your@email.com"
        className="flex-1 md:w-64 px-4 py-2.5 rounded-lg bg-white/5 border border-border-default text-text-bright text-[13px] placeholder:text-text-muted focus:outline-none focus:border-kira/40 transition-colors"
        required
        suppressHydrationWarning
      />
      <button
        type="submit"
        disabled={status === 'loading'}
        className="px-5 py-2.5 rounded-lg bg-kira text-white text-[13px] font-medium btn-glow hover:bg-kira-light transition-colors disabled:opacity-50"
        suppressHydrationWarning
      >
        {status === 'loading' ? '...' : 'Subscribe'}
      </button>
    </form>
  )
}

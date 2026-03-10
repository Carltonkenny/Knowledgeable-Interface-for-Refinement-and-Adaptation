// features/landing/hooks/useScrollReveal.ts
// IntersectionObserver for .reveal elements
// Adds .visible class when element enters viewport

'use client'

import { useEffect } from 'react'

export function useScrollReveal() {
  useEffect(() => {
    if (typeof window === 'undefined') return

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const elements = document.querySelectorAll<HTMLElement>('.reveal')

    if (prefersReduced) {
      elements.forEach(el => el.classList.add('visible'))
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
            observer.unobserve(entry.target) // fire once only
          }
        })
      },
      { threshold: 0.15 }
    )

    elements.forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])
}

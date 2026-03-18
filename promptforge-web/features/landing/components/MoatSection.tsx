// features/landing/components/MoatSection.tsx
// Profile accumulation bars (the moat)
// Server component
'use client'

import { motion } from 'framer-motion'

export function MoatSection() {
  return (
    <section className="py-16 px-12 border-t border-border-subtle">
      <div className="max-w-4xl mx-auto">
        {/* Eyebrow */}
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4"
        >
          // 04  The moat
        </motion.p>

        {/* Title */}
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-[28px] font-bold tracking-tight text-text-bright mb-4"
        >
          Kira gets smarter every time.
        </motion.h2>

        {/* Sub */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="text-[15px] text-text-dim mb-10 max-w-2xl"
        >
          Most AI tools forget you the moment you close the tab. Kira remembers your domains, your style, your preferences. The more you use it, the better it gets.
        </motion.p>

        {/* Card */}
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="border border-border-default rounded-xl bg-[var(--surface-card)] p-6 shadow-card"
        >
          {/* Progress rows */}
          <div className="space-y-4">
            {/* Domain confidence */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[13px] text-text-default">Domain confidence</span>
                <span className="font-mono text-[10px] text-kira">B2B SaaS — 91%</span>
              </div>
              <div className="h-2 bg-border-default rounded-full overflow-hidden">
                <div className="h-full bg-kira rounded-full" style={{ width: '91%' }} />
              </div>
            </div>

            {/* Tone calibration */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[13px] text-text-default">Tone calibration</span>
                <span className="font-mono text-[10px] text-context">Direct, technical</span>
              </div>
              <div className="h-2 bg-border-default rounded-full overflow-hidden">
                <div className="h-full bg-context rounded-full" style={{ width: '78%' }} />
              </div>
            </div>

            {/* Quality trend */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[13px] text-text-default">Quality trend</span>
                <span className="font-mono text-[10px] text-success">↑ 34% this month</span>
              </div>
              <div className="h-2 bg-border-default rounded-full overflow-hidden">
                <div className="h-full bg-success rounded-full" style={{ width: '65%' }} />
              </div>
            </div>

            {/* Clarification rate */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[13px] text-text-default">Clarification rate</span>
                <span className="font-mono text-[10px] text-domain">Rarely needs more</span>
              </div>
              <div className="h-2 bg-border-default rounded-full overflow-hidden">
                <div className="h-full bg-domain rounded-full" style={{ width: '20%' }} />
              </div>
            </div>
          </div>

          {/* Footer */}
          <p className="font-mono text-[10px] text-text-dim mt-6 pt-4 border-t border-border-subtle">
            This lives in your profile.{' '}
            <span className="text-text-bright font-semibold">
              The more you use Kira, the better she gets.
            </span>
          </p>
        </motion.div>
      </div>
    </section>
  )
}

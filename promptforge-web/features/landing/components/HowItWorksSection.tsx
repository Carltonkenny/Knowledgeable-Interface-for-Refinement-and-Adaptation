// features/landing/components/HowItWorksSection.tsx
// 5-step pipeline with agent chips
// Server component — no state needed

'use client'

import { Chip } from '@/components/ui'
import { motion } from 'framer-motion'

const steps = [
  {
    num: '01',
    chips: [{ variant: 'kira' as const, label: 'Reading context', active: false, skipped: false }],
    title: 'Reads your message + profile',
    desc: 'One fast call. Decides what\'s needed.',
  },
  {
    num: '02',
    chips: [
      { variant: 'intent' as const, label: 'Analyzing intent', active: false, skipped: false },
      { variant: 'context' as const, label: 'Context', active: false, skipped: false },
      { variant: 'domain' as const, label: 'Domain', active: false, skipped: false },
    ],
    title: 'Three specialists, in parallel',
    desc: 'Some skip if Kira already knows your domain.',
    note: 'Gets faster as Kira learns you',
  },
  {
    num: '03',
    chips: [{ variant: 'engineer' as const, label: 'Crafting prompt', active: false, skipped: false }],
    title: 'Prompt Engineer synthesizes everything',
    desc: 'All signals combined into one precise output.',
  },
  {
    num: '04',
    chips: [],
    title: 'You see exactly what changed and why',
    desc: 'Diff view. Quality scores. Annotation chips.',
  },
  {
    num: '05',
    chips: [],
    title: 'Kira remembers. Next time is faster.',
    desc: 'Profile dot moves grey → amber → green.',
  },
]

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-16 px-12 border-t border-border-subtle">
      <div className="max-w-4xl mx-auto">
        {/* Eyebrow */}
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4"
        >
          // 03  How it works
        </motion.p>

        {/* Title */}
        <motion.h2 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-[28px] font-bold tracking-tight text-text-bright mb-4"
        >
          Five steps. Four seconds.
        </motion.h2>

        {/* Sub */}
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="text-[13px] text-text-dim mb-10"
        >
          Honest about latency. Transparent about depth.
        </motion.p>

        {/* Steps */}
        <div className="space-y-0">
          {steps.map((step, index) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`
                flex items-start gap-6 py-6
                ${index < steps.length - 1 ? 'border-b border-border-subtle' : ''}
              `}
            >
              {/* Step number */}
              <span className="font-mono text-[10px] tracking-wider text-text-dim w-8 flex-shrink-0 pt-1">
                {step.num}
              </span>

              {/* Content */}
              <div className="flex-1">
                {/* Chips row */}
                {step.chips.length > 0 && (
                  <div className="flex items-center gap-2 mb-3 flex-wrap">
                    {step.chips.map((chip, i) => (
                      <Chip
                        key={i}
                        variant={chip.variant}
                        active={chip.active}
                        skipped={chip.skipped}
                      >
                        {chip.label}
                      </Chip>
                    ))}
                  </div>
                )}

                {/* Title */}
                <h3 className="text-[15px] font-semibold text-text-bright mb-1">
                  {step.title}
                </h3>

                {/* Description */}
                <p className="text-[13px] text-text-dim">
                  {step.desc}
                </p>

                {/* Note */}
                {step.note && (
                  <p className="font-mono text-[10px] text-text-dim mt-2">
                    {step.note}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

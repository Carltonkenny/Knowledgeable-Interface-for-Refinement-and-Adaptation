// features/landing/components/FAQSection.tsx
// Accordion FAQ with glass panels and smooth expand/collapse

'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'

const FAQS = [
  {
    q: 'How is this different from Custom GPTs?',
    a: "Custom GPTs rely on loose, static system prompts. PromptForge operates via deterministic agent routing. Every message passes through our 4-node swarm (Intent, Context, Domain, Synthesizer) guaranteeing explicit, structured execution rather than best-effort conversational responses.",
  },
  {
    q: 'How much context does the system actually retain?',
    a: "Instead of overwhelming the LLM context window with raw chat history, we use semantic pruning. We extract only explicit preferences, tech stacks, and domain heuristics, storing them in a pgvector database. This injected context stays incredibly dense and stays under token limits.",
  },
  {
    q: 'Does this rewrite my code or just my prompts?',
    a: "PromptForge is strictly a prompt-engineering layer. It synthesizes and optimizes your instructions so you can pass them into your primary IDE (Cursor, Copilot, or Claude Desktop). We engineer the blueprint; your IDE handles the codegen.",
  },
  {
    q: 'What is the "Kira" persona?',
    a: "Kira isn't a conversational bot—it is the unified interface overlay for our stateful memory engine. It abstracts away the multi-agent routing so you experience a consistent, low-latency development partner instead of a raw settings dashboard.",
  },
  {
    q: 'How does the stateful memory progress mapping work?',
    a: "The 'Profile Matrix' evaluates context density. Cold (Grey) indicates generic domain logic. Warm (Amber) triggers when standard frameworks/preferences are recognized. Tuned (Green) activates when Kira possesses enough zero-shot context to bypass boilerplate clarification questions entirely.",
  },
  {
    q: 'What is MCP integration?',
    a: 'MCP (Model Context Protocol) allows us to expose PromptForge directly as a tool inside your IDE. You will be able to query the Kira engine without leaving your local environment. This is actively in development for the Pro tier.',
  },
  {
    q: 'Is my proprietary code data safe?',
    a: 'Absolutely. We enforce strict multi-tenant isolation via 38 Supabase Row Level Security (RLS) policies. Your vectors and prompts are encrypted at rest and never utilized for model training. See our Privacy Policy for SOC2-aligned guidelines.',
  },
  {
    q: 'Is the core logic really free?',
    a: "Yes. The Free tier permits unlimited baseline prompt optimization, the complete 4-agent swarm orchestration, and profile state retention. Power-user features—like unlimited MCP calls and extended vector limits—will be packaged in the upcoming Pro tier.",
  },
]

function FAQItem({ q, a, isOpen, onToggle }: { q: string; a: string; isOpen: boolean; onToggle: () => void }) {
  return (
    <div className="glass-card overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-5 md:p-6 text-left group"
        suppressHydrationWarning
      >
        <span className="text-[14px] md:text-[15px] font-medium text-text-bright pr-4 group-hover:text-kira-light transition-colors">
          {q}
        </span>
        <span
          className={`text-text-dim text-lg flex-shrink-0 transition-transform duration-300 ${
            isOpen ? 'rotate-45' : ''
          }`}
        >
          +
        </span>
      </button>
      <div className={`faq-content ${isOpen ? 'open' : ''}`}>
        <div>
          <p className="text-[13px] text-text-dim leading-relaxed px-5 md:px-6 pb-5 md:pb-6">
            {a}
          </p>
        </div>
      </div>
    </div>
  )
}

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  return (
    <section className="py-20 md:py-28 px-5 md:px-12 relative">
      <div className="gradient-line absolute top-0 left-[10%] right-[10%]" />

      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4">
            // FAQ
          </p>
          <h2 className="text-[24px] md:text-[28px] font-bold tracking-tight text-text-bright">
            Questions? Answers.
          </h2>
        </motion.div>

        {/* FAQ items */}
        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05, duration: 0.4 }}
            >
              <FAQItem
                q={faq.q}
                a={faq.a}
                isOpen={openIndex === i}
                onToggle={() => setOpenIndex(openIndex === i ? null : i)}
              />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

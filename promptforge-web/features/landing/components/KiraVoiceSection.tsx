// features/landing/components/KiraVoiceSection.tsx
// 3-card voice progression slider (Session 1, 15, 40+)
// 'use client' — card selection state

'use client'

import { useState } from 'react'

type SessionCard = {
  session: string
  dotColor: string
  dotLabel: string
  label: string
  quote: string
}

const cards: SessionCard[] = [
  {
    session: 'SESSION 1',
    dotColor: 'var(--dot-cold)',
    dotLabel: 'GREY — Cold',
    label: 'Cold',
    quote: "Before I engineer this — what's the context? A project update, a performance conversation, or something else?",
  },
  {
    session: 'SESSION 15',
    dotColor: 'var(--dot-warm)',
    dotLabel: 'AMBER — Warm',
    label: 'Warm',
    quote: "Running it as internal comms — that's your pattern. Project update or something higher stakes?",
  },
  {
    session: 'SESSION 40+',
    dotColor: 'var(--dot-tuned)',
    dotLabel: 'GREEN — Tuned',
    label: 'Tuned',
    quote: "On it. B2B SaaS internal update — your usual territory. Your specificity has been sharp lately, keeping this tight.",
  },
]

export function KiraVoiceSection() {
  const [activeCard, setActiveCard] = useState(1) // Card 2 (Session 15) default active

  return (
    <section id="kira-voice" className="py-16 px-12 border-t border-border-subtle">
      <div className="max-w-4xl mx-auto">
        {/* Eyebrow */}
        <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4">
          // 02  Meet Kira
        </p>

        {/* Title */}
        <h2 className="text-[28px] font-bold tracking-tight text-text-bright mb-4">
          Not a chatbot.
          <br />
          A collaborator that learns your voice.
        </h2>

        {/* Sub */}
        <p className="text-[13px] text-text-dim mb-10 max-w-2xl">
          The same prompt. Three different stages. Same personality — different depth.
        </p>

        {/* Cards */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {cards.map((card, index) => {
            const isActive = index === activeCard
            return (
              <div
                key={card.session}
                onClick={() => setActiveCard(index)}
                className={`
                  rounded-xl p-5 cursor-pointer transition-all duration-150
                  ${isActive
                    ? 'border-kira bg-[var(--kira-glow)]'
                    : 'border-border-default bg-layer1 hover:border-border-bright'
                  }
                `}
              >
                {/* Session label */}
                <p className="font-mono text-[9px] tracking-wider uppercase text-text-dim mb-3">
                  {card.session}
                </p>

                {/* Dot + Label */}
                <div className="flex items-center gap-2 mb-4">
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: card.dotColor }}
                  />
                  <span
                    className="font-mono text-[10px]"
                    style={{ color: card.dotColor }}
                  >
                    ● {card.label}
                  </span>
                </div>

                {/* Quote */}
                <p className="text-[13px] text-text-default leading-relaxed italic">
                  "{card.quote}"
                </p>
              </div>
            )
          })}
        </div>

        {/* Footnote */}
        <p className="font-mono text-[10px] text-text-dim text-center">
          She reads your profile before every response. The more you use it, the less you explain.
        </p>
      </div>
    </section>
  )
}

// features/landing/components/MoatSection.tsx
// Profile accumulation metrics with animated glass card + CSS progress bars
// Server Component — no Framer Motion, progress bars use CSS animation

const metrics = [
  { label: 'Domain vector confidence', value: 'B2B SaaS — 91%', percent: 91, color: 'var(--kira)' },
  { label: 'Architectural alignment', value: 'Microservices, Event-driven', percent: 78, color: 'var(--context)' },
  { label: 'System prompt hit-rate', value: '↑ 34% this month', percent: 65, color: 'var(--success)' },
  { label: 'Manual context overhead', value: 'Down to 12%', percent: 12, color: 'var(--error)' },
]

export function MoatSection() {
  return (
    <section className="py-20 md:py-28 px-5 md:px-12 relative overflow-hidden">
      <div className="absolute -right-[20%] top-[40%] text-[#0B0D14] font-mono text-[200px] leading-none opacity-50 select-none z-0">
         MEMORY
      </div>
      <div className="gradient-line absolute top-0 left-[10%] right-[10%]" />

      <div className="max-w-4xl mx-auto relative z-10">
        {/* Eyebrow */}
        <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4 animate-fade-in-up">
          // 04  Stateful Memory
        </p>

        {/* Title */}
        <h2 className="text-[24px] md:text-[32px] font-bold tracking-tight text-text-bright mb-4 animate-fade-in-up animate-stagger-1">
          Zero-shot amnesia eliminated.
        </h2>

        {/* Sub */}
        <p className="text-[14px] md:text-[15px] text-text-dim mb-10 max-w-2xl leading-relaxed animate-fade-in-up animate-stagger-2">
          Traditional AI tools start from absolute zero on every request. PromptForge utilizes a continuous
          <span className="text-text-bright tracking-wide"> pgvector </span> embedding layer to map your
          coding habits, infrastructure preferences, and syntax styles over time.
        </p>

        {/* Glass metrics card */}
        <div className="glass-card p-6 md:p-8 animate-fade-in-up animate-stagger-3">
          <div className="space-y-6 flex flex-col pt-2">
            {metrics.map((m, i) => (
              <div key={m.label}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[13px] font-mono text-text-muted">{m.label}</span>
                  <span className="font-mono text-[10px]" style={{ color: m.color }}>
                    {m.value}
                  </span>
                </div>
                <div className="h-1.5 bg-black/40 rounded-full overflow-hidden border border-border-default/30 shadow-inner">
                  <div
                    className="h-full rounded-full shadow-[0_0_10px_currentColor] progress-fill"
                    style={{
                      width: `${m.percent}%`,
                      backgroundColor: m.color,
                      transitionDelay: `${i * 0.15}s`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="mt-8 pt-4 border-t border-border-subtle flex justify-between items-center">
             <p className="font-mono text-[9px] text-text-dim uppercase tracking-widest">
               Vector Database Synchronization
             </p>
             <div className="flex items-center gap-2">
               <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
               <span className="font-mono text-[9px] text-success">ONLINE</span>
             </div>
          </div>
        </div>
      </div>
    </section>
  )
}

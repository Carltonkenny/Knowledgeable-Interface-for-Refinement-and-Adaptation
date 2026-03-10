// features/landing/components/MoatSection.tsx
// Profile accumulation bars (the moat)
// Server component

export function MoatSection() {
  return (
    <section className="py-16 px-12 border-t border-border-subtle">
      <div className="max-w-4xl mx-auto">
        {/* Eyebrow */}
        <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4 reveal">
          // 04  The moat
        </p>

        {/* Title */}
        <h2 className="text-[28px] font-bold tracking-tight text-text-bright mb-4 reveal reveal-delay-1">
          The longer you use it,
          <br />
          the more it costs to leave.
        </h2>

        {/* Card */}
        <div className="border border-border-default rounded-xl bg-layer1 p-6 reveal reveal-delay-2">
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
              Switching away means starting over.
            </span>
          </p>
        </div>
      </div>
    </section>
  )
}

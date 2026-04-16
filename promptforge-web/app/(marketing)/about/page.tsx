import { LandingNav } from '@/features/landing/components/LandingNav'
import { LandingFooter } from '@/features/landing/components/LandingFooter'

export const metadata = {
  title: 'Creator — PromptForge',
  description: 'Built by Carlton Kenny.',
}

const VALUES = [
  { icon: '🎯', title: 'Precision over volume', desc: 'One great prompt beats ten mediocre ones.' },
  { icon: '🧠', title: 'Memory matters', desc: 'AI should learn from you, not forget you.' },
  { icon: '🔍', title: 'Transparency always', desc: 'See exactly what changed and why. No black boxes.' },
  { icon: '⚡', title: 'Velocity without compromise', desc: '4 agents, 4 seconds. Quality at speed.' },
]

export default function AboutPage() {
  return (
    <>
      <div className="grain-overlay" />
      <LandingNav />
      <main className="pt-24 pb-24 px-5 md:px-12 min-h-screen relative overflow-hidden">
        
        {/* Background glow lines */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-kira/10 rounded-full blur-[150px] pointer-events-none" />
        <div className="absolute top-[40%] left-0 w-[400px] h-[600px] bg-kira/5 rounded-[100%] blur-[120px] pointer-events-none skew-y-12" />

        <div className="max-w-3xl mx-auto relative z-10">
          
          {/* Manifesto Header */}
          <section className="mb-24 pt-12">
            <p 
              className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-6 flex items-center gap-3 animate-in fade-in slide-in-from-bottom-2 duration-700 fill-mode-both"
            >
              <span className="w-8 h-px bg-kira/50" />
              Manifesto
            </p>
            <h1 
              className="text-[36px] md:text-[52px] font-bold tracking-tight text-text-bright mb-8 leading-[1.1] animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100 fill-mode-both"
            >
              Building the prompt
              <br />
              intelligence layer.
            </h1>
            <p 
              className="text-[16px] md:text-[18px] text-text-dim leading-relaxed max-w-2xl font-light animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200 fill-mode-both"
            >
              Prompt engineering should not be a repetitive chore of copy-pasting context. It should be a systemic, stateful operation managed by agents that learn how you work.
            </p>
          </section>

          {/* Timeline Connector Container */}
          <div className="relative pl-6 md:pl-12 border-l border-border-default/50 space-y-24 pb-12">

            {/* Section 1: The Idea (Why) */}
            <section className="relative pt-12 pb-24">
              <div className="absolute -left-[29px] md:-left-[53px] top-16 w-3 h-3 rounded-full bg-kira shadow-[0_0_20px_rgba(99,102,241,1)]" />
              
              <div className="space-y-20">
                {/* Header Block */}
                <div>
                  <h2 className="text-[14px] font-mono uppercase tracking-[4px] text-kira mb-6">01 // The Core Fracture</h2>
                  <h3 className="text-[32px] md:text-[54px] font-bold text-text-bright leading-[1.1] max-w-3xl">
                    Generative AI has a profound,<br/>
                    terminal illness. <span className="text-text-muted">It forgets.</span>
                  </h3>
                </div>

                {/* Narrative & Data Block */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 md:gap-16">
                  {/* Left: The Narrative Story */}
                  <div className="lg:col-span-7 space-y-6">
                     <p className="text-[16px] md:text-[19px] text-text-dim leading-relaxed font-light">
                       Every time you open a new tab, the LLM starts from absolute zero. It forgets your technology stack. It ignores your stylistic nuances. It abandons your domain rules.
                     </p>
                     <p className="text-[16px] md:text-[19px] text-text-dim leading-relaxed font-light">
                       The industry calls this "prompt iteration," but in reality, it's a repetitive, exhausting cognitive loop. You are forced to re-explain your context just to get a baseline acceptable output from the smartest neural networks on earth.
                     </p>
                     <p className="text-[16px] md:text-[19px] text-text-bright leading-relaxed font-medium mt-8 border-l-2 border-kira pl-6 py-2 bg-layer2/30">
                       We built PromptForge because we realized the "Productivity Paradox." The time saved by AI was being entirely consumed by the overhead of managing the AI's context.
                     </p>
                  </div>
                  
                  {/* Right: The Brutalist Data */}
                  <div className="lg:col-span-5 flex flex-col gap-6">
                    {/* Data Point 1 */}
                    <div className="glass-card p-8 border-error/30 bg-error/5 relative overflow-hidden group">
                      <div className="absolute top-0 left-0 w-1 h-full bg-error" />
                      <span className="font-mono text-[56px] text-error font-bold leading-none block mb-3 opacity-90 group-hover:scale-105 origin-left transition-transform">
                        23m
                      </span>
                      <p className="text-[13px] font-mono uppercase tracking-widest text-text-bright mb-2">
                        The Recovery Tax
                      </p>
                      <p className="text-[14px] text-text-muted leading-relaxed">
                        Data from UC Irvine demonstrates it takes exactly 23 minutes and 15 seconds to regain deep focus after stopping to reconstruct context.
                      </p>
                    </div>

                    {/* Data Point 2 */}
                    <div className="glass-card p-8 border-warning/30 bg-warning/5 relative overflow-hidden group">
                      <div className="absolute top-0 left-0 w-1 h-full bg-warning" />
                      <div className="flex items-start gap-4">
                         <span className="font-mono text-[42px] text-warning font-bold leading-none block opacity-90 group-hover:scale-105 origin-left transition-transform -mt-1">
                           +19%
                         </span>
                         <div>
                            <p className="text-[13px] font-mono uppercase tracking-widest text-text-bright mb-2 mt-1">
                              Slower Execution
                            </p>
                            <p className="text-[14px] text-text-muted leading-relaxed">
                              Recent 2025 workflows prove experienced developers take 19% longer completing tasks due to the hidden drag of prompt maintenance.
                            </p>
                         </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Conclusion Hook */}
                <div className="pt-8 border-t border-border-default/50">
                  <h3 className="text-[26px] font-semibold text-text-bright">We built PromptForge to end the loop.</h3>
                  <p className="text-[16px] font-mono text-kira mt-2">Prompts are code. They should be stateful, versioned, and injected.</p>
                </div>
              </div>
            </section>

            {/* Section 2: The Execution (How) */}
            <section className="relative">
              <div className="absolute -left-[29px] md:-left-[53px] top-1 w-3 h-3 rounded-full bg-border-bright" />
              <h2 className="text-[12px] font-mono uppercase tracking-widest text-text-muted mb-3">02 / The Architecture</h2>
              <h3 className="text-[22px] font-semibold text-text-bright mb-4">Deterministic Swarm Routing</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="glass-card p-6 group hover:border-kira/30 transition-all">
                  <div className="w-10 h-10 rounded-lg bg-kira/10 border border-kira/20 flex items-center justify-center mb-4">
                    <span className="font-mono text-kira text-[16px]">01</span>
                  </div>
                  <h4 className="text-[15px] font-medium text-text-bright mb-2">Semantic Pruning</h4>
                  <p className="text-[13px] text-text-dim leading-relaxed">
                    Instead of appending raw chat history to context windows, we extract core logic into a pgvector database.
                  </p>
                </div>
                <div className="glass-card p-6 group hover:border-kira/30 transition-all">
                  <div className="w-10 h-10 rounded-lg bg-kira/10 border border-kira/20 flex items-center justify-center mb-4">
                    <span className="font-mono text-kira text-[16px]">02</span>
                  </div>
                  <h4 className="text-[15px] font-medium text-text-bright mb-2">Multi-Agent Sync</h4>
                  <p className="text-[13px] text-text-dim leading-relaxed">
                    User inputs are processed in parallel by Intent, Context, and Domain specialists before final synthesis.
                  </p>
                </div>
              </div>
            </section>

            {/* Section 3: Benchmarks */}
            <section className="relative">
              <div className="absolute -left-[29px] md:-left-[53px] top-1 w-3 h-3 rounded-full bg-success/80 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
              <h2 className="text-[12px] font-mono uppercase tracking-widest text-text-muted mb-3">03 / Benchmarks</h2>
              <h3 className="text-[22px] font-semibold text-text-bright mb-4">Speed vs. Quality Metrics</h3>
              
              <div className="glass-card overflow-hidden">
                <div className="grid grid-cols-2 divide-x divide-y divide-border-default md:grid-cols-4 md:divide-y-0">
                  <div className="p-6 flex flex-col items-center text-center">
                    <span className="font-mono text-[24px] text-kira mb-1">0.4s</span>
                    <span className="text-[11px] uppercase tracking-wider text-text-muted">Context Retrieval</span>
                  </div>
                  <div className="p-6 flex flex-col items-center text-center">
                    <span className="font-mono text-[24px] text-success mb-1">94%</span>
                    <span className="text-[11px] uppercase tracking-wider text-text-muted">Zero-Shot Prev</span>
                  </div>
                  <div className="p-6 flex flex-col items-center text-center">
                    <span className="font-mono text-[24px] text-text-bright mb-1">4.2x</span>
                    <span className="text-[11px] uppercase tracking-wider text-text-muted">Iteration Speed</span>
                  </div>
                  <div className="p-6 flex flex-col items-center text-center">
                    <span className="font-mono text-[24px] text-warning mb-1">&lt;10ms</span>
                    <span className="text-[11px] uppercase tracking-wider text-text-muted">Edge Latency</span>
                  </div>
                </div>
              </div>
            </section>

            {/* Section 4: The Architect */}
            <section className="relative pt-8">
              <h2 className="text-[12px] font-mono uppercase tracking-widest text-text-muted mb-6">04 / The Architect</h2>
              
              <div className="glass-card p-6 md:p-8 flex flex-col md:flex-row items-start gap-8 relative overflow-hidden group">
                 {/* Accent glow line inside card */}
                 <div className="absolute left-0 top-0 bottom-0 w-1 bg-kira shadow-[0_0_15px_rgba(99,102,241,0.5)]" />

                 {/* Avatar */}
                 <div className="flex-shrink-0">
                    <div className="w-24 h-24 rounded-2xl bg-layer2 border border-border-default flex items-center justify-center relative shadow-lg overflow-hidden">
                       <span className="text-3xl font-bold font-mono text-kira relative z-10 group-hover:scale-110 transition-transform">CK</span>
                       <div className="absolute inset-0 bg-kira/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                 </div>

                 {/* Bio & Links */}
                 <div className="flex-1">
                    <h3 className="text-[20px] font-bold text-text-bright mb-1">Carlton Kenny</h3>
                    <p className="text-[13px] font-mono text-kira mb-4">Software Engineer & AI Architect</p>
                    <p className="text-[13px] text-text-dim leading-relaxed mb-6 max-w-lg">
                      Obsessed with building tools that bridge the gap between human intent and machine execution. PromptForge is my answer to the ephemeral nature of AI developer tools.
                    </p>
                    
                    {/* Social Footprint */}
                    <div className="flex flex-wrap items-center gap-4">
                       <a href="#" className="flex items-center gap-2 px-4 py-2 bg-layer2 hover:bg-bg border border-border-subtle hover:border-kira/50 rounded-lg transition-all text-[12px] text-text-bright font-medium group">
                         <svg className="w-4 h-4 text-text-muted group-hover:text-kira transition-colors" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" /></svg>
                         GitHub
                       </a>
                       <a href="#" className="flex items-center gap-2 px-4 py-2 bg-layer2 hover:bg-bg border border-border-subtle hover:border-kira/50 rounded-lg transition-all text-[12px] text-text-bright font-medium group">
                         <svg className="w-4 h-4 text-text-muted group-hover:text-kira transition-colors" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" clipRule="evenodd" /></svg>
                         LinkedIn
                       </a>
                       <a href="#" className="flex items-center gap-2 px-4 py-2 bg-layer2 hover:bg-bg border border-border-subtle hover:border-kira/50 rounded-lg transition-all text-[12px] text-text-bright font-medium group">
                         <span className="w-4 h-4 flex items-center justify-center text-text-muted group-hover:text-kira transition-colors text-[14px]">🌐</span>
                         Portfolio
                       </a>
                    </div>
                 </div>
              </div>
            </section>

          </div>

          {/* CTA */}
          <div className="text-center pt-16 mt-8 border-t border-border-subtle">
            <h2 className="text-[20px] font-semibold text-text-bright mb-6">Ready to see it in action?</h2>
            <a
              href="/"
              className="inline-block px-8 py-3 rounded-lg bg-kira text-white text-[13px] font-bold font-mono uppercase tracking-wider btn-glow hover:bg-kira-light transition-colors"
            >
              Return Home
            </a>
          </div>
        </div>
      </main>
      <LandingFooter />
    </>
  )
}

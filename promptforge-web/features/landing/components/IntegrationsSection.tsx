// features/landing/components/IntegrationsSection.tsx
// Ecosystem grid showing MCP integration with major IDEs
// Server Component — CSS animations replace Framer Motion scroll reveals

const INTEGRATIONS = [
  { name: 'Cursor', desc: 'IDE native support via MCP layer.', icon: '⚡', gridClass: 'md:col-start-1 md:row-start-1' },
  { name: 'GitHub Copilot', desc: 'Injected context for Copilot Chat.', icon: '🐙', gridClass: 'md:col-start-3 md:row-start-1' },
  { name: 'Claude Desktop', desc: 'Read/Write access for system prompts.', icon: '🧠', gridClass: 'md:col-start-1 md:row-start-2' },
  { name: 'Antigravity', desc: 'Secure agentic framework.', icon: '🛸', gridClass: 'md:col-start-3 md:row-start-2' },
  { name: 'Qwen Matrix', desc: 'Deep reasoning context sync.', icon: '⚛️', gridClass: 'md:col-start-1 md:row-start-3' },
  { name: 'OpenCode IDE', desc: 'Open source local architecture.', icon: '💻', gridClass: 'md:col-start-3 md:row-start-3' },
]

export function IntegrationsSection() {
  return (
    <section className="py-24 md:py-32 px-5 md:px-12 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-kira/5 rounded-full blur-[120px] pointer-events-none z-0" />

      <div className="max-w-6xl mx-auto relative z-10">
        
        {/* Header */}
        <div className="text-center mb-16 md:mb-24">
          <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4 animate-fade-in-up">
            // Ecosystem
          </p>
          <h2 className="text-[28px] md:text-[40px] font-bold tracking-tight text-text-bright mb-4 animate-fade-in-up animate-stagger-1">
            Works where you work.
          </h2>
          <p className="text-[15px] md:text-[17px] text-text-dim max-w-xl mx-auto animate-fade-in-up animate-stagger-2">
            PromptForge isn't just a dashboard. It acts as an underlying Model Context Protocol (MCP) server, injecting stateful memory directly into your favorite tools.
          </p>
        </div>

        {/* Node Graph Layout */}
        <div className="relative max-w-5xl mx-auto">
          
           {/* Animated SVG Connections (Desktop Only) */}
           <div className="hidden md:block absolute inset-0 pointer-events-none z-0">
             <svg className="w-full h-full" preserveAspectRatio="none">
                <defs>
                   <linearGradient id="glowLine" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="rgba(99,102,241,0.1)" />
                      <stop offset="50%" stopColor="rgba(99,102,241,0.6)" />
                      <stop offset="100%" stopColor="rgba(99,102,241,0.1)" />
                   </linearGradient>
                </defs>
                {/* Lines radiating from Center (50%, 50%) to the 6 nodes */}
                {/* Top Left */}
                <path d="M 50% 50% L 20% 20%" stroke="url(#glowLine)" strokeWidth="1" fill="none" />
                <path d="M 50% 50% L 20% 20%" stroke="#6366f1" strokeWidth="2" fill="none" strokeDasharray="10 20" strokeLinecap="round">
                  <animate attributeName="stroke-dashoffset" values="30;0" dur="2s" repeatCount="indefinite" />
                </path>
                {/* Top Right */}
                <path d="M 50% 50% L 80% 20%" stroke="url(#glowLine)" strokeWidth="1" fill="none" />
                <path d="M 50% 50% L 80% 20%" stroke="#6366f1" strokeWidth="2" fill="none" strokeDasharray="10 20" strokeLinecap="round">
                  <animate attributeName="stroke-dashoffset" values="30;0" dur="2s" repeatCount="indefinite" />
                </path>
                {/* Mid Left */}
                <path d="M 50% 50% L 20% 50%" stroke="url(#glowLine)" strokeWidth="1" fill="none" />
                <path d="M 50% 50% L 20% 50%" stroke="#6366f1" strokeWidth="2" fill="none" strokeDasharray="10 20" strokeLinecap="round">
                  <animate attributeName="stroke-dashoffset" values="30;0" dur="2s" repeatCount="indefinite" />
                </path>
                {/* Mid Right */}
                <path d="M 50% 50% L 80% 50%" stroke="url(#glowLine)" strokeWidth="1" fill="none" />
                <path d="M 50% 50% L 80% 50%" stroke="#6366f1" strokeWidth="2" fill="none" strokeDasharray="10 20" strokeLinecap="round">
                  <animate attributeName="stroke-dashoffset" values="30;0" dur="2s" repeatCount="indefinite" />
                </path>
                {/* Bottom Left */}
                <path d="M 50% 50% L 20% 80%" stroke="url(#glowLine)" strokeWidth="1" fill="none" />
                <path d="M 50% 50% L 20% 80%" stroke="#6366f1" strokeWidth="2" fill="none" strokeDasharray="10 20" strokeLinecap="round">
                  <animate attributeName="stroke-dashoffset" values="30;0" dur="2s" repeatCount="indefinite" />
                </path>
                {/* Bottom Right */}
                <path d="M 50% 50% L 80% 80%" stroke="url(#glowLine)" strokeWidth="1" fill="none" />
                <path d="M 50% 50% L 80% 80%" stroke="#6366f1" strokeWidth="2" fill="none" strokeDasharray="10 20" strokeLinecap="round">
                  <animate attributeName="stroke-dashoffset" values="30;0" dur="2s" repeatCount="indefinite" />
                </path>
             </svg>
           </div>

           {/* CSS Grid (1 col mobile, 3 cols desktop) */}
           <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-x-12 md:gap-y-16 relative z-10 w-full min-h-[600px] items-center">
             
             {/* Center Node: PromptForge Server */}
             <div className="md:col-start-2 md:row-start-2 mx-auto w-40 h-40 rounded-2xl bg-layer2/80 backdrop-blur-md border-[2px] border-kira/40 flex items-center justify-center shadow-[0_0_50px_rgba(99,102,241,0.3)] relative z-20 group animate-scale-in">
                {/* Pulsing ring */}
                <div className="absolute inset-0 rounded-2xl border border-kira animate-ping opacity-20" />
                <div className="text-center">
                   <div className="w-6 h-6 bg-kira rounded-sm mx-auto mb-3 animate-pulse shadow-[0_0_15px_rgba(99,102,241,1)]" />
                   <span className="font-mono text-[11px] uppercase tracking-widest text-kira font-bold">MCP Server</span>
                </div>
             </div>

             {/* Peripheral Nodes mapped to specific columns / rows */}
             {INTEGRATIONS.map((integ, i) => {
               const staggerClass = [
                 'animate-fade-in-up animate-stagger-1',
                 'animate-fade-in-up animate-stagger-2',
                 'animate-fade-in-up animate-stagger-3',
                 'animate-fade-in-up animate-stagger-4',
                 'animate-fade-in-up animate-stagger-5',
                 'animate-fade-in-up animate-stagger-5',
               ][i]
               return (
                <div
                  key={integ.name}
                  className={`glass-card p-5 relative group overflow-hidden border-border-default/50 hover:border-text-bright/20 h-full flex flex-col justify-center ${staggerClass} ${integ.gridClass}`}
                >
                  <div className="flex items-center gap-4 mb-2">
                     <div className="w-10 h-10 rounded-lg bg-layer2 border border-border-default flex items-center justify-center text-xl grayscale group-hover:grayscale-0 transition-all shadow-inner">
                        {integ.icon}
                     </div>
                     <h3 className="text-[15px] font-semibold text-text-bright">{integ.name}</h3>
                  </div>
                  <p className="text-[12px] text-text-dim leading-relaxed ml-14">
                    {integ.desc}
                  </p>
                </div>
               )
             })}

           </div>

        </div>

      </div>
    </section>
  )
}

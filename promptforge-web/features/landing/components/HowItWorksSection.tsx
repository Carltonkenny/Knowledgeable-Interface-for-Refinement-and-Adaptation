// features/landing/components/HowItWorksSection.tsx
// Timeline with glassmorphism step cards and abstract CSS/Framer Motion graphics

'use client'

import { useState, useEffect } from 'react'
import { Chip } from '@/components/ui'
import { motion, AnimatePresence } from 'framer-motion'

const steps = [
  {
    num: '01',
    chips: [{ variant: 'kira' as const, label: 'Reading context', active: false, skipped: false }],
    title: 'Reads your message + profile',
    desc: "One fast call. Decides what's needed.",
  },
  {
    num: '02',
    chips: [
      { variant: 'intent' as const, label: 'Intent', active: false, skipped: false },
      { variant: 'context' as const, label: 'Context', active: false, skipped: false },
      { variant: 'domain' as const, label: 'Domain', active: false, skipped: false },
    ],
    title: 'Three agents analyze in parallel',
    desc: 'Intent, Context, and Domain specialists work simultaneously.',
    note: 'Some skip if Kira already knows your domain',
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

// --- Cinematic High-Fidelity Unified Engine Graphic ---

function UnifiedEngineGraphic({ activeStep }: { activeStep: number }) {
  const isInputActive = activeStep === 0
  const isAgentsActive = activeStep === 1
  const isSynthActive = activeStep === 2
  const isDiffActive = activeStep === 3
  const isMemoryActive = activeStep === 4

  return (
    <div className="w-full h-full flex flex-col bg-[#0B0D14] rounded-2xl relative overflow-hidden border border-border-default shadow-2xl p-4">
      {/* Dynamic Background */}
      <div className={`absolute inset-0 z-0 transition-colors duration-1000 ${isMemoryActive ? 'bg-success/5' : isDiffActive ? 'bg-bg/80' : 'bg-kira/5'}`} />

      <div className="relative z-10 w-full h-full flex flex-col gap-4">
        
        {/* Top Row: Intercepted Request & Vector Graph */}
        <div className="flex gap-4 h-[120px]">
          {/* Step 0: Context Payload */}
          <motion.div 
            animate={{ 
              borderColor: isInputActive ? 'rgba(99,102,241,0.8)' : 'rgba(255,255,255,0.05)',
              backgroundColor: isInputActive ? 'rgba(99,102,241,0.05)' : 'rgba(255,255,255,0.02)',
              boxShadow: isInputActive ? '0 0 30px rgba(99,102,241,0.1)' : 'none'
            }}
            transition={{ duration: 0.5 }}
            className="flex-[2] rounded-xl border flex flex-col px-4 py-3 relative overflow-hidden"
          >
             <span className="font-mono text-[9px] uppercase tracking-widest text-[#a3a3a3] mb-2">Incoming Context Payload</span>
             <div className="font-mono text-[10px] text-[#22c55e] leading-snug break-all blur-0 opacity-80">
                <motion.span animate={{ opacity: isInputActive ? 1 : 0.3 }}>{"{"}</motion.span><br/>
                &nbsp;&nbsp;<span className="text-[#60a5fa]">"user"</span>: <span className="text-[#fca5a5]">"usr_prod_8f9a"</span>,<br/>
                &nbsp;&nbsp;<span className="text-[#60a5fa]">"active_file"</span>: <span className="text-[#fca5a5]">"api/routes.ts"</span>,<br/>
                &nbsp;&nbsp;<span className="text-[#60a5fa]">"cursor_pos"</span>: <span className="text-[#fca5a5]">"L:42"</span>,<br/>
                &nbsp;&nbsp;<span className="text-[#60a5fa]">"mcp_state"</span>: <motion.span animate={{ color: isInputActive ? '#facc15' : '#4ade80' }}>"SYNCING..."</motion.span><br/>
                <motion.span animate={{ opacity: isInputActive ? 1 : 0.3 }}>{"}"}</motion.span>
             </div>
             
             {isInputActive && (
               <motion.div 
                 initial={{ left: '-100%' }} animate={{ left: '100%' }} transition={{ duration: 2, repeat: Infinity }}
                 className="absolute top-0 bottom-0 w-16 bg-gradient-to-r from-transparent via-kira/20 to-transparent skew-x-[-20deg]"
               />
             )}
          </motion.div>

          {/* Step 4: Memory Vector Graph */}
          <motion.div 
             animate={{ 
               borderColor: isMemoryActive ? 'rgba(16,185,129,0.8)' : 'rgba(255,255,255,0.05)',
               backgroundColor: isMemoryActive ? 'rgba(16,185,129,0.05)' : 'rgba(255,255,255,0.02)',
             }}
            className="flex-1 rounded-xl border flex flex-col items-center justify-center p-3 relative overflow-hidden"
          >
             <span className={`absolute top-2 left-2 font-mono text-[8px] uppercase tracking-widest ${isMemoryActive ? 'text-success' : 'text-text-dim'}`}>pgvector</span>
             
             {/* Simple visual graph mapping */}
             <div className="relative w-full h-full flex items-center justify-center mt-3">
                 <motion.div animate={{ scale: isMemoryActive ? [1, 1.2, 1] : 1 }} transition={{ duration: 2, repeat: Infinity }} className={`absolute w-3 h-3 rounded-full z-20 ${isMemoryActive ? 'bg-success shadow-[0_0_15px_#10B981]' : 'bg-text-dim'}`} />
                 <motion.div animate={{ rotate: isMemoryActive ? 180 : 0 }} transition={{ duration: 20, repeat: Infinity, ease: 'linear' }} className="absolute w-12 h-12 border border-dashed border-success/30 rounded-full" />
                 <motion.div animate={{ rotate: isMemoryActive ? -360 : 0 }} transition={{ duration: 30, repeat: Infinity, ease: 'linear' }} className="absolute w-20 h-20 border border-success/10 rounded-full" />
                 
                 {/* Satellite nodes */}
                 {isMemoryActive && (
                   <>
                     <div className="absolute top-1 left-2 w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                     <div className="absolute bottom-2 right-2 w-1.5 h-1.5 rounded-full bg-success animate-pulse" style={{ animationDelay: '500ms'}} />
                     <div className="absolute top-4 right-1 w-1.5 h-1.5 rounded-full bg-success animate-pulse" style={{ animationDelay: '1000ms'}} />
                   </>
                 )}
             </div>
          </motion.div>
        </div>

        {/* Middle Row: Central Synthesizer & Agents */}
        <div className="flex flex-1 gap-4 overflow-hidden relative">
           
           {/* Step 3: Diff Viewer Overlay (Takes over middle row) */}
           <AnimatePresence>
              {isDiffActive && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="absolute inset-0 z-30 bg-[#0B0D14] rounded-xl border border-border-bright p-4 flex flex-col shadow-2xl"
                >
                  <h4 className="font-mono text-[9px] text-text-muted uppercase tracking-widest mb-3 flex items-center justify-between">
                    <span>Diff Protocol Executed</span>
                    <span className="text-success tracking-normal">score: 98%</span>
                  </h4>
                  
                  <div className="flex-1 rounded-lg border border-border-default overflow-hidden flex flex-col font-mono text-[10px] sm:text-[11px] bg-black relative">
                    
                    {/* The Code Diff */}
                    <div className="flex-1 bg-error/5 border-l-4 border-error p-3 text-text-dim flex items-center gap-2 pr-24">
                      <span className="text-error font-bold">-</span>
                      <span className="line-through decoration-error/50">Write a quick update</span>
                    </div>
                    <div className="flex-1 bg-success/10 border-l-4 border-success p-3 text-text-bright flex items-center gap-2 pr-24 relative">
                      <span className="text-success font-bold">+</span>
                      <span>Write a decisive Q3 update email outlining auth integrations</span>
                      
                      {/* Floating Quality Annotations */}
                      <motion.div 
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 }}
                        className="absolute right-2 top-1/2 -translate-y-1/2 bg-success/20 text-success px-2 py-0.5 rounded border border-success/30 text-[8px] uppercase tracking-widest"
                      >
                        Style matched
                      </motion.div>
                    </div>

                  </div>
                </motion.div>
              )}
           </AnimatePresence>

           {/* Step 2: Synthesizer Core */}
           <motion.div 
             animate={{ 
               borderColor: isSynthActive ? 'rgba(99,102,241,0.8)' : 'rgba(255,255,255,0.05)',
               backgroundColor: isSynthActive ? 'rgba(99,102,241,0.05)' : 'rgba(255,255,255,0.02)',
               filter: isDiffActive ? 'blur(4px)' : 'blur(0px)'
             }}
             className="flex-[2] rounded-xl border flex flex-col p-4 relative"
           >
              <div className="flex items-center justify-between mb-4">
                 <span className={`font-mono text-[9px] uppercase tracking-widest ${isSynthActive ? 'text-kira' : 'text-text-muted'}`}>Prompt Construction</span>
                 <motion.div 
                    animate={{ rotate: isSynthActive ? 360 : 0 }}
                    transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                    className="w-4 h-4 rounded border-2 border-dashed border-text-dim"
                 />
              </div>

              {/* Advanced UI Funnel Simulation */}
              <div className="flex-1 flex flex-col items-center justify-center gap-2 relative">
                 {/* Top Funnel lines coming in */}
                 <div className="flex gap-4 w-full px-4 mb-2">
                    <motion.div animate={{ height: isSynthActive ? 24 : 8, backgroundColor: isSynthActive ? '#818cf8': '#333' }} className="w-1 rounded-full mx-auto transition-all duration-500" />
                    <motion.div animate={{ height: isSynthActive ? 32 : 8, backgroundColor: isSynthActive ? '#818cf8': '#333' }} className="w-1 rounded-full mx-auto transition-all duration-500 delay-100" />
                    <motion.div animate={{ height: isSynthActive ? 24 : 8, backgroundColor: isSynthActive ? '#818cf8': '#333' }} className="w-1 rounded-full mx-auto transition-all duration-500 delay-200" />
                 </div>
                 
                 {/* Injection Box */}
                 <motion.div 
                   animate={{ width: isSynthActive ? '100%' : '50%', borderColor: isSynthActive ? '#6366f1' : '#333' }}
                   className="h-10 border rounded-lg flex items-center justify-center gap-2 overflow-hidden px-2 transition-all duration-500"
                 >
                    <span className="font-mono text-[8px] text-text-dim whitespace-nowrap">sys_prompt + </span>
                    <AnimatePresence>
                       {isSynthActive && (
                         <motion.span initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="font-mono text-[8px] tracking-widest text-[#22c55e] bg-success/20 px-1 py-[1px] rounded">
                           [DOMAIN_OVERRIDE]
                         </motion.span>
                       )}
                    </AnimatePresence>
                 </motion.div>

                 {/* Outgoing Prompt */}
                 <motion.div animate={{ opacity: isSynthActive ? 1 : 0.2 }} className="w-3/4 h-2 bg-kira/80 rounded-full mt-4" />
                 <motion.div animate={{ opacity: isSynthActive ? 1 : 0.2 }} className="w-full h-2 bg-kira/50 rounded-full" />
              </div>
           </motion.div>

           {/* Step 1: Agents Sidebar (Logs) */}
           <motion.div 
             animate={{ filter: isDiffActive ? 'blur(4px)' : 'blur(0px)' }}
             className="flex-1 rounded-xl flex flex-col gap-2"
           >
              {[
                { name: 'INT', color: '#f87171' },
                { name: 'CTX', color: '#60a5fa' },
                { name: 'DOM', color: '#facc15' }
              ].map((agent, i) => (
                 <motion.div
                   key={agent.name}
                   animate={{ 
                     borderColor: isAgentsActive ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.02)',
                     backgroundColor: isAgentsActive ? 'rgba(0,0,0,0.5)' : 'rgba(255,255,255,0.02)',
                   }}
                   className="flex-1 rounded-lg border bg-layer2/50 flex flex-col p-2 relative overflow-hidden"
                 >
                   <span className="font-mono text-[8px] text-text-dim mb-1" style={{ color: isAgentsActive ? agent.color : '#666' }}>[{agent.name}_AGENT]</span>
                   <div className="font-mono text-[6px] text-[#a3a3a3] flex flex-col tracking-wider">
                      <span>{'>'} init routine</span>
                      <AnimatePresence>
                         {isAgentsActive && (
                           <>
                             <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 + (i * 0.1) }}>{'>'} load vectors</motion.span>
                             <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 + (i * 0.1) }}>{'>'} mapping params</motion.span>
                             <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 + (i * 0.1) }} className="text-success">{'>'} 200 OK</motion.span>
                           </>
                         )}
                      </AnimatePresence>
                   </div>
                 </motion.div>
              ))}
           </motion.div>
        </div>

      </div>
    </div>
  )
}


export function HowItWorksSection() {
  const [activeStep, setActiveStep] = useState(0)

  return (
    <section id="how-it-works" className="py-20 md:py-28 px-5 md:px-12 relative">
      {/* Gradient divider at top */}
      <div className="gradient-line absolute top-0 left-[10%] right-[10%]" />

      <div className="max-w-6xl mx-auto flex flex-col lg:flex-row gap-12 lg:gap-20 lg:items-start">
        
        {/* Left Column: Timeline */}
        <div className="w-full lg:w-1/2">
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
            className="text-[24px] md:text-[28px] font-bold tracking-tight text-text-bright mb-4"
          >
            Five steps. Four seconds.
          </motion.h2>

          {/* Sub */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-[13px] md:text-[14px] text-text-dim mb-12"
          >
             Honest about latency. Transparent about depth.
          </motion.p>

          {/* Steps with timeline */}
          <div className="relative pl-6 md:pl-10 pb-32">
            {/* Timeline line */}
            <div className="absolute left-[7px] md:left-[15px] top-4 bottom-4 w-px bg-gradient-to-b from-kira/40 via-kira/15 to-transparent" />

            <div className="space-y-12 lg:space-y-[40vh]"> {/* Huge spacing forces scrolling on desktop, stacked on mobile */}
              {steps.map((step, index) => (
                <motion.div
                  key={step.num}
                  initial={{ opacity: 0, x: -20, filter: 'blur(4px)' }}
                  whileInView={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
                  viewport={{  margin: '-20% 0px -50% 0px' }}
                  onViewportEnter={() => setActiveStep(index)}
                  transition={{ duration: 0.5 }}
                  className="relative flex items-start gap-4 md:gap-5"
                >
                  {/* Timeline dot */}
                  <div className={`absolute -left-6 md:-left-10 top-4 w-[14px] h-[14px] md:w-[18px] md:h-[18px] rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors duration-500 ${activeStep === index ? 'border-kira bg-kira/20' : 'border-kira/40 bg-bg'}`}>
                    <div className={`w-[5px] h-[5px] md:w-[6px] md:h-[6px] rounded-full transition-colors duration-500 ${activeStep === index ? 'bg-kira' : 'bg-kira/60'}`} />
                  </div>

                  {/* Content */}
                  <div className={`glass-card p-5 flex-1 transition-all duration-500 ${activeStep === index ? 'border-kira/30 shadow-[0_0_20px_rgba(99,102,241,0.1)]' : 'border-border-default opacity-60'}`}>
                    {/* Step number */}
                    <span className={`font-mono text-[10px] tracking-wider transition-colors duration-500 ${activeStep === index ? 'text-kira' : 'text-text-dim'}`}>
                      {step.num}
                    </span>

                    {/* Chips row */}
                    {step.chips.length > 0 && (
                      <div className="flex items-center gap-2 mt-2 mb-3 flex-wrap">
                        {step.chips.map((chip, i) => (
                          <Chip
                            key={i}
                            variant={chip.variant}
                            active={activeStep === index ? true : chip.active}
                            skipped={chip.skipped}
                          >
                            {chip.label}
                          </Chip>
                        ))}
                      </div>
                    )}

                    {/* Title */}
                    <h3 className="text-[14px] md:text-[15px] font-semibold text-text-bright mb-1 mt-2">
                       {step.title}
                    </h3>

                    {/* Description */}
                    <p className="text-[12px] md:text-[13px] text-text-dim">
                       {step.desc}
                    </p>

                    {/* Note */}
                    {step.note && (
                      <p className="font-mono text-[10px] text-text-dim mt-2 opacity-60">
                        {step.note}
                      </p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Perfectly Locked Sticky Graphic */}
        <div className="hidden lg:flex w-1/2 sticky top-32 h-[calc(100vh-12rem)] items-center justify-center relative">
          <div className="w-full aspect-square max-w-[500px] flex items-center justify-center relative">
             {/* Background glow behind graphic */}
            <div className={`absolute inset-0 rounded-full blur-[100px] pointer-events-none transition-colors duration-1000 ${activeStep === 3 ? 'bg-success/10' : 'bg-kira/10'}`} />
            
            <div className="w-full h-full relative z-10 transition-all duration-500">
               <UnifiedEngineGraphic activeStep={activeStep} />
            </div>
            
            <motion.div
              layoutId="emote-caption"
              className="absolute -bottom-6 left-1/2 -translate-x-1/2 glass-card px-4 py-2 z-20 whitespace-nowrap"
            >
              <p className="font-mono text-[10px] text-text-bright uppercase tracking-widest flex items-center justify-center gap-2">
                 <span className={`w-1.5 h-1.5 rounded-full animate-live-pulse ${activeStep === 3 ? 'bg-success' : 'bg-kira'}`} />
                 {steps[activeStep].title}
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  )
}

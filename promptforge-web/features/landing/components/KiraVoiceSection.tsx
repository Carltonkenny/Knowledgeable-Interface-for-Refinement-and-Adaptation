// features/landing/components/KiraVoiceSection.tsx
// Interactive Morphing Terminal for Kira's voice progression

'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'

const DOMAINS = [
  {
    id: 'backend', name: 'Backend Architecture',
    levels: [
      { stage: 'Cold', session: 'SESSION 01', quote: "Before I write this SQL — what dialect are we using? Are we on Postgres 15+ or older MySQL? Should I be cautious about UUID generating functions versus standard auto-incrementing integers? And are there any specific naming conventions for junction tables you want me to strictly enforce?", desc: "Kira asks clarifying baseline questions.", metric: "0 Data mapped" },
      { stage: 'Warm', session: 'SESSION 18', quote: "FastAPI endpoints for the new analytics service. Should I use your standard dependency injection pattern for the database sessions? I noticed last month we relied heavily on Pydantic v2 schemas for request validation. Want me to duplicate that validation layer here as well?", desc: "She recognizes your framework and past architectural choices.", metric: "14 Data points" },
      { stage: 'Tuned', session: 'SESSION 54', quote: "On it. Postgres daily active users script. I'll use CTEs for readability and ensure the WHERE clause filters on your partitioned created_at index. I also noticed this touches the same reporting tables we modified in Session 30, so I'll inject the identical materialized view refresh logic.", desc: "Zero boilerplate. She executes exactly like a senior engineer.", metric: "52 Data points" }
    ]
  },
  {
    id: 'frontend', name: 'Frontend React',
    levels: [
      { stage: 'Cold', session: 'SESSION 03', quote: "I'm scaffolding the new screen. Are we using Expo Router, or standard React Navigation? Do you prefer pure Tailwind CSS or a strict UI library like shadcn/ui? Let me know if you want the state managed via Zustand or just standard React Context providers before I begin.", desc: "Establishing baseline preferences for the mobile stack.", metric: "0 Data mapped" },
      { stage: 'Warm', session: 'SESSION 25', quote: "Refactoring the Data Table. Want me to stick to the shadcn/ui and TanStack Table patterns we established last week? I recall you explicitly requested strict server-side pagination with React Query to handle the massive datasets. I'll scaffold the hooks accordingly.", desc: "Remembers your exact component library configurations.", metric: "28 Data points" },
      { stage: 'Tuned', session: 'SESSION 89', quote: "Vite config updated. I memoized the animated components using React.memo and lazy-loaded the heavy chart libraries, perfectly matching your strict 95+ Lighthouse targets. I also stripped the moment.js imports and swapped them natively to date-fns precisely as you enforced in the last PR.", desc: "Anticipates your performance optimizations instantly.", metric: "109 Data points" }
    ]
  },
  {
    id: 'devops', name: 'DevOps & AWS',
    levels: [
      { stage: 'Cold', session: 'SESSION 05', quote: "Setting up the AWS provider block. Are we dealing with standard local profiles, or are we injecting secrets via GitHub Actions OIDC? Do you want the S3 bucket to enforce KMS encryption by default, or is server-side AES-256 sufficient for this non-prod environment?", desc: "Learns how you handle deployments and secrets.", metric: "0 Data mapped" },
      { stage: 'Warm', session: 'SESSION 42', quote: "Dockerizing the Python worker. Shall I implement the multi-stage Alpine build pattern you used in the auth service last month? It shaved 400MB off the container size last time. I can also pull the same non-root user execution policy to satisfy the security scanner.", desc: "Recycles your most efficient infrastructure patterns.", metric: "45 Data points" },
      { stage: 'Tuned', session: 'SESSION 92', quote: "Terraform state updated. Deploying the autoscaling group with your hardened IAM roles and strict exact-match tagging conventions. I automatically enabled VPC Flow Logs and dropped them into the centralized Infosec S3 bucket, anticipating your compliance requirements entirely.", desc: "Flawless infrastructure execution based on memory.", metric: "142 Data points" }
    ]
  },
  {
    id: 'data', name: 'Data Pipelines',
    levels: [
      { stage: 'Cold', session: 'SESSION 02', quote: "Writing the ETL script. Are we using basic Pandas, aggressive in-memory Polars, or pushing this directly to PySpark on a Databricks cluster? Also, should I implement try/catch blocks for messy CSV strings, or just drop malformed rows entirely?", desc: "Mapping out your data processing boundaries.", metric: "0 Data mapped" },
      { stage: 'Warm', session: 'SESSION 15', quote: "Updating the Airflow DAG. Should I set the retry policy to 3 attempts with exponential backoff like we did for the sales pipeline? I noticed you usually prefer alerting via the Slack webhook rather than email when the upstream ingest fails. Want me to add that operator?", desc: "Leverages your previous orchestration rules.", metric: "31 Data points" },
      { stage: 'Tuned', session: 'SESSION 67', quote: "dbt models compiled. I injected the incremental materialization logic based on your custom timestamps to drastically optimize Snowflake warehouse compute costs. I also applied the strict schema tests on the unique ID columns to prevent the data duplication issue we fought last quarter.", desc: "Proactively optimizes based on your strict financial limits.", metric: "210 Data points" }
    ]
  },
  {
    id: 'pm', name: 'Product Management',
    levels: [
      { stage: 'Cold', session: 'SESSION 01', quote: "Drafting the PRD. Do you prefer the standard 'Jobs to be Done' framework, or simple user story mapping? Do you need a strict Definition of Done attached, or are we keeping this document loose and high-level for early stakeholder alignment?", desc: "Seeking structure for product documentation.", metric: "0 Data mapped" },
      { stage: 'Warm', session: 'SESSION 12', quote: "Writing tickets for the Epic. Should I include the standard AC checklist and QA manual verification steps at the bottom of every ticket? Your engineers usually ask for strict API payload examples, so I can generate those automatically if you'd like.", desc: "Knows your team's exact ticket hygiene.", metric: "18 Data points" },
      { stage: 'Tuned', session: 'SESSION 44', quote: "Jira mapping generated. I broke the frontend tasks down to 3-point maximums, fully anticipating your Lead Engineer's velocity constraints. I also separated the Database migration tickets into their own explicit Epic since I know your DBA requires a 48-hour advanced pull request review.", desc: "Navigates your exact agile methodology.", metric: "88 Data points" }
    ]
  },
  {
    id: 'marketing', name: 'Marketing Copy',
    levels: [
      { stage: 'Cold', session: 'SESSION 04', quote: "Writing the launch tweet. What's the tone here? Are we aiming for hype-focused, deeply technical, or highly conversational? Do you want me to limit emojis, use a hook-first thread format, or just a single punchy visual statement?", desc: "Calibrating to your brand's voice.", metric: "0 Data mapped" },
      { stage: 'Warm', session: 'SESSION 21', quote: "Drafting the newsletter. Want me to keep it under 300 words and highly punchy, exact to last month's update style? I noticed your CTR was highest when we led with the changelog bullet points rather than the long narrative intro.", desc: "Emulates your exact editorial constraints.", metric: "23 Data points" },
      { stage: 'Tuned', session: 'SESSION 81', quote: "Blog post outlined. I led instantly with the technical architecture pain-points, dropping the marketing fluff entirely, just how your core developer audience demands. I utilized the short, direct sentences you favor and embedded the specific terminal code snippets.", desc: "Speaks flawlessly in your curated voice.", metric: "155 Data points" }
    ]
  },
  {
    id: 'security', name: 'Security & Auth',
    levels: [
      { stage: 'Cold', session: 'SESSION 07', quote: "Implementing auth. Are we defaulting to basic OAuth wrappers using NextAuth, or rolling a strict custom JWT strategy? Should I assume we need RBAC (Role Based Access Control) immediately, or is this a simple single-tenant admin panel?", desc: "Verifying acceptable entry points.", metric: "0 Data mapped" },
      { stage: 'Warm', session: 'SESSION 32', quote: "Adding rate limiting to the new endpoints. Stick to the 100req/min Redis sliding window we used in the core API? I can also patch in the exact same IP-banning middleware you wrote to stop the credential stuffing attacks last week.", desc: "Applies past security hygiene instantly.", metric: "58 Data points" },
      { stage: 'Tuned', session: 'SESSION 99', quote: "Middleware hardened. I instantly injected the strict CSP headers, rotated the signing keys, and ensured all tokens are HTTP-only secure by default. I also enforced the bcrypt 12-round hashing specifically because I know your compliance audit requires it next week.", desc: "Automates your non-negotiable security postures.", metric: "310 Data points" }
    ]
  },
  {
    id: 'personal', name: 'Career & Networking',
    levels: [
      { stage: 'Cold', session: 'SESSION 01', quote: "Reviewing this email draft. Are we writing a formal cold-intro to a recruiter, or casually catching up with a former colleague? Should I focus heavily on your recent backend accomplishments, or pivot toward your leadership and management skills?", desc: "Understanding your networking intent.", metric: "0 Data mapped" },
      { stage: 'Warm', session: 'SESSION 19', quote: "Polishing your resume bullet point. Let's strictly quantify this action—what was the percentage gain in performance? Based on your previous bullets, recruiters respond best when we highlight exact revenue or latency improvements rather than generic effort.", desc: "Pushes you toward your established career goals.", metric: "21 Data points" },
      { stage: 'Tuned', session: 'SESSION 63', quote: "Cover letter finalized. I explicitly emphasized your transition from monolithic to microservices, directly aligning with the job description's core requirement. I also wove in your specific Kubernetes migration story from 2023 because the hiring manager explicitly mentioned scaling woes in their recent blog post.", desc: "Synthesizes your exact career trajectory perfectly.", metric: "128 Data points" }
    ]
  }
]

export function KiraVoiceSection() {
  const [activeDomainIdx, setActiveDomainIdx] = useState(0)
  const [activeLevelIdx, setActiveLevelIdx] = useState(0)
  const [isHovered, setIsHovered] = useState(false)

  // Autoplay functionality: Progress the timeline automatically entirely
  useEffect(() => {
    if (isHovered) return

    const interval = setInterval(() => {
      setActiveLevelIdx((prev) => {
        if (prev === 2) {
           // Move to next domain and reset level, loop back to 0
           setActiveDomainIdx((d) => (d + 1) % DOMAINS.length)
           return 0
        }
        return prev + 1
      })
    }, 2500) // Change state every 2.5 seconds

    return () => clearInterval(interval)
  }, [isHovered])

  const activeDomain = DOMAINS[activeDomainIdx]
  const activeData = activeDomain.levels[activeLevelIdx]

  // Dynamic Theme Generation
  const getThemeVars = () => {
    if (activeLevelIdx === 0) return { color: '#6366f1', bg: 'rgba(99,102,241,0.05)', border: 'rgba(99,102,241,0.3)', glow: 'rgba(99,102,241,0.2)' } // Cold - Blue
    if (activeLevelIdx === 1) return { color: '#f59e0b', bg: 'rgba(245,158,11,0.05)', border: 'rgba(245,158,11,0.3)', glow: 'rgba(245,158,11,0.2)' }   // Warm - Amber
    return { color: '#10b981', bg: 'rgba(16,185,129,0.05)', border: 'rgba(16,185,129,0.4)', glow: 'rgba(16,185,129,0.3)' }                     // Tuned - Green
  }
  const theme = getThemeVars()

  return (
    <section id="kira-voice" className="py-24 md:py-32 relative overflow-hidden">
      {/* Background glow syncing with theme */}
      <motion.div 
         animate={{ backgroundColor: theme.glow }}
         transition={{ duration: 1 }}
         className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full blur-[150px] pointer-events-none" 
      />

      <div className="max-w-6xl mx-auto px-5 md:px-12 relative z-10 mb-16 text-center md:text-left">
        {/* Eyebrow */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4"
        >
          // 02  Meet Kira
        </motion.p>

        {/* Title */}
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-[28px] md:text-[36px] font-bold tracking-tight text-text-bright mb-4"
        >
          Not a chatbot.
          <br className="hidden md:block" />
          A collaborator that learns your base.
        </motion.h2>

        {/* Sub */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="text-[14px] md:text-[15px] text-text-dim max-w-2xl mx-auto md:mx-0"
        >
          She reads your profile before every response. Click the timeline or let it play to watch her rewrite responses based on memory.
        </motion.p>
      </div>

      {/* The Morphing Terminal Component */}
      <div 
        className="max-w-5xl mx-auto px-5 md:px-12 relative z-20"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <motion.div 
           animate={{ borderColor: theme.border, boxShadow: `0 0 40px ${theme.glow}` }}
           transition={{ duration: 0.8 }}
           className="flex flex-col md:flex-row glass-card overflow-hidden border"
        >
          
          {/* Left Sidebar: Domains */}
          <div className="w-full md:w-[220px] border-b md:border-b-0 md:border-r border-border-default bg-layer2/50 flex flex-row md:flex-col p-4 gap-2 overflow-x-auto custom-scrollbar">
            {DOMAINS.map((domain, idx) => (
              <button
                key={domain.id}
                onClick={() => { setActiveDomainIdx(idx); setActiveLevelIdx(0); setIsHovered(true) }}
                className={`text-left px-4 py-3 rounded-lg transition-all duration-300 font-medium text-[13px] whitespace-nowrap shrink-0 md:w-full
                  ${activeDomainIdx === idx ? 'bg-white/10 text-white' : 'text-text-dim hover:bg-white/5 hover:text-text-bright border border-transparent'}
                `}
              >
                {domain.name}
              </button>
            ))}
          </div>

          {/* Right Main Window: Terminal + Timeline */}
          <motion.div 
            animate={{ backgroundColor: theme.bg }}
            transition={{ duration: 0.8 }}
            className="w-full flex-1 flex flex-col relative bg-layer1 min-h-[380px]"
          >
            {/* Terminal Header */}
            <div className="flex items-center px-4 py-3 border-b border-border-default bg-layer2/50 backdrop-blur-md">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-error/50" />
                <div className="w-3 h-3 rounded-full bg-warning/50" />
                <div className="w-3 h-3 rounded-full bg-success/50" />
              </div>
              <div className="mx-auto flex gap-2 items-center">
                {/* Auto Play Indicator */}
                {!isHovered && <motion.div animate={{ opacity: [0, 1, 0] }} transition={{ duration: 2, repeat: Infinity }} className="w-1.5 h-1.5 rounded-full bg-kira ml-2" />}
              </div>
            </div>

            {/* Terminal Body */}
            <div className="flex-1 p-6 flex flex-col relative">
              <AnimatePresence mode="wait">
                <motion.div
                  key={`${activeDomain.id}-${activeLevelIdx}`}
                  initial={{ opacity: 0, y: 10, filter: 'blur(8px)' }}
                  animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                  exit={{ opacity: 0, y: -10, filter: 'blur(8px)' }}
                  transition={{ duration: 0.4 }}
                  className="flex-1 flex flex-col"
                >
                  <p className="text-[16px] md:text-[18px] text-text-bright leading-relaxed italic mb-8 font-medium">
                    &ldquo;{activeData.quote}&rdquo;
                  </p>
                  
                  <div className="mt-auto grid grid-cols-2 gap-4 pt-6 border-t border-border-subtle">
                    <div>
                      <p className="font-mono text-[9px] uppercase tracking-wider text-text-muted mb-1">Impact</p>
                      <p className="text-[13px] text-text-dim">{activeData.desc}</p>
                    </div>
                    <div>
                        <p className="font-mono text-[9px] uppercase tracking-wider text-text-muted mb-1">Profile Matrix</p>
                        <motion.p 
                          animate={{ color: theme.color }}
                          className="font-mono text-[13px]"
                        >
                          {activeData.metric}
                        </motion.p>
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Terminal Timeline Footer */}
            <div className="px-6 py-5 bg-layer2/80 border-t border-border-default relative">
              <div className="flex items-center justify-between relative max-w-lg mx-auto">
                {/* Connecting Track Line Base */}
                <div className="absolute top-1/2 left-4 right-4 h-1 rounded-full bg-border-default -translate-y-1/2 z-0" />
                
                {/* Colored Progress Track */}
                <motion.div 
                  className="absolute top-1/2 left-4 h-1 rounded-full -translate-y-1/2 z-0" 
                  animate={{ 
                    width: `calc(${(activeLevelIdx / 2) * 100}% - 32px)`,
                    backgroundColor: theme.color 
                  }}
                  transition={{ duration: 0.5, ease: "easeInOut" }}
                />

                {/* The 3 Stage Nodes */}
                {activeDomain.levels.map((lvl, idx) => (
                  <button
                    key={lvl.stage}
                    onClick={() => { setActiveLevelIdx(idx); setIsHovered(true) }}
                    className="relative z-10 flex flex-col items-center gap-2 group"
                  >
                    <motion.div 
                      animate={{
                         backgroundColor: activeLevelIdx >= idx ? theme.color : '#1a1d2d',
                         borderColor: activeLevelIdx >= idx ? theme.color : '#2d3142',
                         scale: activeLevelIdx === idx ? 1.2 : 1
                      }}
                      className="w-5 h-5 rounded-full border-2 transition-all duration-300"
                    />
                    <div className="absolute top-8 flex flex-col items-center mt-1">
                      <span className={`font-mono text-[10px] tracking-wider uppercase transition-colors ${activeLevelIdx === idx ? 'text-text-bright' : 'text-text-muted'}`}>{lvl.stage}</span>
                      <span className="font-mono text-[9px] text-text-dim/50 whitespace-nowrap">{lvl.session}</span>
                    </div>
                  </button>
                ))}
              </div>
            {/* Spacer so the absolutely positioned text fits */}
              <div className="h-10" />
            </div>

          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}

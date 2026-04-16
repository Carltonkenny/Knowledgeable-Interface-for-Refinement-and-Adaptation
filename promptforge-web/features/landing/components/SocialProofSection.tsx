// features/landing/components/SocialProofSection.tsx
// Trust signals — 15 scrolling testimonials
// Server Component — CSS-only marquee animation, no Framer Motion needed

const TESTIMONIALS = [
  {
    quote: "I used to spend 10 minutes writing prompts. Now Kira does it in seconds, better than I ever could.",
    name: "Priya Sharma",
    role: "Product Manager",
    company: "FinTech Org, BLR",
    avatar: "https://randomuser.me/api/portraits/women/22.jpg",
  },
  {
    quote: "The memory feature is a game-changer. Kira knows my domain, my tone, my audience. It feels like a real collaborator.",
    name: "Rohan Desai",
    role: "Staff Engineer",
    company: "SaaS Enterprise",
    avatar: "https://randomuser.me/api/portraits/men/33.jpg",
  },
  {
    quote: "Switched from ChatGPT for prompt work. The quality scoring alone made it worth it — I can see exactly what improved.",
    name: "Alex C.",
    role: "Content Strategist",
    company: "Marketing Agency",
    avatar: "https://randomuser.me/api/portraits/men/11.jpg",
  },
  {
    quote: "Finally a tool for serious devs. It reads my codebase context perfectly before answering.",
    name: "Karthik N.",
    role: "Backend Lead",
    company: "E-Commerce, BLR",
    avatar: "https://randomuser.me/api/portraits/men/55.jpg",
  },
  {
    quote: "Saves me easily 2 hours a week on internal documentation comms. Highly recommend.",
    name: "Sarah Jenkins",
    role: "Technical Writer",
    company: "DevTools",
    avatar: "https://randomuser.me/api/portraits/women/33.jpg",
  },
  {
    quote: "I love watching the agents work in parallel. You can literally see it optimizing the prompt in real time.",
    name: "Amit Patel",
    role: "Founder",
    company: "AI Startup",
    avatar: "https://randomuser.me/api/portraits/men/44.jpg",
  },
  {
    quote: "The API integrations are solid. We've automated our entire prompt-engineering pipeline with PromptForge.",
    name: "Neha Gupta",
    role: "Data Scientist",
    company: "HealthTech, BLR",
    avatar: "https://randomuser.me/api/portraits/women/44.jpg",
  },
  {
    quote: "It's like having a senior engineer reviewing all my prompts. The specificity score forces me to be clearer.",
    name: "Marcus R.",
    role: "Frontend Dev",
    company: "Design Agency",
    avatar: "https://randomuser.me/api/portraits/men/90.jpg",
  },
  {
    quote: "Built my entire initial launch strategy using just 4 prompts refined by Kira.",
    name: "Divya Kumar",
    role: "Product Owner",
    company: "Logistics SaaS",
    avatar: "https://randomuser.me/api/portraits/women/55.jpg",
  },
  {
    quote: "Best AI teammate ever. The more I use it, the less context I have to give. It just knows.",
    name: "Vikram S.",
    role: "UX Researcher",
    company: "Tech Giant, BLR",
    avatar: "https://randomuser.me/api/portraits/men/77.jpg",
  },
  {
    quote: "PromptForge made me realize how bad my original prompts were. Now they're bulletproof.",
    name: "Emily Wong",
    role: "Creator",
    company: "Media Co",
    avatar: "https://randomuser.me/api/portraits/women/66.jpg",
  },
  {
    quote: "Insane latency. 4 parallel agents generating a perfect prompt in under 3 seconds. Magic.",
    name: "Vishal T.",
    role: "DevOps Engineer",
    company: "Cloud Infra",
    avatar: "https://randomuser.me/api/portraits/men/88.jpg",
  },
  {
    quote: "The interface is gorgeous. Glassmorphism done right. Oh, and the AI is amazing too.",
    name: "James O.",
    role: "UI Designer",
    company: "Freelance",
    avatar: "https://randomuser.me/api/portraits/men/32.jpg",
  },
  {
    quote: "Our entire marketing team uses Kira to refine copy now. It aligns perfectly with our brand tone.",
    name: "Aditi M.",
    role: "CMO",
    company: "EdTech, BLR",
    avatar: "https://randomuser.me/api/portraits/women/77.jpg",
  },
  {
    quote: "I thought it was just another wrapper. It's not. The domain tuning is legitimately next level.",
    name: "Sneha Reddy",
    role: "Fullstack Eng",
    company: "FinTech Startup",
    avatar: "https://randomuser.me/api/portraits/women/88.jpg",
  },
]

export function SocialProofSection() {
  return (
    <section className="py-20 md:py-28 relative overflow-hidden">
      <div className="gradient-line absolute top-0 left-[10%] right-[10%]" />

      <div className="max-w-6xl mx-auto px-5 md:px-12 mb-14 text-center">
        {/* Section header */}
        <div className="animate-fade-in-up">
          <p className="font-mono text-kira tracking-[3px] uppercase text-[10px] mb-4">
            // what builders say
          </p>
          <h2 className="text-[24px] md:text-[28px] font-bold tracking-tight text-text-bright mb-4">
            Trusted by developers who care about quality.
          </h2>
          <p className="text-[13px] md:text-[14px] text-text-dim max-w-xl mx-auto">
            Used by engineers, writers, and product teams at startups and enterprises alike.
          </p>
        </div>
      </div>

      {/* Marquee Track */}
      <div className="relative w-full overflow-hidden flex pb-8">
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes social-marquee {
            0% { transform: translateX(0); }
            100% { transform: translateX(calc(-50% - 1rem)); } 
          }
          .animate-social-marquee {
            animation: social-marquee 60s linear infinite;
            width: max-content;
          }
          .animate-social-marquee:hover {
            animation-play-state: paused;
          }
        `}} />
        
        {/* Fade Edges */}
        <div className="absolute left-0 top-0 bottom-0 w-16 md:w-40 bg-gradient-to-r from-bg to-transparent z-20 pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-16 md:w-40 bg-gradient-to-l from-bg to-transparent z-20 pointer-events-none" />

        <div className="flex animate-social-marquee gap-6 px-6 items-stretch">
          {/* Double array for infinite scroll loop */}
          {[...TESTIMONIALS, ...TESTIMONIALS].map((t, index) => (
            <div
              key={`${t.name}-${index}`}
              className="w-[320px] md:w-[350px] shrink-0 glass-card p-6 flex flex-col justify-between"
            >
              <div className="flex items-center gap-1 mb-4 text-kira">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/>
                </svg>
              </div>

              {/* Quote */}
              <p className="text-[14px] text-text-default leading-relaxed mb-6 font-medium">
                {t.quote}
              </p>

              {/* Author */}
              <div className="flex items-center gap-3 pt-4 border-t border-border-subtle">
                <img 
                  src={t.avatar} 
                  alt={t.name}
                  className="w-10 h-10 rounded-full border border-kira/30 object-cover flex-shrink-0"
                  loading="lazy"
                />
                <div>
                  <p className="text-[13px] font-medium text-text-bright">{t.name}</p>
                  <p className="text-[11px] text-text-dim">{t.role} · {t.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

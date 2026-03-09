// features/onboarding/components/AuthLeftPanel.tsx
// Server component — shared left panel for login and signup layouts
// NO 'use client' — this is a server component

interface AuthLeftPanelProps {
  variant: 'login' | 'signup'
}

export default function AuthLeftPanel({ variant }: AuthLeftPanelProps) {
  const isSignup = variant === 'signup'

  return (
    <div
      className="relative hidden lg:flex flex-col justify-between p-12"
      style={{
        background: `
          repeating-linear-gradient(
            0deg,
            rgba(99, 102, 241, 0.03) 0px,
            rgba(99, 102, 241, 0.03) 1px,
            transparent 1px,
            transparent 40px
          ),
          repeating-linear-gradient(
            90deg,
            rgba(99, 102, 241, 0.03) 0px,
            rgba(99, 102, 241, 0.03) 1px,
            transparent 1px,
            transparent 40px
          )
        `,
        backgroundColor: 'var(--bg)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg border border-kira bg-[var(--kira-dim)] flex items-center justify-center">
          <span className="text-kira font-bold font-mono">⬡</span>
        </div>
        <span className="text-text-bright font-bold text-lg">PromptForge</span>
      </div>

      {/* Headline + Sub */}
      <div className="space-y-6">
        <h1 className="text-4xl font-bold text-text-bright leading-tight">
          {isSignup ? (
            <>
              Your prompts,
              <br />
              <em className="gradient-text">precisely</em> engineered.
            </>
          ) : (
            <>
              Welcome back.
              <br />
              <span className="text-text-dim">Kira remembers.</span>
            </>
          )}
        </h1>

        <p className="text-text-dim text-base leading-relaxed max-w-md">
          {isSignup
            ? "Kira learns how you think. First session starts warm — three questions and she knows your domain before you send a prompt."
            : "Your profile is intact. Pick up exactly where you left off."}
        </p>

        {/* Kira Quote Block */}
        <div
          className="rounded-xl p-4 border"
          style={{
            backgroundColor: 'var(--kira-glow)',
            borderColor: 'var(--kira-dim)',
          }}
        >
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-md border border-kira bg-[var(--kira-dim)] flex items-center justify-center flex-shrink-0">
              <span className="text-kira font-bold font-mono text-sm">K</span>
            </div>
            <blockquote className="text-text-default text-sm italic leading-relaxed">
              {isSignup
                ? "Let's see what you're working on."
                : "Good to have you back."}
            </blockquote>
          </div>
        </div>
      </div>

      {/* Spacer for balance */}
      <div />
    </div>
  )
}

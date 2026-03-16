// features/onboarding/components/OnboardingWizard.tsx
// 3-step onboarding: Primary use → Audience → AI frustrations

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'

interface OnboardingWizardProps {
  token: string
  apiUrl: string
  onComplete: (profile: {
    primary_use: string
    audience: string
    ai_frustration: string
    frustration_detail?: string
  }) => void
}

type Step = 'use' | 'audience' | 'frustration'

const USE_CASES = [
  { value: 'content_creation', label: 'Content Creation', icon: '✍️', desc: 'Blog posts, social media, marketing copy' },
  { value: 'coding', label: 'Coding & Development', icon: '💻', desc: 'Code generation, debugging, documentation' },
  { value: 'research', label: 'Research & Analysis', icon: '📊', desc: 'Literature reviews, data analysis, summaries' },
  { value: 'education', label: 'Education & Training', icon: '📚', desc: 'Lesson plans, tutorials, explanations' },
  { value: 'business', label: 'Business & Communication', icon: '💼', desc: 'Emails, reports, presentations' },
  { value: 'creative', label: 'Creative Writing', icon: '🎨', desc: 'Stories, scripts, poetry, worldbuilding' },
]

const AUDIENCE_OPTIONS = [
  { value: 'technical', label: 'Technical Audience', desc: 'Developers, engineers, data scientists' },
  { value: 'business', label: 'Business Professionals', desc: 'Managers, executives, stakeholders' },
  { value: 'general', label: 'General Public', desc: 'Non-specialists, broad audience' },
  { value: 'academic', label: 'Academic', desc: 'Researchers, students, educators' },
  { value: 'creative', label: 'Creative Community', desc: 'Artists, writers, designers' },
]

const FRUSTRATIONS = [
  { value: 'too_vague', label: 'AI responses are too vague', desc: 'Generic answers without specifics' },
  { value: 'misses_context', label: 'AI misses my context', desc: "Doesn't understand my situation" },
  { value: 'too_wordy', label: 'AI is too wordy', desc: 'Long responses when I want brevity' },
  { value: 'too_brief', label: 'AI is too brief', desc: 'Needs more detail and explanation' },
  { value: 'wrong_tone', label: 'Wrong tone', desc: 'Too formal or too casual' },
  { value: 'repeats', label: 'AI repeats itself', desc: 'Says the same thing multiple times' },
]

export default function OnboardingWizard({ token, apiUrl, onComplete }: OnboardingWizardProps) {
  const router = useRouter()
  const [step, setStep] = useState<Step>('use')
  const [profile, setProfile] = useState({
    primary_use: '',
    audience: '',
    ai_frustration: '',
    frustration_detail: '',
  })

  const handleNext = () => {
    if (step === 'use') setStep('audience')
    else if (step === 'audience') setStep('frustration')
    else if (step === 'frustration') {
      // Pass profile to parent's onComplete
      onComplete(profile)
    }
  }

  const getProgress = () => {
    if (step === 'use') return 33
    if (step === 'audience') return 66
    return 100
  }

  return (
    <div className="min-h-screen bg-layer1 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-xs text-text-dim mb-2">
            <span>Step {step === 'use' ? '1' : step === 'audience' ? '2' : '3'} of 3</span>
            <span>{getProgress()}% Complete</span>
          </div>
          <div className="h-1 bg-layer3 rounded-full overflow-hidden">
            <div 
              className="h-full bg-kira transition-all duration-300"
              style={{ width: `${getProgress()}%` }}
            />
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-[var(--surface-card)] rounded-2xl border border-border-default shadow-card p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key="use"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
            >
              <h2 className="text-2xl font-bold text-text-bright mb-2">
                What will you use PromptForge for?
              </h2>
              <p className="text-text-dim mb-6">
                This helps Kira tailor her prompt engineering to your domain.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {USE_CASES.map((useCase, i) => (
                  <motion.button
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: i * 0.08 }}
                    key={useCase.value}
                    onClick={() => setProfile({ ...profile, primary_use: useCase.value })}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      profile.primary_use === useCase.value
                        ? 'border-kira bg-kira/10 shadow-glow'
                        : 'border-border-default bg-[var(--surface-card)] hover:bg-[var(--surface-hover)] hover:border-border-focus'
                    }`}
                  >
                    <span className="text-2xl mb-2 block">{useCase.icon}</span>
                    <span className="font-medium text-text-bright block">{useCase.label}</span>
                    <span className="text-xs text-text-dim">{useCase.desc}</span>
                  </motion.button>
                ))}
              </div>
            </motion.div>

          {step === 'audience' && (
            <motion.div
              key="audience"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
            >
              <h2 className="text-2xl font-bold text-text-bright mb-2">
                Who is your primary audience?
              </h2>
              <p className="text-text-dim mb-6">
                Kira will optimize prompts for your target readers.
              </p>
              <div className="space-y-3">
                {AUDIENCE_OPTIONS.map((option, i) => (
                  <motion.button
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: i * 0.08 }}
                    key={option.value}
                    onClick={() => setProfile({ ...profile, audience: option.value })}
                    className={`w-full p-4 rounded-xl border text-left transition-all ${
                      profile.audience === option.value
                        ? 'border-kira bg-kira/10 shadow-glow'
                        : 'border-border-default bg-[var(--surface-card)] hover:bg-[var(--surface-hover)] hover:border-border-focus'
                    }`}
                  >
                    <span className="font-medium text-text-bright block">{option.label}</span>
                    <span className="text-xs text-text-dim">{option.desc}</span>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {step === 'frustration' && (
            <motion.div
              key="frustration"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
            >
              <h2 className="text-2xl font-bold text-text-bright mb-2">
                What frustrates you about AI?
              </h2>
              <p className="text-text-dim mb-6">
                Tell us what goes wrong so Kira can fix it.
              </p>
              <div className="space-y-3 mb-6">
                {FRUSTRATIONS.map((frustration, i) => (
                  <motion.button
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: i * 0.08 }}
                    key={frustration.value}
                    onClick={() => setProfile({ ...profile, ai_frustration: frustration.value })}
                    className={`w-full p-4 rounded-xl border text-left transition-all ${
                      profile.ai_frustration === frustration.value
                        ? 'border-kira bg-kira/10 shadow-glow'
                        : 'border-border-default bg-[var(--surface-card)] hover:bg-[var(--surface-hover)] hover:border-border-focus'
                    }`}
                  >
                    <span className="font-medium text-text-bright block">{frustration.label}</span>
                    <span className="text-xs text-text-dim">{frustration.desc}</span>
                  </motion.button>
                ))}
              </div>
              
              <motion.div 
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: 0.5 }}
                className="mt-4"
              >
                <label className="text-sm text-text-dim block mb-2">
                  Anything specific you'd like to add? (optional)
                </label>
                <textarea
                  value={profile.frustration_detail}
                  onChange={(e) => setProfile({ ...profile, frustration_detail: e.target.value })}
                  placeholder="E.g., 'AI always uses too much jargon' or 'I want more concrete examples'"
                  rows={3}
                  className="w-full bg-[var(--bg)] border border-border-default rounded-lg p-3 text-text-default text-sm placeholder:text-text-dim focus:shadow-glow focus:border-border-focus outline-none"
                />
              </motion.div>
            </motion.div>
          )}
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t border-border-subtle">
            {step !== 'use' ? (
              <button
                onClick={() => setStep(step === 'audience' ? 'use' : 'audience')}
                className="text-text-dim hover:text-text-bright text-sm"
              >
                ← Back
              </button>
            ) : (
              <div />
            )}
            <button
              onClick={handleNext}
              disabled={
                (step === 'use' && !profile.primary_use) ||
                (step === 'audience' && !profile.audience) ||
                (step === 'frustration' && !profile.ai_frustration)
              }
              className={`px-6 py-2.5 rounded-lg font-medium text-sm transition-all ${
                (step === 'use' && profile.primary_use) ||
                (step === 'audience' && profile.audience) ||
                (step === 'frustration' && profile.ai_frustration)
                  ? 'bg-kira text-white hover:shadow-kira'
                  : 'bg-layer3 text-text-dim cursor-not-allowed'
              }`}
            >
              {step === 'frustration' ? "Let's Go! 🚀" : 'Continue →'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

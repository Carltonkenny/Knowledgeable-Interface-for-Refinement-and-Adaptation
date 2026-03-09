// features/onboarding/components/OnboardingStep.tsx
// Client component — Single question screen
// 'use client' — contains interactive state

'use client'

import { Button } from '@/components/ui'
import type { OnboardingQuestion } from '@/lib/constants'

interface OnboardingStepProps {
  question: OnboardingQuestion
  selectedValues: string[]
  onSelect: (value: string) => void
  onTextChange?: (value: string) => void
  textValue?: string
  onNext: () => void
  isLastStep: boolean
  isLoading: boolean
}

export default function OnboardingStep({
  question,
  selectedValues,
  onSelect,
  onTextChange,
  textValue,
  onNext,
  isLastStep,
  isLoading,
}: OnboardingStepProps) {
  const isSelected = (value: string) => selectedValues.includes(value)
  const canProceedNow = selectedValues.length > 0 || (textValue && textValue.length > 0)

  return (
    <div className="space-y-6">
      {/* Question */}
      <h2 className="text-2xl font-bold text-text-bright text-center max-w-[480px] mx-auto">
        {question.question}
      </h2>

      {/* Options */}
      <div className={`space-y-3 ${
        question.type === 'grid' ? 'grid grid-cols-2 gap-3' :
        question.type === 'list' ? 'flex flex-col' :
        'flex flex-wrap justify-center gap-2'
      }`}>
        {question.options.map((option: { label: string; icon?: string }, index: number) => {
          const selected = isSelected(option.label)

          if (question.type === 'chips') {
            return (
              <button
                key={index}
                onClick={() => onSelect(option.label)}
                className={`px-4 py-2 rounded-full text-sm transition-all duration-150 border ${
                  selected
                    ? 'border-kira bg-[var(--kira-glow)] text-text-bright'
                    : 'border-border-strong bg-layer1 text-text-default hover:border-border-bright'
                }`}
              >
                {option.label}
              </button>
            )
          }

          return (
            <button
              key={index}
              onClick={() => onSelect(option.label)}
              className={`p-4 rounded-xl transition-all duration-150 border text-left ${
                question.type === 'grid' ? '' : 'w-full'
              } ${
                selected
                  ? 'border-kira bg-[var(--kira-glow)] text-text-bright'
                  : 'border-border-strong bg-layer1 text-text-default hover:border-border-bright'
              }`}
            >
              <div className="flex items-center gap-3">
                {option.icon && (
                  <span className="text-2xl">{option.icon}</span>
                )}
                <span className="font-medium">{option.label}</span>
              </div>
            </button>
          )
        })}
      </div>

      {/* Text fallback for chips */}
      {question.hasTextFallback && onTextChange && (
        <div className="mt-4">
          <input
            type="text"
            placeholder={question.textPlaceholder}
            value={textValue || ''}
            onChange={(e) => onTextChange(e.target.value)}
            className="w-full px-4 py-2.5 bg-layer2 border border-border-strong rounded-lg text-text-default placeholder:text-text-dim focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira transition-colors"
          />
        </div>
      )}

      {/* Next button */}
      <div className="pt-4">
        <Button
          type="button"
          variant="primary"
          size="lg"
          onClick={onNext}
          disabled={!canProceedNow || isLoading}
          className="w-full"
        >
          {isLoading ? (
            'Saving...'
          ) : isLastStep ? (
            "Let's go →"
          ) : (
            'Continue →'
          )}
        </Button>
      </div>
    </div>
  )
}

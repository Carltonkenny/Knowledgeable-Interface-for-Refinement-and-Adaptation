// features/onboarding/types.ts
// Onboarding-specific types

export interface OnboardingState {
  step: number
  answers: Record<string, string[]>
  textAnswers: Record<string, string>
  isSubmitting: boolean
  error: string | null
}

export interface OnboardingActions {
  selectOption: (value: string) => void
  setTextAnswer: (value: string) => void
  goNext: () => void
  skip: () => void
}

/**
 * tests/auth-flow.test.tsx
 * ─────────────────────────────────────────────
 * Tests for professional auth flow (T&C → Onboarding)
 *
 * RULES.md Compliance:
 * - Unit tests for individual components
 * - Integration tests for auth flow
 * - Validates user experience
 * ─────────────────────────────────────────────
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import TermsAndConditions from '@/features/auth/components/TermsAndConditions'
import OnboardingWizard from '@/features/onboarding/components/OnboardingWizard'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
}))

// Mock auth functions
jest.mock('@/lib/auth', () => ({
  getSession: jest.fn(),
  signOut: jest.fn(),
  acceptTerms: jest.fn(),
  completeOnboarding: jest.fn(),
  hasAcceptedTerms: jest.fn(),
  hasCompletedOnboarding: jest.fn(),
}))

describe('TermsAndConditions', () => {
  describe('Rendering', () => {
    it('renders T&C modal correctly', () => {
      render(
        <TermsAndConditions
          onAccept={() => {}}
          onDecline={() => {}}
        />
      )

      expect(screen.getByText('Welcome to PromptForge')).toBeInTheDocument()
      expect(screen.getByText('Terms of Service')).toBeInTheDocument()
      expect(screen.getByText('Privacy Policy')).toBeInTheDocument()
    })

    it('renders all three checkboxes', () => {
      render(
        <TermsAndConditions
          onAccept={() => {}}
          onDecline={() => {}}
        />
      )

      expect(screen.getByText(/I am 18 years of age or older/i)).toBeInTheDocument()
      expect(screen.getByText(/I have read and accept the Terms of Service/i)).toBeInTheDocument()
      expect(screen.getByText(/I have read and accept the Privacy Policy/i)).toBeInTheDocument()
    })

    it('renders Accept button disabled initially', () => {
      render(
        <TermsAndConditions
          onAccept={() => {}}
          onDecline={() => {}}
        />
      )

      const acceptButton = screen.getByText('Accept & Continue')
      expect(acceptButton).toBeDisabled()
    })
  })

  describe('Checkbox Interactions', () => {
    it('enables accept button when all checkboxes checked', async () => {
      render(
        <TermsAndConditions
          onAccept={() => {}}
          onDecline={() => {}}
        />
      )

      // Check all boxes
      const checkboxes = screen.getAllByType('checkbox')
      checkboxes.forEach(cb => fireEvent.click(cb))

      // Wait for button to enable
      await waitFor(() => {
        const acceptButton = screen.getByText('Accept & Continue')
        expect(acceptButton).not.toBeDisabled()
      })
    })

    it('calls onAccept when accept button clicked', async () => {
      const onAccept = jest.fn()
      render(
        <TermsAndConditions
          onAccept={onAccept}
          onDecline={() => {}}
        />
      )

      // Check all boxes
      const checkboxes = screen.getAllByType('checkbox')
      checkboxes.forEach(cb => fireEvent.click(cb))

      // Click accept
      const acceptButton = screen.getByText('Accept & Continue')
      fireEvent.click(acceptButton)

      await waitFor(() => {
        expect(onAccept).toHaveBeenCalled()
      })
    })

    it('calls onDecline when decline clicked', () => {
      const onDecline = jest.fn()
      render(
        <TermsAndConditions
          onAccept={() => {}}
          onDecline={onDecline}
        />
      )

      const declineButton = screen.getByText('Decline')
      fireEvent.click(declineButton)

      expect(onDecline).toHaveBeenCalled()
    })
  })

  describe('Individual Checkbox States', () => {
    it('tracks each checkbox independently', () => {
      render(
        <TermsAndConditions
          onAccept={() => {}}
          onDecline={() => {}}
        />
      )

      const checkboxes = screen.getAllByType('checkbox')

      // Check only first box
      fireEvent.click(checkboxes[0])

      // Should still be disabled
      expect(screen.getByText('Accept & Continue')).toBeDisabled()

      // Check second box
      fireEvent.click(checkboxes[1])

      // Should still be disabled
      expect(screen.getByText('Accept & Continue')).toBeDisabled()
    })
  })
})

describe('OnboardingWizard', () => {
  const defaultProps = {
    token: 'test-token',
    apiUrl: 'http://test-api.com',
    onComplete: jest.fn(),
  }

  describe('Step 1: Primary Use', () => {
    it('renders step 1 correctly', () => {
      render(<OnboardingWizard {...defaultProps} />)

      expect(screen.getByText(/What will you use PromptForge for/i)).toBeInTheDocument()
      expect(screen.getByText('Step 1 of 3')).toBeInTheDocument()
    })

    it('shows all use case options', () => {
      render(<OnboardingWizard {...defaultProps} />)

      expect(screen.getByText('Content Creation')).toBeInTheDocument()
      expect(screen.getByText('Coding & Development')).toBeInTheDocument()
      expect(screen.getByText('Research & Analysis')).toBeInTheDocument()
      expect(screen.getByText('Education & Training')).toBeInTheDocument()
      expect(screen.getByText('Business & Communication')).toBeInTheDocument()
      expect(screen.getByText('Creative Writing')).toBeInTheDocument()
    })

    it('enables continue when use case selected', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)

      await waitFor(() => {
        const continueButton = screen.getByText('Continue →')
        expect(continueButton).not.toBeDisabled()
      })
    })

    it('advances to step 2 on continue', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)

      const continueButton = screen.getByText('Continue →')
      fireEvent.click(continueButton)

      await waitFor(() => {
        expect(screen.getByText(/Who is your primary audience/i)).toBeInTheDocument()
      })
    })
  })

  describe('Step 2: Audience', () => {
    it('shows step 2 after step 1', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      // Complete step 1
      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        expect(screen.getByText('Step 2 of 3')).toBeInTheDocument()
      })
    })

    it('shows all audience options', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      // Complete step 1
      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        expect(screen.getByText('Technical Audience')).toBeInTheDocument()
        expect(screen.getByText('Business Professionals')).toBeInTheDocument()
        expect(screen.getByText('General Public')).toBeInTheDocument()
        expect(screen.getByText('Academic')).toBeInTheDocument()
        expect(screen.getByText('Creative Community')).toBeInTheDocument()
      })
    })
  })

  describe('Step 3: Frustrations', () => {
    it('shows step 3 after step 2', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      // Complete step 1
      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        // Complete step 2
        const technicalOption = screen.getByText('Technical Audience').closest('button')
        if (technicalOption) fireEvent.click(technicalOption)
      })

      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        expect(screen.getByText('Step 3 of 3')).toBeInTheDocument()
      })
    })

    it('shows frustration detail textarea', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      // Navigate to step 3
      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        const technicalOption = screen.getByText('Technical Audience').closest('button')
        if (technicalOption) fireEvent.click(technicalOption)
      })
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Anything specific/i)).toBeInTheDocument()
      })
    })

    it('calls onComplete on final submit', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      // Complete all steps
      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        const technicalOption = screen.getByText('Technical Audience').closest('button')
        if (technicalOption) fireEvent.click(technicalOption)
      })
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        const frustrationOption = screen.getByText('AI responses are too vague').closest('button')
        if (frustrationOption) fireEvent.click(frustrationOption)
      })

      const finishButton = screen.getByText("Let's Go! 🚀")
      fireEvent.click(finishButton)

      await waitFor(() => {
        expect(defaultProps.onComplete).toHaveBeenCalled()
      })
    })
  })

  describe('Navigation', () => {
    it('shows back button on step 2', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      // Complete step 1
      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        expect(screen.getByText('← Back')).toBeInTheDocument()
      })
    })

    it('goes back to step 1 from step 2', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      // Complete step 1
      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        const backButton = screen.getByText('← Back')
        fireEvent.click(backButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Step 1 of 3')).toBeInTheDocument()
      })
    })
  })

  describe('Progress Bar', () => {
    it('shows correct progress for each step', async () => {
      render(<OnboardingWizard {...defaultProps} />)

      // Step 1: 33%
      expect(screen.getByText('33% Complete')).toBeInTheDocument()

      // Complete step 1
      const codingOption = screen.getByText('Coding & Development').closest('button')
      if (codingOption) fireEvent.click(codingOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        // Step 2: 66%
        expect(screen.getByText('66% Complete')).toBeInTheDocument()
      })

      // Complete step 2
      const technicalOption = screen.getByText('Technical Audience').closest('button')
      if (technicalOption) fireEvent.click(technicalOption)
      fireEvent.click(screen.getByText('Continue →'))

      await waitFor(() => {
        // Step 3: 100%
        expect(screen.getByText('100% Complete')).toBeInTheDocument()
      })
    })
  })
})

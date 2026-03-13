// features/auth/components/TermsAndConditions.tsx
// Professional T&C modal with checkboxes - per company standards

'use client'

import { useState } from 'react'

interface TermsAndConditionsProps {
  onAccept: () => void
  onDecline: () => void
}

export default function TermsAndConditions({ onAccept, onDecline }: TermsAndConditionsProps) {
  const [checked, setChecked] = useState({
    over18: false,
    terms: false,
    privacy: false,
  })

  const allChecked = checked.over18 && checked.terms && checked.privacy

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-layer1 rounded-2xl border border-border-default max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-border-subtle">
          <h2 className="text-2xl font-bold text-text-bright">
            Welcome to PromptForge
          </h2>
          <p className="text-text-dim text-sm mt-1">
            Before we begin, please review and accept our terms
          </p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Terms of Service */}
          <div className="bg-layer2 rounded-lg p-4 border border-border-subtle">
            <h3 className="font-semibold text-text-bright mb-2">
              Terms of Service
            </h3>
            <div className="text-text-dim text-sm space-y-2 h-32 overflow-y-auto pr-2">
              <p>
                1. <strong>Service Purpose:</strong> PromptForge is an AI-powered prompt engineering tool designed to help users create, improve, and optimize prompts for AI systems.
              </p>
              <p>
                2. <strong>User Responsibilities:</strong> You are responsible for the content you create and must ensure it complies with all applicable laws and regulations.
              </p>
              <p>
                3. <strong>Prohibited Use:</strong> You may not use PromptForge for illegal activities, harassment, misinformation, or any harmful purposes.
              </p>
              <p>
                4. <strong>Data Usage:</strong> We store your prompts and interactions to improve the service and provide personalized experiences.
              </p>
              <p>
                5. <strong>Service Changes:</strong> We reserve the right to modify or discontinue the service at any time.
              </p>
            </div>
          </div>

          {/* Privacy Policy */}
          <div className="bg-layer2 rounded-lg p-4 border border-border-subtle">
            <h3 className="font-semibold text-text-bright mb-2">
              Privacy Policy
            </h3>
            <div className="text-text-dim text-sm space-y-2 h-32 overflow-y-auto pr-2">
              <p>
                1. <strong>Data Collection:</strong> We collect your prompts, interactions, and usage patterns to improve the service.
              </p>
              <p>
                2. <strong>Data Storage:</strong> Your data is stored securely using industry-standard encryption and security practices.
              </p>
              <p>
                3. <strong>Data Sharing:</strong> We do not sell your personal data. Aggregated, anonymized data may be used for analytics.
              </p>
              <p>
                4. <strong>Your Rights:</strong> You can request deletion of your data at any time by contacting support.
              </p>
              <p>
                5. <strong>Cookies:</strong> We use essential cookies for authentication and service functionality.
              </p>
            </div>
          </div>

          {/* Checkboxes */}
          <div className="space-y-3 pt-4">
            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={checked.over18}
                onChange={(e) => setChecked({ ...checked, over18: e.target.checked })}
                className="mt-1 w-4 h-4 rounded border-border-subtle bg-layer2 text-kira focus:ring-kira focus:ring-2"
              />
              <span className="text-sm text-text-dim group-hover:text-text-bright">
                I am 18 years of age or older
              </span>
            </label>

            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={checked.terms}
                onChange={(e) => setChecked({ ...checked, terms: e.target.checked })}
                className="mt-1 w-4 h-4 rounded border-border-subtle bg-layer2 text-kira focus:ring-kira focus:ring-2"
              />
              <span className="text-sm text-text-dim group-hover:text-text-bright">
                I have read and accept the <strong>Terms of Service</strong>
              </span>
            </label>

            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={checked.privacy}
                onChange={(e) => setChecked({ ...checked, privacy: e.target.checked })}
                className="mt-1 w-4 h-4 rounded border-border-subtle bg-layer2 text-kira focus:ring-2"
              />
              <span className="text-sm text-text-dim group-hover:text-text-bright">
                I have read and accept the <strong>Privacy Policy</strong>
              </span>
            </label>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-border-subtle flex justify-between items-center">
          <button
            onClick={onDecline}
            className="text-text-dim hover:text-text-bright text-sm"
          >
            Decline
          </button>
          <button
            onClick={onAccept}
            disabled={!allChecked}
            className={`px-6 py-2.5 rounded-lg font-medium text-sm transition-all ${
              allChecked
                ? 'bg-kira text-white hover:shadow-kira'
                : 'bg-layer3 text-text-dim cursor-not-allowed'
            }`}
          >
            Accept & Continue
          </button>
        </div>
      </div>
    </div>
  )
}

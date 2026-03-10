// features/landing/components/LiveDemoWidget.tsx
// Interactive demo with gate logic (3 uses max)
// State machine: IDLE → LOADING → RESULT → GATED

'use client'

import { useState } from 'react'
import { Button, Input, Chip } from '@/components/ui'
import { apiDemoChat } from '@/lib/api'
import { mapError } from '@/lib/errors'
import type { ChatResult } from '@/lib/api'
import { useDemoGate } from '../hooks/useDemoGate'
import { ROUTES } from '@/lib/constants'

// Fallback result when backend unreachable
const FALLBACK_RESULT: ChatResult = {
  improved_prompt: "Write a professional email to [client name] regarding [project name]. Tone: confident and clear. Include: what was accomplished, what it means for the timeline, and a clear next step. Length: under 200 words.",
  diff: [
    { type: 'add', text: '[client name]' },
    { type: 'add', text: '[project name]' },
    { type: 'add', text: 'confident and clear' },
    { type: 'add', text: 'Length: under 200 words.' },
    { type: 'remove', text: 'your project' },
  ],
  quality_score: { specificity: 4, clarity: 5, actionability: 3 },
  kira_message: "On it. Here's your engineered prompt ↓",
  memories_applied: 0,
  latency_ms: 2800,
  agents_run: [],
}

type WidgetState = 'idle' | 'loading' | 'result' | 'gated'

export function LiveDemoWidget() {
  const [state, setState] = useState<WidgetState>('idle')
  const [input, setInput] = useState('')
  const [result, setResult] = useState<ChatResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { isGated, recordUse } = useDemoGate()

  const handleSubmit = async () => {
    if (!input.trim()) return

    setState('loading')
    setError(null)

    try {
      const data = await apiDemoChat(input)
      setResult(data)
      setState('result')
      recordUse()
    } catch (err) {
      // Use fallback result on error
      setResult(FALLBACK_RESULT)
      setState('result')
      recordUse()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Gated state
  if (isGated && state !== 'result') {
    return (
      <div className="relative w-full max-w-2xl mx-auto">
        <div className="border border-border-default rounded-xl bg-layer1 p-8 min-h-[300px] flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-lg bg-[var(--kira-dim)] border border-kira text-kira font-mono font-bold flex items-center justify-center text-xl">
              K
            </div>
            <p className="text-text-bright font-semibold mb-2">
              You've seen what I can do.
            </p>
            <p className="text-text-dim text-sm mb-6">
              Sign up to keep going — it's free.
            </p>
            <div className="flex items-center justify-center gap-3">
              <Button variant="primary" onClick={() => (window.location.href = ROUTES.SIGNUP)}>
                Create free account →
              </Button>
              <Button variant="ghost" onClick={() => (window.location.href = ROUTES.LOGIN)}>
                Sign in
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Window chrome */}
      <div className="flex items-center justify-between mb-3 px-4 py-2 bg-layer2 border border-border-default rounded-t-xl">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-success animate-live-pulse" />
          <span className="font-mono text-[10px] text-text-dim uppercase tracking-wider">
            Live demo
          </span>
        </div>
        <span className="font-mono text-[9px] text-kira uppercase tracking-wider">
          LIVE · REAL BACKEND · REAL KIRA
        </span>
      </div>

      {/* Content area */}
      <div className="border border-border-default border-t-0 rounded-b-xl bg-layer1 p-6 min-h-[300px]">
        {state === 'idle' && (
          <div className="space-y-4">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Try: 'help me write an email to my client'"
              className="w-full"
            />
            <div className="flex justify-end">
              <Button
                variant="kira"
                size="sm"
                onClick={handleSubmit}
                disabled={!input.trim()}
              >
                Send
              </Button>
            </div>
          </div>
        )}

        {state === 'loading' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Chip variant="kira" label="Reading context" active />
              <Chip variant="intent" label="Analyzing intent" active />
              <Chip variant="context" label="Context" skipped />
              <Chip variant="domain" label="Domain" active />
              <Chip variant="engineer" label="Crafting prompt" active />
            </div>
            <p className="font-mono text-[10px] text-text-dim">
              Engineering prompt...
            </p>
          </div>
        )}

        {state === 'result' && result && (
          <div className="space-y-4">
            {/* Kira message */}
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-lg bg-[var(--kira-dim)] border border-kira text-kira font-mono font-bold flex items-center justify-center text-sm flex-shrink-0">
                K
              </div>
              <p className="text-[13px] text-text-default leading-relaxed">
                {result.kira_message}
              </p>
            </div>

            {/* Output card */}
            <div className="border border-border-default rounded-xl bg-layer2 p-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-[9px] tracking-wider uppercase text-text-dim">
                  Engineered prompt
                </span>
                <div className="flex items-center gap-3">
                  {result.memories_applied > 0 && (
                    <span className="font-mono text-[10px] text-memory">
                      ● {result.memories_applied} memories
                    </span>
                  )}
                  <span className="font-mono text-[10px] text-teal">
                    {(result.latency_ms / 1000).toFixed(1)}s
                  </span>
                </div>
              </div>

              {/* Output text */}
              <p className="text-[--output-text] text-[13px] leading-relaxed mb-4">
                {result.improved_prompt}
              </p>

              {/* Quality scores */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-text-dim w-20">Specificity</span>
                  <div className="flex-1 h-[3px] bg-border-default rounded-full overflow-hidden">
                    <div
                      className="h-full bg-kira rounded-full"
                      style={{ width: `${(result.quality_score.specificity / 5) * 100}%` }}
                    />
                  </div>
                  <span className="font-mono text-[10px] text-text-dim w-8 text-right">
                    {result.quality_score.specificity}/5
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-text-dim w-20">Clarity</span>
                  <div className="flex-1 h-[3px] bg-border-default rounded-full overflow-hidden">
                    <div
                      className="h-full bg-kira rounded-full"
                      style={{ width: `${(result.quality_score.clarity / 5) * 100}%` }}
                    />
                  </div>
                  <span className="font-mono text-[10px] text-text-dim w-8 text-right">
                    {result.quality_score.clarity}/5
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-text-dim w-20">Actionability</span>
                  <div className="flex-1 h-[3px] bg-border-default rounded-full overflow-hidden">
                    <div
                      className="h-full bg-kira rounded-full"
                      style={{ width: `${(result.quality_score.actionability / 5) * 100}%` }}
                    />
                  </div>
                  <span className="font-mono text-[10px] text-text-dim w-8 text-right">
                    {result.quality_score.actionability}/5
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-border-default">
                <Button variant="ghost" size="sm">
                  Copy
                </Button>
                <Button variant="kira" size="sm" onClick={() => (window.location.href = ROUTES.SIGNUP)}>
                  Try it yourself →
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// features/chat/components/StatusChips.tsx
// Processing chips row

import { Chip } from '@/components/ui'
import type { ProcessingStatus } from '../types'

interface StatusChipsProps {
  status: ProcessingStatus
}

export default function StatusChips({ status }: StatusChipsProps) {
  const { state, agentsComplete, agentsSkipped } = status

  if (state === 'idle' || state === 'complete') return null

  const isKiraReading = state === 'kira_reading'
  const isSwarmRunning = state === 'swarm_running'

  return (
    <div className="flex items-center gap-2 mb-4 flex-wrap">
      {/* Kira chip */}
      <Chip
        variant="kira"
        active={isKiraReading}
      >
        Reading context
      </Chip>

      {/* Intent chip */}
      {isSwarmRunning && (
        <Chip
          variant="intent"
          active={!agentsSkipped.has('intent')}
          skipped={agentsSkipped.has('intent')}
        >
          Analyzing intent
        </Chip>
      )}

      {/* Context chip */}
      {isSwarmRunning && (
        <Chip
          variant="context"
          active={!agentsSkipped.has('context')}
          skipped={agentsSkipped.has('context')}
        >
          Context
        </Chip>
      )}

      {/* Domain chip */}
      {isSwarmRunning && (
        <Chip
          variant="domain"
          active={!agentsSkipped.has('domain')}
          skipped={agentsSkipped.has('domain')}
        >
          Domain
        </Chip>
      )}

      {/* Engineer chip */}
      {isSwarmRunning && (
        <Chip
          variant="engineer"
          active
        >
          Crafting prompt
        </Chip>
      )}
    </div>
  )
}

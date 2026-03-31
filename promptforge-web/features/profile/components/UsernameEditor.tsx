'use client'

import { useState } from 'react'
import { User, Check, X, Edit2, Loader2 } from 'lucide-react'

interface UsernameEditorProps {
  initialUsername?: string | null
  isUpdating: boolean
  onSave: (val: string) => Promise<boolean>
  tier?: 'Bronze' | 'Silver' | 'Gold' | 'Kira'
  trustLevel: number // 0, 1, 2
}

export default function UsernameEditor({ initialUsername, isUpdating, onSave, tier = 'Bronze', trustLevel }: UsernameEditorProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [value, setValue] = useState(initialUsername || '')
  const [error, setError] = useState<string | null>(null)

  const trustLabels = ['COLD', 'WARM', 'HOT']
  const trustColors = ['bg-blue-500', 'bg-purple-500', 'bg-kira']
  const tierColors: Record<string, string> = {
    Bronze: 'from-orange-400 to-orange-700',
    Silver: 'from-slate-300 to-slate-500',
    Gold: 'from-yellow-300 to-yellow-600',
    Kira: 'from-kira to-kira-dim shadow-[0_0_10px_rgba(var(--color-kira),0.5)]'
  }

  const handleSave = async () => {
    if (!value.trim()) {
      setError('Username cannot be empty')
      return
    }
    if (value.trim().length < 3) {
      setError('Must be at least 3 characters')
      return
    }
    setError(null)
    try {
      const success = await onSave(value.trim())
      if (success) {
        setIsEditing(false)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update username')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      setIsEditing(false)
      setValue(initialUsername || '')
      setError(null)
    }
  }

  return (
    <div className="bg-layer2 rounded-xl p-5 border border-border-subtle hover:border-border-muted transition-colors group">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-layer3 text-text-muted group-hover:text-kira transition-colors">
            <User size={18} />
          </div>
          <div>
            <p className="text-[10px] text-text-dim uppercase tracking-wider font-semibold mb-1">
              Digital Identity
            </p>
            {isEditing ? (
              <div className="relative">
                <input
                  id="username-input"
                  name="username"
                  type="text"
                  value={value}
                  onChange={(e) => {
                    setValue(e.target.value)
                    if (error) setError(null)
                  }}
                  onKeyDown={handleKeyDown}
                  disabled={isUpdating}
                  autoFocus
                  autoComplete="username"
                  className="bg-layer2 border border-kira/50 text-text-bright text-sm rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-kira/20 w-48 font-mono placeholder:text-text-dim"
                  placeholder="Enter username..."
                  style={{ color: 'var(--color-text-bright)' }}
                />
                {error && (
                  <span className="absolute -bottom-5 left-0 text-[10px] text-intent whitespace-nowrap">
                    {error}
                  </span>
                )}
              </div>
            ) : (
              <div className="flex flex-col">
                <h3 className="text-base font-medium text-text-bright flex items-center gap-2 group-hover:text-kira transition-colors">
                  {initialUsername ? `@${initialUsername}` : 'Set Username'}
                  <div className={`text-[9px] px-1.5 py-0.5 rounded font-bold text-white bg-gradient-to-br ${tierColors[tier]}`}>
                    {tier.toUpperCase()}
                  </div>
                </h3>
                
                {/* Trust Level Indicator */}
                <div className="mt-2 flex items-center gap-2">
                  <div className="w-24 h-1 bg-layer3 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-1000 ${trustColors[trustLevel]}`} 
                      style={{ width: `${((trustLevel + 1) / 3) * 100}%` }}
                    />
                  </div>
                  <span className={`text-[8px] font-mono font-bold ${trustLevel === 2 ? 'text-kira animate-pulse' : 'text-text-dim'}`}>
                    {trustLabels[trustLevel]} SYNC
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSave}
                disabled={isUpdating || !value.trim()}
                className="p-1.5 rounded-md hover:bg-success/10 text-success transition-colors disabled:opacity-50"
                title="Save Changes"
              >
                {isUpdating ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
              </button>
              <button
                onClick={() => {
                  setIsEditing(false)
                  setValue(initialUsername || '')
                  setError(null)
                }}
                disabled={isUpdating}
                className="p-1.5 rounded-md hover:bg-intent/10 text-intent transition-colors disabled:opacity-50"
                title="Cancel"
              >
                <X size={16} />
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="p-1.5 rounded-md hover:bg-layer3 text-text-dim hover:text-text-bright transition-colors"
              title="Edit Username"
            >
              <Edit2 size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

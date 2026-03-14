'use client'

import { useState } from 'react'
import { User, Check, X, Edit2, Loader2 } from 'lucide-react'

interface UsernameEditorProps {
  initialUsername?: string
  isUpdating: boolean
  onSave: (val: string) => Promise<boolean>
}

export default function UsernameEditor({ initialUsername, isUpdating, onSave }: UsernameEditorProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [value, setValue] = useState(initialUsername || '')
  const [error, setError] = useState<string | null>(null)

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
    } catch (err: any) {
      setError(err.message || 'Failed to update username')
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
                  type="text"
                  value={value}
                  onChange={(e) => {
                    setValue(e.target.value)
                    if (error) setError(null)
                  }}
                  onKeyDown={handleKeyDown}
                  disabled={isUpdating}
                  autoFocus
                  className="bg-layer1 border border-primary/50 text-text-bright text-sm rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/20 w-48 font-mono"
                  placeholder="Enter username..."
                />
                {error && (
                  <span className="absolute -bottom-5 left-0 text-[10px] text-intent whitespace-nowrap">
                    {error}
                  </span>
                )}
              </div>
            ) : (
              <h3 className="text-base font-medium text-text-bright flex items-center gap-2">
                {initialUsername ? `@${initialUsername}` : 'Set Username'}
              </h3>
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

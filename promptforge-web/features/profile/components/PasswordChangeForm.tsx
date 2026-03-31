'use client'

import { useState } from 'react'
import { Lock, Eye, EyeOff, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'

interface PasswordChangeFormProps {
  token: string
}

export default function PasswordChangeForm({ token }: PasswordChangeFormProps) {
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  })
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const passwordStrength = (password: string) => {
    let score = 0
    if (password.length >= 8) score++
    if (/[a-z]/.test(password)) score++
    if (/[A-Z]/.test(password)) score++
    if (/[0-9]/.test(password)) score++
    if (/[^a-zA-Z0-9]/.test(password)) score++
    return score
  }

  const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']
  const strengthColors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-blue-500', 'bg-green-500']
  const currentStrength = passwordStrength(formData.new_password)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage(null)

    if (formData.new_password !== formData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' })
      return
    }

    if (formData.new_password.length < 8) {
      setMessage({ type: 'error', text: 'Password must be at least 8 characters' })
      return
    }

    setIsLoading(true)

    try {
      const form = new FormData()
      form.append('current_password', formData.current_password)
      form.append('new_password', formData.new_password)

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user/change-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: form
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to change password')
      }

      setMessage({ type: 'success', text: 'Password updated successfully' })
      setFormData({ current_password: '', new_password: '', confirm_password: '' })
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to change password' })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-6 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Current Password */}
        <div>
          <label className="block text-xs font-mono font-bold text-text-dim uppercase tracking-widest mb-2">
            Current Password
          </label>
          <div className="relative">
            <input
              type={showPasswords.current ? 'text' : 'password'}
              value={formData.current_password}
              onChange={(e) => setFormData({ ...formData, current_password: e.target.value })}
              className="w-full bg-layer1/60 border border-border-default/50 rounded-xl px-4 py-3 pr-10 text-sm font-mono text-kira focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] placeholder:text-text-dim/50"
              placeholder="••••••••"
              required
            />
            <button
              type="button"
              onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-dim hover:text-kira transition-colors"
            >
              {showPasswords.current ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        {/* New Password */}
        <div>
          <label className="block text-xs font-mono font-bold text-kira/80 uppercase tracking-widest mb-2">
            New Password
          </label>
          <div className="relative">
            <input
              type={showPasswords.new ? 'text' : 'password'}
              value={formData.new_password}
              onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
              className="w-full bg-layer1/60 border border-border-default/50 rounded-xl px-4 py-3 pr-10 text-sm font-mono text-kira focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] placeholder:text-text-dim/50"
              placeholder="[Enter new security sequence]"
              required
              minLength={8}
            />
            <button
              type="button"
              onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-dim hover:text-kira transition-colors"
            >
              {showPasswords.new ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          
          {/* Password Strength Meter */}
          {formData.new_password && (
            <div className="mt-3 bg-layer1/30 p-3 rounded-lg border border-border-default/50">
              <div className="flex items-center gap-3 mb-1.5">
                <div className="flex-1 flex gap-1 h-1.5">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <div
                      key={level}
                      className={`flex-1 rounded-full transition-all duration-300 ${
                        level <= currentStrength
                          ? strengthColors[currentStrength - 1].replace('bg-', 'bg-').concat(' shadow-[0_0_5px_currentColor]')
                          : 'bg-layer3/50'
                      }`}
                    />
                  ))}
                </div>
                <span className={`text-[10px] font-bold font-mono tracking-wider uppercase whitespace-nowrap ${
                  strengthColors[currentStrength - 1].replace('bg-', 'text-')
                }`}>
                  {strengthLabels[currentStrength - 1] || 'Very Weak'}
                </span>
              </div>
              <p className="text-[9px] font-mono text-text-dim/70">
                RECOMMENDATION: 8+ CHARS // ALPHA-NUMERIC // SYMBOLS
              </p>
            </div>
          )}
        </div>

        {/* Confirm Password */}
        <div>
          <label className="block text-xs font-mono font-bold text-kira/80 uppercase tracking-widest mb-2 mt-4">
            Verify Sequence
          </label>
          <div className="relative">
            <input
              type={showPasswords.confirm ? 'text' : 'password'}
              value={formData.confirm_password}
              onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
              className="w-full bg-layer1/60 border border-border-default/50 rounded-xl px-4 py-3 pr-10 text-sm font-mono text-kira focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] placeholder:text-text-dim/50"
              placeholder="[Re-enter sequence]"
              required
            />
            <button
              type="button"
              onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-dim hover:text-kira transition-colors"
            >
              {showPasswords.confirm ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`flex items-center gap-2 p-3 rounded-lg text-sm ${
            message.type === 'success'
              ? 'bg-success/10 text-success border border-success/20'
              : 'bg-intent/10 text-intent border border-intent/20'
          }`}>
            {message.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            {message.text}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="group relative w-full flex items-center justify-center gap-2 px-6 py-3.5 mt-6 rounded-xl bg-kira/20 border border-kira text-kira text-sm font-bold hover:bg-kira hover:text-white transition-all overflow-hidden shadow-[0_0_15px_rgba(var(--color-kira),0.3)] hover:shadow-[0_0_30px_rgba(var(--color-kira),0.8)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-[200%] group-hover:animate-[wave_1s_ease-in-out_infinite]" />
          {isLoading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              <span className="uppercase tracking-widest font-mono">Updating Keys...</span>
            </>
          ) : (
            <>
              <Lock size={18} />
              <span className="uppercase tracking-widest font-mono">Update Security Protocol</span>
            </>
          )}
        </button>
      </form>
    </div>
  )
}

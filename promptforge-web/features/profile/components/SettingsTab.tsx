'use client'

import { useState, useEffect } from 'react'
import { Settings, Globe, Lock, Clock, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'
import { apiGetSettings, apiUpdateSettings } from '@/lib/api'
import { logger } from '@/lib/logger'

interface SettingsTabProps {
  token: string
}

interface UserSettings {
  is_public: boolean
  default_tone: string
  default_audience: string
  session_timeout_hours: number
}

export default function SettingsTab({ token }: SettingsTabProps) {
  const [settings, setSettings] = useState<UserSettings>({
    is_public: false,
    default_tone: 'direct',
    default_audience: 'personal',
    session_timeout_hours: 24
  })
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadSettings()
  }, [token])

  const loadSettings = async () => {
    try {
      const data = await apiGetSettings(token)
      setSettings(data)
    } catch (error) {
      logger.error('Failed to load settings', { error })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    setMessage(null)

    try {
      await apiUpdateSettings(token, settings)
      setMessage({ type: 'success', text: 'Settings saved successfully' })
    } catch (error) {
      logger.error('Failed to save settings', { error })
      setMessage({ type: 'error', text: 'Failed to save settings' })
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="bg-layer2 rounded-2xl border border-border-subtle p-8 text-center">
        <Loader2 size={24} className="animate-spin mx-auto mb-3 text-kira" />
        <p className="text-sm text-text-dim">Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-kira/20 text-kira border border-kira/30 shadow-[0_0_10px_rgba(var(--color-kira),0.5)]">
            <Settings size={20} className="animate-[spin_4s_linear_infinite]" />
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-widest text-text-bright uppercase">System Configuration</h2>
            <p className="text-sm font-mono text-kira/70">Manage your neural preferences</p>
          </div>
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

      {/* Privacy Settings */}
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-kira/10 text-kira">
            <Globe size={18} />
          </div>
          <h3 className="text-sm font-bold tracking-wider text-text-bright uppercase">Network Privacy</h3>
        </div>

        <div className="space-y-4">
          <label className="flex items-center justify-between p-4 rounded-xl bg-layer1/60 border border-border-default/50 cursor-pointer hover:border-kira/50 transition-colors shadow-[inset_0_0_10px_rgba(0,0,0,0.2)]">
            <div className="flex items-center gap-4">
              <div className={`p-2 rounded-lg transition-colors ${settings.is_public ? 'bg-kira/20 text-kira shadow-[0_0_10px_rgba(var(--color-kira),0.5)]' : 'bg-layer3/50 text-text-dim'}`}>
                <Globe size={16} />
              </div>
              <div>
                <p className={`text-sm font-bold font-mono uppercase tracking-tight transition-colors ${settings.is_public ? 'text-kira drop-shadow-[0_0_5px_rgba(var(--color-kira),0.5)]' : 'text-text-bright'}`}>Public Profile Broadcast</p>
                <p className="text-xs text-text-dim mt-0.5">Allow matrix entities to view your profile via direct link</p>
              </div>
            </div>
            
            {/* Cybernetic Toggle */}
            <div className="relative flex items-center">
              <input
                type="checkbox"
                checked={settings.is_public}
                onChange={(e) => setSettings({ ...settings, is_public: e.target.checked })}
                className="sr-only"
              />
              <div className={`w-12 h-6 rounded-full transition-all duration-300 ease-in-out flex items-center px-1 ${
                settings.is_public 
                  ? 'bg-kira/30 border border-kira/50 shadow-[0_0_15px_rgba(var(--color-kira),0.6)]' 
                  : 'bg-layer3 border border-border-subtle'
              }`}>
                <div className={`w-4 h-4 rounded-full bg-white transition-all duration-300 ease-in-out shadow-sm ${
                  settings.is_public ? 'translate-x-6 shadow-[0_0_10px_#fff]' : 'translate-x-0 opacity-50'
                }`} />
              </div>
            </div>
          </label>
        </div>
      </div>

      {/* Default Prompt Settings */}
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-kira/10 text-kira">
            <Settings size={18} />
          </div>
          <h3 className="text-sm font-bold tracking-wider text-text-bright uppercase">Prompt Defaults</h3>
        </div>

        <div className="space-y-5">
          <div>
            <label className="block text-xs font-mono font-bold text-kira/80 uppercase tracking-widest mb-2">
              Default Output Tone
            </label>
            <div className="relative">
              <select
                value={settings.default_tone}
                onChange={(e) => setSettings({ ...settings, default_tone: e.target.value })}
                className="w-full bg-layer1/60 border border-kira/30 rounded-xl px-4 py-3 text-sm font-mono text-text-bright focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] appearance-none cursor-pointer"
              >
                <option value="direct" className="bg-layer1">Direct</option>
                <option value="friendly" className="bg-layer1">Friendly</option>
                <option value="formal" className="bg-layer1">Formal</option>
                <option value="casual" className="bg-layer1">Casual</option>
                <option value="professional" className="bg-layer1">Professional</option>
              </select>
              <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-kira">
                ▼
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono font-bold text-kira/80 uppercase tracking-widest mb-2">
              Default Target Audience
            </label>
            <div className="relative">
              <select
                value={settings.default_audience}
                onChange={(e) => setSettings({ ...settings, default_audience: e.target.value })}
                className="w-full bg-layer1/60 border border-kira/30 rounded-xl px-4 py-3 text-sm font-mono text-text-bright focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] appearance-none cursor-pointer"
              >
                <option value="personal" className="bg-layer1">Personal</option>
                <option value="professional" className="bg-layer1">Professional</option>
                <option value="academic" className="bg-layer1">Academic</option>
                <option value="technical" className="bg-layer1">Technical</option>
              </select>
              <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-kira">
                ▼
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Session Settings */}
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-kira/10 text-kira">
            <Clock size={18} />
          </div>
          <h3 className="text-sm font-bold tracking-wider text-text-bright uppercase">Session Control</h3>
        </div>

        <div>
          <label className="block text-xs font-mono font-bold text-kira/80 uppercase tracking-widest mb-2">
            Auto-Disconnect Timeout
          </label>
          <div className="relative">
            <select
              value={settings.session_timeout_hours}
              onChange={(e) => setSettings({ ...settings, session_timeout_hours: parseInt(e.target.value) })}
              className="w-full bg-layer1/60 border border-kira/30 rounded-xl px-4 py-3 text-sm font-mono text-kira focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] appearance-none cursor-pointer"
            >
              <option value={1} className="bg-layer1">1 Hour</option>
              <option value={24} className="bg-layer1">24 Hours</option>
              <option value={168} className="bg-layer1">7 Days</option>
              <option value={720} className="bg-layer1">30 Days</option>
            </select>
            <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-kira">
              ▼
            </div>
          </div>
          <p className="text-xs font-mono text-text-dim mt-2 bg-layer1/30 px-3 py-2 rounded-lg border border-border-subtle inline-block">
            <span className="text-kira mr-2">ℹ</span>
            Connection severed automatically after inactivity
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end mt-8">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="group relative flex items-center gap-2 px-8 py-3 rounded-xl bg-kira/20 border border-kira text-kira text-sm font-bold hover:bg-kira hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden shadow-[0_0_15px_rgba(var(--color-kira),0.3)] hover:shadow-[0_0_30px_rgba(var(--color-kira),0.8)]"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-[200%] group-hover:animate-[wave_1s_ease-in-out_infinite]" />
          {isSaving ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              <span className="uppercase tracking-widest">Applying...</span>
            </>
          ) : (
            <>
              <CheckCircle2 size={18} />
              <span className="uppercase tracking-widest">Apply Configuration</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import { Shield, Lock, LogOut, Smartphone, Monitor, Globe, CheckCircle2, AlertCircle } from 'lucide-react'
import { motion } from 'framer-motion'
import PasswordChangeForm from './PasswordChangeForm'
import ActiveSessionsList from './ActiveSessionsList'

interface SecurityTabProps {
  token: string
}

export default function SecurityTab({ token }: SecurityTabProps) {
  const [activeSection, setActiveSection] = useState<'password' | 'sessions'>('password')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-intent/20 text-intent border border-intent/30 shadow-[0_0_10px_rgba(var(--color-intent),0.5)]">
            <Shield size={20} className="animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-widest text-text-bright uppercase">System Security</h2>
            <p className="text-sm font-mono text-intent/70">Access controls and neural links</p>
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveSection('password')}
          className={`relative flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors z-10 ${
            activeSection === 'password' ? 'text-kira' : 'text-text-dim hover:text-text-bright hover:bg-layer3/50'
          }`}
        >
          {activeSection === 'password' && (
            <motion.div
              layoutId="activeSecurityTab"
              className="absolute inset-0 bg-kira/10 border border-kira/30 rounded-xl -z-10 shadow-[0_0_15px_rgba(var(--color-kira),0.15)]"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
          <Lock size={16} />
          <span className="font-mono uppercase tracking-wider text-xs">Auth Protocol</span>
        </button>
        <button
          onClick={() => setActiveSection('sessions')}
          className={`relative flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors z-10 ${
            activeSection === 'sessions' ? 'text-kira' : 'text-text-dim hover:text-text-bright hover:bg-layer3/50'
          }`}
        >
          {activeSection === 'sessions' && (
            <motion.div
              layoutId="activeSecurityTab"
              className="absolute inset-0 bg-kira/10 border border-kira/30 rounded-xl -z-10 shadow-[0_0_15px_rgba(var(--color-kira),0.15)]"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
          <LogOut size={16} />
          <span className="font-mono uppercase tracking-wider text-xs">Active Links</span>
        </button>
      </div>

      {/* Section Content */}
      {activeSection === 'password' ? (
        <PasswordChangeForm token={token} />
      ) : (
        <ActiveSessionsList token={token} />
      )}
    </div>
  )
}

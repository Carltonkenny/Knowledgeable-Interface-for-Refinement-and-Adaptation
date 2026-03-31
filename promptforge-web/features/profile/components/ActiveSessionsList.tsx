'use client'

import { useState, useEffect } from 'react'
import { LogOut, Monitor, Smartphone, Globe, MapPin, Clock, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'

interface Session {
  id: string
  device: string
  browser: string
  location: string
  last_active: string
  is_current: boolean
}

interface ActiveSessionsListProps {
  token: string
}

export default function ActiveSessionsList({ token }: ActiveSessionsListProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [revokingId, setRevokingId] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadSessions()
  }, [token])

  const loadSessions = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to load sessions')
      }

      setSessions(data.sessions || [])
    } catch (error: any) {
      console.error('Failed to load sessions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRevoke = async (sessionId: string) => {
    if (sessionId === 'current') return
    
    setRevokingId(sessionId)
    setMessage(null)

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/user/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to revoke session')
      }

      setMessage({ type: 'success', text: 'Session revoked successfully' })
      setSessions(sessions.filter(s => s.id !== sessionId))
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to revoke session' })
    } finally {
      setRevokingId(null)
    }
  }

  const getDeviceIcon = (device: string) => {
    return device.toLowerCase().includes('mobile') ? (
      <Smartphone size={16} />
    ) : (
      <Monitor size={16} />
    )
  }

  const formatLastActive = (isoString: string) => {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  if (isLoading) {
    return (
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-8 text-center shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
        <Loader2 size={24} className="animate-spin mx-auto mb-3 text-kira" />
        <p className="text-sm font-mono text-kira/70 uppercase">Scanning Links...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Info Card */}
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 p-5 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
        <div className="flex items-start gap-4">
          <div className="p-2.5 rounded-lg bg-intent/10 text-intent border border-intent/20">
            <LogOut size={18} />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-bold font-mono tracking-widest text-text-bright uppercase mb-1">Active Neural Links</h3>
            <p className="text-xs text-text-dim">
              Authorized endpoints transmitting to your profile. Terminate unrecognized vectors immediately.
            </p>
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

      {/* Sessions List */}
      <div className="bg-layer2/40 backdrop-blur-xl rounded-2xl border border-border-default/50 divide-y divide-border-default/30 shadow-[0_4px_20px_rgba(0,0,0,0.5)] overflow-hidden">
        {sessions.length === 0 ? (
          <div className="p-8 text-center">
            <Globe size={32} className="mx-auto mb-3 text-kira/30" />
            <p className="text-sm font-mono text-kira/50 uppercase">No active links detected</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between p-5 hover:bg-layer1/50 transition-colors gap-4 sm:gap-0"
            >
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl ${session.is_current ? 'bg-kira/20 text-kira border border-kira/30 shadow-[0_0_10px_rgba(var(--color-kira),0.4)]' : 'bg-layer1/80 text-text-dim border border-border-default'}`}>
                  {getDeviceIcon(session.device)}
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <p className="text-sm font-bold font-mono text-text-bright">
                      {session.browser.toUpperCase()} // {session.device.toUpperCase()}
                    </p>
                    {session.is_current && (
                      <span className="text-[9px] px-2 py-0.5 rounded border border-kira text-kira font-bold uppercase tracking-widest shadow-[0_0_5px_rgba(var(--color-kira),0.5)]">
                        Origin
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-4 mt-1.5 text-xs text-text-dim font-mono">
                    <span className="flex items-center gap-1.5">
                      <MapPin size={12} className={session.is_current ? 'text-kira/70' : ''} />
                      {session.location.toUpperCase()}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock size={12} className={session.is_current ? 'text-kira/70' : ''} />
                      {formatLastActive(session.last_active).toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              {!session.is_current && (
                <button
                  onClick={() => handleRevoke(session.id)}
                  disabled={revokingId === session.id}
                  className="flex justify-center items-center gap-2 px-4 py-2 rounded-lg bg-intent/10 border border-intent/30 text-intent text-xs font-bold hover:bg-intent/20 hover:shadow-[0_0_15px_rgba(var(--color-intent),0.6)] transition-all disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-widest"
                >
                  {revokingId === session.id ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Terminating...
                    </>
                  ) : (
                    <>
                      <LogOut size={14} />
                      Terminate
                    </>
                  )}
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Revoke All Button */}
      {sessions.some(s => !s.is_current) && (
        <div className="flex justify-end">
          <button
            onClick={() => {
              sessions.filter(s => !s.is_current).forEach(s => handleRevoke(s.id))
            }}
            disabled={revokingId !== null}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-intent/10 border border-intent text-intent text-xs font-bold hover:bg-intent hover:text-white hover:shadow-[0_0_20px_rgba(var(--color-intent),0.8)] transition-all disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-widest"
          >
            <AlertCircle size={16} />
            Execute protocol: PURGE_ALL
          </button>
        </div>
      )}
    </div>
  )
}

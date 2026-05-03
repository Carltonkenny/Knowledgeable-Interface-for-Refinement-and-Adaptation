// features/profile/components/McpTokenSection.tsx
// MCP token generation, listing, and revocation

'use client'
import { logger } from '@/lib/logger'

import { useState, useEffect } from 'react'
import { Key, Copy, Check, Trash2, Loader2, ShieldAlert, Cpu, Terminal, ExternalLink } from 'lucide-react'
import { apiMcpGenerateToken, apiMcpListTokens, apiMcpRevokeToken } from '@/lib/api'
import type { McpToken } from '@/lib/api'

interface McpTokenSectionProps {
  sessionCount: number
  trustLevel: 0 | 1 | 2
  authToken: string
}

export default function McpTokenSection({ sessionCount, trustLevel, authToken }: McpTokenSectionProps) {
  const [generatedToken, setGeneratedToken] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [tokens, setTokens] = useState<McpToken[]>([])
  const [loadingTokens, setLoadingTokens] = useState(true)
  const [revokingId, setRevokingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeConfigTab, setActiveConfigTab] = useState<'claude' | 'cursor'>('claude')
  const [os, setOs] = useState<'win' | 'mac' | 'linux'>('win')

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const platform = window.navigator.userAgent.toLowerCase()
      if (platform.includes('mac')) setOs('mac')
      else if (platform.includes('linux')) setOs('linux')
    }
  }, [])

  const trustLabels = {
    0: { label: 'COLD', color: 'text-text-dim', dot: 'bg-[var(--dot-cold)]' },
    1: { label: 'WARM', color: 'text-domain', dot: 'bg-[var(--dot-warm)]' },
    2: { label: 'TUNED', color: 'text-success', dot: 'bg-[var(--dot-tuned)]' },
  }
  const { label, color, dot } = trustLabels[trustLevel]

  // Load token list on mount
  useEffect(() => {
    loadTokens()
  }, [])

  async function loadTokens() {
    try {
      setLoadingTokens(true)
      const data = await apiMcpListTokens(authToken)
      setTokens(data.tokens)
    } catch (err) {
      logger.error('[McpTokenSection] Failed to load tokens:', { error: err })
      setError('Failed to load tokens — please refresh')
    } finally {
      setLoadingTokens(false)
    }
  }

  async function handleGenerate() {
    try {
      setError(null)
      setGenerating(true)
      const data = await apiMcpGenerateToken(authToken)
      setGeneratedToken(data.mcp_token)
      await loadTokens()
    } catch (err) {
      logger.error('[McpTokenSection] Failed to generate token:', { error: err })
      setError('Failed to generate token. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  async function handleCopy() {
    if (!generatedToken) return
    try {
      await navigator.clipboard.writeText(generatedToken)
      setCopied(true)
      setTimeout(() => {
        setCopied(false)
        setGeneratedToken(null) // Clear after copy — won't be shown again
      }, 2000)
    } catch (err) {
      logger.error('[McpTokenSection] Clipboard write failed:', { error: err })
    }
  }

  async function handleRevoke(tokenId: string) {
    if (!window.confirm('Revoke this MCP token? Any Cursor/IDE using it will lose access immediately.')) return
    try {
      setRevokingId(tokenId)
      await apiMcpRevokeToken(authToken, tokenId)
      await loadTokens()
    } catch (err) {
      logger.error('[McpTokenSection] Failed to revoke token:', { error: err })
      setError('Failed to revoke token. Please try again.')
    } finally {
      setRevokingId(null)
    }
  }

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <div className="rounded-xl border border-border-default overflow-hidden bg-[var(--surface-card)]">
      {/* Header */}
      <div className="p-4 bg-[var(--surface-hover)] border-b border-border-default flex items-center gap-3">
        <Key size={18} className="text-mcp" />
        <h3 className="font-semibold text-text-bright">MCP Integration</h3>
      </div>

      <div className="p-5 space-y-4">
        {/* Status badge */}
        <div className="p-3 rounded-lg bg-[var(--bg)] border border-border-default">
          <div className="flex items-center gap-2 mb-1">
            <div className={`w-2 h-2 rounded-full ${dot}`} />
            <span className={`font-mono text-[10px] tracking-wider uppercase ${color}`}>
              {label} ({sessionCount} sessions)
            </span>
          </div>
          <p className="text-text-dim text-sm">
            {trustLevel === 0 && "Keep using the app, I'll get sharper in MCP too."}
            {trustLevel === 1 && "You're getting close. More sessions = better MCP integration."}
            {trustLevel === 2 && "Full MCP access available. Generate your token below."}
          </p>
        </div>

        {/* Error display */}
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-intent/5 border border-intent/20 text-intent text-sm font-mono">
            <ShieldAlert size={16} />
            {error}
          </div>
        )}

        {/* Generate button */}
        {trustLevel === 2 ? (
          <button
            id="mcp-generate-token"
            name="generate-mcp-token"
            onClick={handleGenerate}
            disabled={generating || !!generatedToken}
            className="w-full py-2.5 bg-kira text-white rounded-lg font-medium hover:bg-kira/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            aria-label="Generate new MCP token for IDE integration"
          >
            {generating ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Generating...
              </>
            ) : generatedToken ? (
              'Token generated — copy below'
            ) : (
              'Generate MCP Token'
            )}
          </button>
        ) : (
          <button
            disabled
            className="w-full py-2.5 bg-[var(--surface-hover)] text-text-dim rounded-lg font-medium cursor-not-allowed"
          >
            Available at Tuned level (30+ sessions)
          </button>
        )}

        {/* Token reveal — shown once after generation */}
        {generatedToken && (
          <div className="p-3 rounded-lg bg-[var(--bg)] border border-border-focus space-y-2">
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                readOnly
                value={generatedToken}
                className="flex-1 bg-transparent font-mono text-xs text-text-default truncate outline-none min-w-0"
              />
              <button
                onClick={handleCopy}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors shrink-0 ${
                  copied
                    ? 'bg-success/10 text-success border border-success/30'
                    : 'bg-[var(--surface-hover)] text-text-default border border-border-default hover:border-border-focus'
                }`}
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <p className="text-[10px] font-mono text-intent">
              ⚠️ Copy this token now — it won't be shown again
            </p>
          </div>
        )}

        {/* Configuration Assistant Wizard — Stays visible after token generation */}
        {(generatedToken || tokens.length > 0) && (
          <div className="mt-6 p-4 rounded-xl bg-layer1 border border-border-focus animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Terminal size={16} className="text-mcp" />
                <h4 className="text-sm font-semibold text-text-bright">Configuration Assistant</h4>
              </div>
              <div className="flex bg-layer3 p-1 rounded-lg border border-border-subtle">
                <button
                  onClick={() => setActiveConfigTab('claude')}
                  className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${activeConfigTab === 'claude' ? 'bg-layer1 text-text-bright shadow-sm' : 'text-text-dim hover:text-text-muted'}`}
                >
                  CLAUDE
                </button>
                <button
                  onClick={() => setActiveConfigTab('cursor')}
                  className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${activeConfigTab === 'cursor' ? 'bg-layer1 text-text-bright shadow-sm' : 'text-text-dim hover:text-text-muted'}`}
                >
                  CURSOR
                </button>
              </div>
            </div>

            {activeConfigTab === 'claude' ? (
              <div className="space-y-3">
                <div className="p-2.5 rounded-lg bg-layer2 border border-border-subtle">
                  <p className="text-[11px] text-text-muted mb-2">
                    1. Open your <strong>claude_desktop_config.json</strong> file:
                  </p>
                  <code className="block text-[10px] font-mono bg-black/30 p-2 rounded border border-white/5 text-blue-300 break-all">
                    {os === 'win' ? '%APPDATA%\\Claude\\claude_desktop_config.json' : '~/Library/Application Support/Claude/claude_desktop_config.json'}
                  </code>
                </div>
                <div className="p-2.5 rounded-lg bg-layer2 border border-border-subtle">
                  <p className="text-[11px] text-text-muted mb-2">
                    2. Add this to your <code>mcpServers</code> block:
                  </p>
                  <pre className="text-[10px] font-mono bg-black/30 p-3 rounded border border-white/5 text-purple-300 overflow-x-auto">
{`{
  "mcpServers": {
    "promptforge": {
      "command": "npx",
      "args": ["-y", "@promptforge/mcp-server"],
      "env": {
        "PROMPTFORGE_MCP_TOKEN": "${generatedToken || 'YOUR_TOKEN_HERE'}"
      }
    }
  }
}`}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-2.5 rounded-lg bg-layer2 border border-border-subtle">
                  <p className="text-[11px] text-text-muted mb-2">
                    1. Go to <strong>Settings</strong> → <strong>Features</strong> → <strong>MCP</strong>.
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-layer2 border border-border-subtle">
                  <p className="text-[11px] text-text-muted mb-2">
                    2. Add a new <strong>Stdio</strong> server:
                  </p>
                  <div className="space-y-2">
                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] uppercase tracking-wider text-text-dim font-bold">Name</span>
                      <code className="text-[10px] bg-black/30 p-1.5 rounded border border-white/5 text-green-300">PromptForge</code>
                    </div>
                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] uppercase tracking-wider text-text-dim font-bold">Command</span>
                      <code className="text-[10px] bg-black/30 p-1.5 rounded border border-white/5 text-green-300">
                        npx -y @promptforge/mcp-server
                      </code>
                    </div>
                    <div className="p-2 rounded bg-intent/5 border border-intent/20">
                       <p className="text-[10px] text-intent italic">
                         Note: Cursor handles environment variables via the UI. Ensure you have PROMPTFORGE_MCP_TOKEN set.
                       </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="mt-4 flex items-center justify-between pt-3 border-t border-border-subtle">
              <div className="flex items-center gap-1.5 text-[10px] text-text-dim">
                <Cpu size={12} />
                <span>Verified v1.0.0</span>
              </div>
              <a 
                href="https://promptforge.ai/docs/mcp" 
                target="_blank" 
                className="flex items-center gap-1 text-[10px] text-kira hover:underline"
              >
                View full guide <ExternalLink size={10} />
              </a>
            </div>
          </div>
        )}

        {/* Active tokens list */}
        <div className="pt-4 border-t border-border-default">
          <p className="text-[10px] font-mono text-text-dim tracking-wider uppercase mb-3">
            ACTIVE TOKENS:
          </p>

          {loadingTokens ? (
            <div className="flex items-center gap-2 text-text-dim text-sm">
              <Loader2 size={14} className="animate-spin" />
              Loading tokens...
            </div>
          ) : tokens.length === 0 ? (
            <p className="text-sm text-text-dim">No active tokens</p>
          ) : (
            <div className="space-y-2">
              {tokens.map((t, i) => (
                <div
                  key={t.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-lg bg-[var(--bg)] border border-border-default"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-mono text-[10px] text-text-dim">#{i + 1}</span>
                    <span className="text-xs text-text-default">
                      Created {formatDate(t.created_at)}
                    </span>
                    <span className="text-xs text-text-dim">·</span>
                    <span className="text-xs text-text-dim">
                      Expires {formatDate(t.expires_at)}
                    </span>
                  </div>
                  <button
                    onClick={() => handleRevoke(t.id)}
                    disabled={revokingId === t.id}
                    className="flex items-center gap-1 text-xs text-intent hover:text-intent/80 transition-colors disabled:opacity-50 shrink-0"
                  >
                    {revokingId === t.id ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Trash2 size={14} />
                    )}
                    Revoke
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-[10px] font-mono text-text-dim">
          Token stored as hash only · Revocable anytime
        </p>
      </div>
    </div>
  )
}

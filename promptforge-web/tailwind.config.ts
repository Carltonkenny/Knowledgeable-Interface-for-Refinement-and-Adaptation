import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './features/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg:       'var(--bg)',
        'surface-card':  'var(--surface-card)',
        'surface-hover': 'var(--surface-hover)',
        kira:     'var(--kira)',
        intent:   'var(--intent)',
        context:  'var(--context)',
        domain:   'var(--domain)',
        engineer: 'var(--engineer)',
        profile:  'var(--profile)',
        memory:   'var(--memory)',
        mcp:      'var(--mcp)',
        teal:     'var(--teal)',
        success:  'var(--success)',
        'text-bright':  'var(--text-bright)',
        'text-default': 'var(--text-default)',
        'text-dim':     'var(--text-dim)',
        'text-muted':   'var(--text-muted)',
        'border-subtle':  'var(--border-subtle)',
        'border-default': 'var(--border-default)',
        'border-focus':   'var(--border-focus)',
      },
      fontFamily: {
        mono:    ['JetBrains Mono', 'monospace'],
        display: ['Geist', 'sans-serif'],
      },
      boxShadow: {
        'glow':       '0 0 0 1px rgba(255,255,255,0.15)',
        'card':       '0 8px 16px rgba(0,0,0,0.4), 0 2px 4px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
}

export default config

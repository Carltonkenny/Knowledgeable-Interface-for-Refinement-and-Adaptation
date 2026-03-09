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
        layer1:   'var(--layer-1)',
        layer2:   'var(--layer-2)',
        layer3:   'var(--layer-3)',
        layer4:   'var(--layer-4)',
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
        'border-strong':  'var(--border-strong)',
        'border-bright':  'var(--border-bright)',
      },
      fontFamily: {
        mono:    ['JetBrains Mono', 'monospace'],
        display: ['Satoshi', 'sans-serif'],
      },
      boxShadow: {
        'kira':       '0 0 16px rgba(99,102,241,0.25)',
        'kira-strong':'0 0 20px rgba(99,102,241,0.4), 0 2px 8px rgba(0,0,0,0.4)',
        'memory':     '0 0 12px rgba(236,72,153,0.3)',
        'tuned':      '0 0 8px rgba(34,197,94,0.6), 0 0 20px rgba(34,197,94,0.2)',
        'card':       '0 8px 32px rgba(99,102,241,0.08), 0 2px 8px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
}

export default config

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
        bg:              'var(--bg)',
        'bg-secondary':  'var(--bg-secondary)',
        'surface-card':  'var(--surface-card)',
        'surface-hover': 'var(--surface-hover)',
        'surface-glass': 'var(--surface-glass)',
        kira:            'var(--kira)',
        'kira-light':    'var(--kira-light)',
        intent:          'var(--intent)',
        context:         'var(--context)',
        domain:          'var(--domain)',
        engineer:        'var(--engineer)',
        profile:         'var(--profile)',
        memory:          'var(--memory)',
        mcp:             'var(--mcp)',
        teal:            'var(--teal)',
        success:         'var(--success)',
        'text-bright':   'var(--text-bright)',
        'text-default':  'var(--text-default)',
        'text-dim':      'var(--text-dim)',
        'text-muted':    'var(--text-muted)',
        'border-subtle':  'var(--border-subtle)',
        'border-default': 'var(--border-default)',
        'border-bright':  'var(--border-bright)',
        'border-focus':   'var(--border-focus)',
        'border-glass':   'var(--border-glass)',
      },
      fontFamily: {
        mono:    ['JetBrains Mono', 'ui-monospace', 'monospace'],
        display: ['Inter', 'Geist', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow':       '0 0 0 1px rgba(255,255,255,0.15)',
        'glow-kira':  '0 0 20px rgba(99, 102, 241, 0.15), 0 0 60px rgba(99, 102, 241, 0.05)',
        'glow-sm':    '0 0 10px rgba(99, 102, 241, 0.1)',
        'card':       '0 8px 32px rgba(0,0,0,0.4), 0 2px 4px rgba(0,0,0,0.4)',
        'card-hover': '0 16px 48px rgba(0,0,0,0.5), 0 4px 8px rgba(0,0,0,0.4)',
        'glass':      '0 8px 32px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.04)',
      },
      animation: {
        'fade-in-up': 'fade-in-up 0.6s ease-out forwards',
        'fade-in':    'fade-in 0.4s ease-out forwards',
        'scale-in':   'scale-in 0.5s ease-out forwards',
        'shimmer':    'shimmer 2s linear infinite',
        'live-pulse': 'live-pulse 2s ease-in-out infinite',
      },
      backdropBlur: {
        'glass': '20px',
        '3xl':   '64px',
      },
    },
  },
  plugins: [],
}

export default config

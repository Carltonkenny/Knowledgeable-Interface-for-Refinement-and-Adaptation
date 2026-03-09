// lib/constants.ts
// App-wide constants (routes, limits, messages)

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  ONBOARDING: '/onboarding',
  APP: '/app',
  HISTORY: '/app/history',
  PROFILE: '/app/profile',
} as const

export const API_ROUTES = {
  HEALTH:      '/health',
  CHAT:        '/chat',
  CHAT_STREAM: '/chat/stream',
  REFINE:      '/refine',
  TRANSCRIBE:  '/transcribe',
  HISTORY:     '/history',
  CONVERSATION:'/conversation',
  PROFILE_SAVE:'/user/profile',
} as const

export const LIMITS = {
  PROMPT_MIN:        5,
  PROMPT_MAX:        2000,
  FILE_MAX_BYTES:    2 * 1024 * 1024,  // 2MB
  IMAGE_MAX_BYTES:   5 * 1024 * 1024,  // 5MB
  DEMO_MAX_USES:     3,
  DEMO_STORAGE_KEY:  'pf_demo_uses',
  SESSION_STORAGE_KEY: 'pf_session_id',
} as const

export const PERSONA_DOT_THRESHOLDS = {
  COLD:  0,   // grey  — session 0-9
  WARM:  10,  // amber — session 10-29
  TUNED: 30,  // green — session 30+
} as const

export const KIRA_ERROR_MESSAGES = {
  NETWORK:     "Something broke on my end. Your prompt is safe — try again.",
  RATE_LIMIT:  "You're moving fast. Give me 30 seconds to catch up.",
  AUTH:        "Session expired. Sign back in and we'll pick up where we left off.",
  VALIDATION:  "That's too short for me to work with. Give me a bit more context.",
  SERVER:      "Backend's having a moment. Your prompt is safe — try again.",
  UNKNOWN:     "Something went wrong. Your prompt is safe — try again.",
} as const

export const ONBOARDING_QUESTIONS = [
  {
    id: 'primary_use',
    question: 'What do you mostly use AI for?',
    type: 'grid' as const,
    options: [
      { label: 'Writing',   icon: '✍️' },
      { label: 'Code',      icon: '💻' },
      { label: 'Marketing', icon: '📣' },
      { label: 'Research',  icon: '🔬' },
      { label: 'Product',   icon: '🗺️' },
      { label: 'Other',     icon: '✦' },
    ],
  },
  {
    id: 'audience',
    question: 'Who do you usually write for?',
    type: 'list' as const,
    options: [
      { label: 'Just me / internal teams' },
      { label: 'External customers or clients' },
      { label: 'Both — depends on the day' },
    ],
  },
  {
    id: 'ai_frustration',
    question: "What does AI keep getting wrong for you?",
    type: 'chips' as const,
    options: [
      { label: 'Too generic' },
      { label: 'Wrong tone' },
      { label: 'Misses context' },
      { label: 'Too long' },
      { label: 'Too formal' },
      { label: 'Off-brand' },
    ],
    hasTextFallback: true,
    textPlaceholder: "Or describe it in your own words...",
  },
] as const

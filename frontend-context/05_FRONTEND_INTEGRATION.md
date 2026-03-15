# PromptForge v2.0 — Frontend Integration Guide

**Document Purpose:** Complete guide for frontend developers to integrate with PromptForge backend.

**Tech Stack:** Next.js 16 + React 19 + TypeScript + Tailwind CSS + Supabase Auth

---

## TABLE OF CONTENTS

1. [Quick Start](#1-quick-start)
2. [Authentication Setup](#2-authentication-setup)
3. [API Client Implementation](#3-api-client-implementation)
4. [SSE Streaming Hook](#4-sse-streaming-hook)
5. [Session Management](#5-session-management)
6. [Component Examples](#6-component-examples)
7. [Error Handling](#7-error-handling)
8. [Rate Limiting](#8-rate-limiting)
9. [Multimodal Integration](#9-multimodal-integration)
10. [Best Practices](#10-best-practices)

---

## 1. QUICK START

### Prerequisites

```bash
# Node.js 18+ required
node --version

# Install dependencies
npm install @supabase/supabase-js
```

### Environment Variables

```env
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Project Structure

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   ├── app/
│   │   ├── page.tsx          # Chat page
│   │   ├── profile/
│   │   └── history/
│   └── layout.tsx
├── components/
│   ├── chat/
│   │   ├── ChatContainer.tsx
│   │   ├── MessageList.tsx
│   │   ├── InputBar.tsx
│   │   └── OutputCard.tsx
│   └── ui/
├── lib/
│   ├── api.ts                # API client
│   ├── stream.ts             # SSE parser
│   ├── auth.ts               # Auth utilities
│   └── constants.ts
├── hooks/
│   ├── useKiraStream.ts
│   ├── useSessionId.ts
│   └── useAuth.ts
└── types/
    └── api.ts
```

---

## 2. AUTHENTICATION SETUP

### Supabase Client

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### Auth Provider

```typescript
// contexts/AuthContext.tsx
'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error
  }

  const signUp = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
    })
    if (error) throw error
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
```

### Auth Hook for API Calls

```typescript
// hooks/useAuth.ts
import { useAuth } from '@/contexts/AuthContext'
import { useCallback } from 'react'

export function useApiAuth() {
  const { session } = useAuth()

  const getToken = useCallback(async () => {
    if (!session) return null
    
    // Check if token is expired
    const now = Math.floor(Date.now() / 1000)
    if (session.expires_at && session.expires_at < now) {
      // Refresh session
      const { data: { session: newSession } } = await supabase.auth.refreshSession()
      return newSession?.access_token ?? null
    }
    
    return session.access_token
  }, [session])

  return { getToken, isAuthenticated: !!session }
}
```

---

## 3. API CLIENT IMPLEMENTATION

### Types

```typescript
// types/api.ts
export interface RefineRequest {
  prompt: string
  session_id?: string
}

export interface RefineResponse {
  original_prompt: string
  improved_prompt: string
  breakdown: {
    intent: {
      primary_intent: string
      goal_clarity: string
      missing_info: string[]
    }
    context: {
      skill_level: string
      tone: string
      constraints: string[]
      implicit_preferences: string[]
    }
    domain: {
      primary_domain: string
      sub_domain: string
      relevant_patterns: string[]
      complexity: string
    }
  }
  session_id: string
}

export interface ChatRequest {
  message: string
  session_id: string
  input_modality?: 'text' | 'file' | 'image' | 'voice'
  file_base64?: string
  file_type?: string
}

export type ChatResponseType = 
  | 'conversation'
  | 'followup_refined'
  | 'prompt_improved'
  | 'clarification_requested'
  | 'clarification_resolved'

export interface ChatResponse {
  type: ChatResponseType
  reply: string
  kira_message?: string
  improved_prompt?: string
  breakdown?: {
    intent: any
    context: any
    domain: any
  }
  session_id: string
}

export interface SSEEvent {
  type: 'status' | 'kira_message' | 'result' | 'done' | 'error'
  data: {
    message?: string
    reply?: string
    improved_prompt?: string
    complete?: boolean
    [key: string]: any
  }
}

export interface HistoryItem {
  id: string
  raw_prompt: string
  improved_prompt: string
  quality_score: {
    specificity: number
    clarity: number
    actionability: number
    overall: number
  }
  created_at: string
}

export interface ConversationTurn {
  id: string
  role: 'user' | 'assistant'
  message: string
  message_type: string
  improved_prompt?: string
  created_at: string
}
```

### API Client

```typescript
// lib/api.ts
import { 
  RefineRequest, 
  RefineResponse, 
  ChatRequest, 
  ChatResponse,
  SSEEvent,
  HistoryItem,
  ConversationTurn 
} from '@/types/api'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class PromptForgeAPI {
  private getToken: () => Promise<string | null>
  
  constructor(getToken: () => Promise<string | null>) {
    this.getToken = getToken
  }
  
  private async getHeaders(): Promise<HeadersInit> {
    const token = await this.getToken()
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    }
  }
  
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...(await this.getHeaders()),
        ...options?.headers,
      },
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new ApiError(response.status, error.detail || error.message || 'Unknown error')
    }
    
    return response.json()
  }
  
  async refine(prompt: string, sessionId?: string): Promise<RefineResponse> {
    return this.request<RefineResponse>('/refine', {
      method: 'POST',
      body: JSON.stringify({ prompt, session_id: sessionId }),
    })
  }
  
  async chat(message: string, sessionId: string): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    })
  }
  
  async *chatStream(message: string, sessionId: string): AsyncGenerator<SSEEvent> {
    const response = await fetch(`${BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: await this.getHeaders(),
      body: JSON.stringify({ message, session_id: sessionId }),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Stream failed' }))
      throw new ApiError(response.status, error.detail || error.message || 'Stream failed')
    }
    
    const reader = response.body?.getReader()
    if (!reader) throw new Error('Response body is null')
    
    const decoder = new TextDecoder()
    let buffer = ''
    
    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: SSEEvent = JSON.parse(line.slice(6))
              yield event
            } catch (e) {
              console.warn('Failed to parse SSE event:', line, e)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }
  
  async getHistory(sessionId?: string, limit?: number): Promise<HistoryItem[]> {
    const params = new URLSearchParams()
    if (sessionId) params.append('session_id', sessionId)
    if (limit) params.append('limit', limit.toString())
    return this.request<HistoryItem[]>(`/history?${params}`)
  }
  
  async getConversation(sessionId: string, limit?: number): Promise<ConversationTurn[]> {
    const params = new URLSearchParams()
    params.append('session_id', sessionId)
    if (limit) params.append('limit', limit.toString())
    const result = await this.request<{ turns: ConversationTurn[] }>(`/conversation?${params}`)
    return result.turns
  }
  
  async transcribe(audioBlob: Blob): Promise<{ text: string }> {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')
    
    const token = await this.getToken()
    const response = await fetch(`${BASE_URL}/transcribe`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: formData,
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Transcription failed' }))
      throw new ApiError(response.status, error.detail || error.message || 'Transcription failed')
    }
    
    return response.json()
  }
  
  async uploadFile(file: File): Promise<{ text: string; filename: string; file_type: string }> {
    const formData = new FormData()
    formData.append('file', file)
    
    const token = await this.getToken()
    const response = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: formData,
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new ApiError(response.status, error.detail || error.message || 'Upload failed')
    }
    
    return response.json()
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
```

### Initialize API Client

```typescript
// lib/api-client.ts
import { PromptForgeAPI } from './api'
import { supabase } from './supabase'

export const api = new PromptForgeAPI(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token ?? null
})
```

---

## 4. SSE STREAMING HOOK

```typescript
// hooks/useKiraStream.ts
import { useState, useCallback, useRef } from 'react'
import { SSEEvent, ChatResponseType } from '@/types/api'
import { api } from '@/lib/api-client'

interface UseKiraStreamOptions {
  sessionId: string
  onStatus?: (message: string) => void
  onKiraMessage?: (message: string, complete: boolean) => void
  onResult?: (result: ChatResponseType, data: any) => void
  onDone?: () => void
  onError?: (error: string) => void
}

export function useKiraStream({
  sessionId,
  onStatus,
  onKiraMessage,
  onResult,
  onDone,
  onError,
}: UseKiraStreamOptions) {
  const [status, setStatus] = useState<string>('')
  const [kiraMessage, setKiraMessage] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<any | null>(null)
  
  const abortControllerRef = useRef<AbortController | null>(null)
  
  const send = useCallback(async (message: string) => {
    // Abort any ongoing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    abortControllerRef.current = new AbortController()
    setIsStreaming(true)
    setError(null)
    setStatus('Starting...')
    setKiraMessage('')
    setResult(null)
    
    try {
      for await (const event of api.chatStream(message, sessionId)) {
        switch (event.type) {
          case 'status':
            setStatus(event.data.message || '')
            onStatus?.(event.data.message || '')
            break
            
          case 'kira_message':
            if (event.data.complete) {
              setKiraMessage(prev => prev) // Signal completion
            } else {
              setKiraMessage(prev => prev + (event.data.message || ''))
            }
            onKiraMessage?.(event.data.message || '', event.data.complete ?? false)
            break
            
          case 'result':
            setResult(event.data)
            onResult?.(event.data.type, event.data)
            break
            
          case 'done':
            setIsStreaming(false)
            onDone?.()
            break
            
          case 'error':
            throw new Error(event.data.message || 'Stream error')
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return // Aborted by user
      }
      
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      setIsStreaming(false)
      onError?.(errorMessage)
    }
  }, [sessionId, onStatus, onKiraMessage, onResult, onDone, onError])
  
  const retry = useCallback(() => {
    // Implement retry logic
  }, [])
  
  const clearError = useCallback(() => {
    setError(null)
  }, [])
  
  return {
    status,
    kiraMessage,
    isStreaming,
    error,
    result,
    send,
    retry,
    clearError,
  }
}
```

---

## 5. SESSION MANAGEMENT

```typescript
// hooks/useSessionId.ts
import { useState, useEffect, useCallback } from 'react'

const SESSION_STORAGE_KEY = 'promptforge_session_id'

function generateSessionId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 15)}`
}

export function useSessionId() {
  const [sessionId, setSessionId] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    // Load from localStorage on mount
    const stored = localStorage.getItem(SESSION_STORAGE_KEY)
    if (stored) {
      setSessionId(stored)
    } else {
      const newId = generateSessionId()
      setSessionId(newId)
      localStorage.setItem(SESSION_STORAGE_KEY, newId)
    }
    setIsLoading(false)
  }, [])
  
  const createNewSession = useCallback(() => {
    const newId = generateSessionId()
    setSessionId(newId)
    localStorage.setItem(SESSION_STORAGE_KEY, newId)
    return newId
  }, [])
  
  const clearSession = useCallback(() => {
    localStorage.removeItem(SESSION_STORAGE_KEY)
    setSessionId('')
  }, [])
  
  return {
    sessionId,
    isLoading,
    createNewSession,
    clearSession,
  }
}
```

---

## 6. COMPONENT EXAMPLES

### Chat Container

```typescript
// components/chat/ChatContainer.tsx
'use client'

import { useState } from 'react'
import { useSessionId } from '@/hooks/useSessionId'
import { useKiraStream } from '@/hooks/useKiraStream'
import { useAuth } from '@/hooks/useAuth'
import { MessageList } from './MessageList'
import { InputBar } from './InputBar'
import { EmptyState } from './EmptyState'
import { OutputCard } from './OutputCard'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'output'
  improved_prompt?: string
  breakdown?: any
}

export function ChatContainer() {
  const { sessionId, createNewSession } = useSessionId()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  
  const {
    status,
    kiraMessage,
    isStreaming,
    error,
    result,
    send,
  } = useKiraStream({
    sessionId,
    onKiraMessage: (message, complete) => {
      // Update last assistant message with streaming content
      setMessages(prev => {
        const last = prev[prev.length - 1]
        if (last?.role === 'assistant') {
          return [
            ...prev.slice(0, -1),
            { ...last, content: last.content + message },
          ]
        }
        return prev
      })
    },
    onResult: (type, data) => {
      // Add output card if prompt was improved
      if (type === 'prompt_improved' || type === 'clarification_resolved') {
        setMessages(prev => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.reply,
            type: 'output',
            improved_prompt: data.improved_prompt,
            breakdown: data.breakdown,
          },
        ])
      }
    },
  })
  
  const handleSubmit = async (text: string) => {
    if (!text.trim() || isStreaming) return
    
    // Add user message
    setMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'user',
        content: text,
      },
    ])
    
    // Add placeholder assistant message for streaming
    setMessages(prev => [
      ...prev,
      {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
      },
    ])
    
    setInput('')
    await send(text)
  }
  
  const handleNewChat = () => {
    createNewSession()
    setMessages([])
  }
  
  return (
    <div className="flex flex-col h-screen">
      {messages.length === 0 ? (
        <EmptyState onNewChat={handleNewChat} />
      ) : (
        <MessageList messages={messages} />
      )}
      
      <InputBar
        value={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        isLoading={isStreaming}
        error={error}
        onRetry={() => send(messages[messages.length - 2]?.content || '')}
      />
      
      {status && (
        <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-4 py-2 rounded-lg text-sm">
          {status}
        </div>
      )}
    </div>
  )
}
```

### Input Bar

```typescript
// components/chat/InputBar.tsx
import { useState, useRef } from 'react'
import { PaperAirplaneIcon, MicrophoneIcon, PaperClipIcon } from '@heroicons/react/24/outline'

interface InputBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (text: string) => void
  isLoading: boolean
  error: string | null
  onRetry: () => void
}

export function InputBar({
  value,
  onChange,
  onSubmit,
  isLoading,
  error,
  onRetry,
}: InputBarProps) {
  const [isRecording, setIsRecording] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  const handleSubmit = () => {
    if (value.trim() && !isLoading) {
      onSubmit(value)
    }
  }
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }
  
  const handleVoiceInput = async () => {
    // Implement voice recording using MediaRecorder API
    setIsRecording(!isRecording)
  }
  
  const handleAttachment = () => {
    // Implement file attachment
  }
  
  return (
    <div className="border-t border-gray-200 p-4 bg-white">
      {error && (
        <div className="mb-2 p-2 bg-red-50 text-red-600 rounded text-sm flex justify-between">
          <span>{error}</span>
          <button onClick={onRetry} className="underline">Retry</button>
        </div>
      )}
      
      <div className="flex items-end gap-2 max-w-3xl mx-auto">
        <button
          onClick={handleAttachment}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
        >
          <PaperClipIcon className="w-5 h-5" />
        </button>
        
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe what you want to create..."
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={1}
            disabled={isLoading}
          />
          
          <button
            onClick={handleVoiceInput}
            className={`absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full ${
              isRecording ? 'text-red-500 animate-pulse' : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            <MicrophoneIcon className="w-5 h-5" />
          </button>
        </div>
        
        <button
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading}
          className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <PaperAirplaneIcon className="w-5 h-5" />
        </button>
      </div>
      
      <p className="text-xs text-gray-400 text-center mt-2">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  )
}
```

### Output Card

```typescript
// components/chat/OutputCard.tsx
import { useState } from 'react'
import { CheckIcon, ClipboardIcon } from '@heroicons/react/24/outline'

interface OutputCardProps {
  message: string
  improved_prompt: string
  breakdown?: any
}

export function OutputCard({ message, improved_prompt, breakdown }: OutputCardProps) {
  const [copied, setCopied] = useState(false)
  const [showDiff, setShowDiff] = useState(false)
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(improved_prompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 my-2">
      <p className="text-gray-800 mb-3">{message}</p>
      
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-gray-800">Improved Prompt</h3>
          <div className="flex gap-2">
            <button
              onClick={() => setShowDiff(!showDiff)}
              className="text-sm text-blue-600 hover:underline"
            >
              {showDiff ? 'Hide Diff' : 'Show Diff'}
            </button>
            <button
              onClick={handleCopy}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              {copied ? (
                <CheckIcon className="w-4 h-4 text-green-500" />
              ) : (
                <ClipboardIcon className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
        
        {showDiff ? (
          <div className="text-sm font-mono bg-gray-50 p-3 rounded">
            {/* Implement diff view */}
            <p className="text-green-600">+ Added role assignment</p>
            <p className="text-green-600">+ Specified output format</p>
            <p className="text-green-600">+ Included tone guidance</p>
          </div>
        ) : (
          <pre className="text-sm whitespace-pre-wrap text-gray-700">
            {improved_prompt}
          </pre>
        )}
        
        {breakdown && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-600 mb-2">Analysis</h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Domain:</span>
                <span className="ml-1 text-gray-800">
                  {breakdown.domain?.primary_domain}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Intent:</span>
                <span className="ml-1 text-gray-800">
                  {breakdown.intent?.primary_intent}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Quality:</span>
                <span className="ml-1 text-gray-800">
                  {breakdown.quality_score?.overall}/5
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
```

---

## 7. ERROR HANDLING

```typescript
// lib/errors.ts
import { ApiError } from './api'

export function handleApiError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 400:
        return 'Invalid input. Please check your message.'
      case 403:
        return 'Session expired. Please log in again.'
      case 429:
        return 'Rate limit exceeded. Please wait before sending more requests.'
      case 504:
        return 'Request timed out. Please try again.'
      default:
        return error.message || 'Something went wrong.'
    }
  }
  
  if (error instanceof Error) {
    return error.message
  }
  
  return 'An unexpected error occurred.'
}
```

---

## 8. RATE LIMITING

```typescript
// hooks/useRateLimit.ts
import { useState, useEffect } from 'react'

export function useRateLimit() {
  const [remaining, setRemaining] = useState<number>(100)
  const [resetTime, setResetTime] = useState<Date | null>(null)
  
  useEffect(() => {
    // Parse rate limit headers from API responses
    const updateRateLimit = (headers: Headers) => {
      const remaining = headers.get('X-RateLimit-Remaining')
      const window = headers.get('X-RateLimit-Window')
      
      if (remaining) {
        setRemaining(parseInt(remaining, 10))
      }
      
      if (window) {
        const resetTime = new Date(Date.now() + parseInt(window, 10) * 1000)
        setResetTime(resetTime)
      }
    }
    
    // Cleanup
    return () => {}
  }, [])
  
  return {
    remaining,
    resetTime,
    isLimited: remaining === 0,
  }
}
```

---

## 9. MULTIMODAL INTEGRATION

### Voice Input

```typescript
// hooks/useVoiceInput.ts
import { useState, useCallback, useRef } from 'react'
import { api } from '@/lib/api-client'

export function useVoiceInput(onTranscript: (text: string) => void) {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []
      
      mediaRecorder.ondataavailable = (e) => {
        chunksRef.current.push(e.data)
      }
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
        
        try {
          const { text } = await api.transcribe(audioBlob)
          onTranscript(text)
        } catch (err) {
          setError('Transcription failed')
        }
      }
      
      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      setError('Microphone access denied')
    }
  }, [onTranscript])
  
  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }, [])
  
  return {
    isRecording,
    error,
    startRecording,
    stopRecording,
  }
}
```

### File Attachment

```typescript
// hooks/useFileUpload.ts
import { useState, useCallback } from 'react'
import { api } from '@/lib/api-client'

export function useFileUpload(onUpload: (text: string) => void) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true)
    setError(null)
    
    try {
      const { text } = await api.uploadFile(file)
      onUpload(text)
    } catch (err) {
      setError('File upload failed')
    } finally {
      setIsUploading(false)
    }
  }, [onUpload])
  
  return {
    isUploading,
    error,
    uploadFile,
  }
}
```

---

## 10. BEST PRACTICES

### 1. Session Management

```typescript
// Always use session IDs for conversation continuity
const { sessionId } = useSessionId()
await api.chat(message, sessionId)
```

### 2. Error Recovery

```typescript
// Implement retry logic with exponential backoff
async function sendWithRetry(message: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await api.chat(message, sessionId)
    } catch (err) {
      if (i === maxRetries - 1) throw err
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)))
    }
  }
}
```

### 3. Streaming Optimization

```typescript
// Use requestAnimationFrame for smooth text rendering
function useTypingEffect(text: string, speed = 10) {
  const [displayed, setDisplayed] = useState('')
  
  useEffect(() => {
    let index = 0
    const timer = requestAnimationFrame(function animate() {
      if (index < text.length) {
        setDisplayed(prev => prev + text[index])
        index++
        requestAnimationFrame(animate)
      }
    })
    
    return () => cancelAnimationFrame(timer)
  }, [text])
  
  return displayed
}
```

### 4. Memory Management

```typescript
// Clean up old sessions periodically
function useSessionCleanup() {
  useEffect(() => {
    const cleanup = () => {
      const sessions = JSON.parse(localStorage.getItem('sessions') || '[]')
      const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000
      
      const activeSessions = sessions.filter((s: any) => s.timestamp > thirtyDaysAgo)
      localStorage.setItem('sessions', JSON.stringify(activeSessions))
    }
    
    cleanup()
    const interval = setInterval(cleanup, 24 * 60 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])
}
```

### 5. Accessibility

```typescript
// Add ARIA labels and keyboard navigation
<button
  onClick={handleSubmit}
  aria-label="Send message"
  className="..."
>
  <PaperAirplaneIcon />
</button>

<textarea
  aria-label="Message input"
  onKeyDown={handleKeyDown}
  className="..."
/>
```

---

**End of Frontend Integration Guide**

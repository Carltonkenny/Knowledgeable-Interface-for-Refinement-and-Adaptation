# PromptForge v2.0 — Complete API Reference

**Document Purpose:** Comprehensive API documentation for frontend integration.

**Base URL:** `http://localhost:8000` (development)
**Production URL:** (deployment-specific)

---

## AUTHENTICATION

All endpoints except `/health` require JWT authentication via Supabase.

### Getting a Token

```typescript
// Frontend: Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'securepassword'
})

// Frontend: Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'securepassword'
})

// Token is stored in localStorage by Supabase client
// Extract for API calls:
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token
```

### Using the Token

```typescript
// Include in every API request
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ message: '...', session_id: '...' })
})
```

---

## ENDPOINTS

### GET /health

Liveness check — no authentication required.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

---

### POST /refine

Single-shot prompt improvement. No memory, no conversation history.

**Authentication:** Required (JWT)

**Request Schema:**
```typescript
interface RefineRequest {
  prompt: string       // 5-2000 characters
  session_id?: string  // Default: "default"
}
```

**Request Example:**
```typescript
const response = await fetch('http://localhost:8000/refine', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    prompt: "write a story about a robot",
    session_id: "session-123"
  })
})
```

**Response Schema:**
```typescript
interface RefineResponse {
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
```

**Response Example:**
```json
{
  "original_prompt": "write a story about a robot",
  "improved_prompt": "You are a seasoned science-fiction author. Write a 1,200-word short story...",
  "breakdown": {
    "intent": {
      "primary_intent": "creative_writing",
      "goal_clarity": "medium",
      "missing_info": ["genre", "target_audience", "tone"]
    },
    "context": {
      "skill_level": "intermediate",
      "tone": "casual",
      "constraints": [],
      "implicit_preferences": ["prefers_examples", "likes_detailed_explanations"]
    },
    "domain": {
      "primary_domain": "creative_writing",
      "sub_domain": "science_fiction",
      "relevant_patterns": ["character_development", "world_building"],
      "complexity": "medium"
    }
  },
  "session_id": "session-123"
}
```

**Error Responses:**
```json
// 400 Bad Request
{
  "detail": "Prompt must be between 5 and 2000 characters"
}

// 403 Forbidden (Invalid JWT)
{
  "detail": "Invalid or expired token"
}

// 504 Gateway Timeout
{
  "detail": "Request timed out — please retry"
}

// 500 Internal Server Error
{
  "detail": "Error message details"
}
```

---

### POST /chat

Conversational endpoint with memory. Classifies message → routes appropriately.

**Authentication:** Required (JWT)

**Request Schema:**
```typescript
interface ChatRequest {
  message: string      // 1-2000 characters
  session_id: string   // Required
  input_modality?: 'text' | 'file' | 'image' | 'voice'
  file_base64?: string
  file_type?: string
}
```

**Request Example:**
```typescript
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    message: "write a story about a robot",
    session_id: "session-123"
  })
})
```

**Response Schema:**
```typescript
interface ChatResponse {
  type: 'conversation' | 'followup_refined' | 'prompt_improved' | 'clarification_requested' | 'clarification_resolved'
  reply: string
  kira_message?: string
  improved_prompt?: string
  breakdown?: {
    intent: {...}
    context: {...}
    domain: {...}
  }
  session_id: string
}
```

**Response Types:**

#### 1. CONVERSATION
```json
{
  "type": "conversation",
  "reply": "Hey! I'm Kira — I turn messy prompts into precise ones. What are you working on?",
  "kira_message": "Hey! I'm Kira — I turn messy prompts into precise ones. What are you working on?",
  "improved_prompt": null,
  "breakdown": null,
  "session_id": "session-123"
}
```

#### 2. FOLLOWUP_REFINED
```json
{
  "type": "followup_refined",
  "reply": "Got it — refining now.",
  "kira_message": "Got it — refining now.",
  "improved_prompt": "You are a Python expert. Write an async function with error handling...",
  "breakdown": null,
  "session_id": "session-123"
}
```

#### 3. PROMPT_IMPROVED
```json
{
  "type": "prompt_improved",
  "reply": "Here's your supercharged prompt 🚀\n\nWant me to refine it further?",
  "kira_message": null,
  "improved_prompt": "You are a seasoned science-fiction author. Write a 1,200-word short story...",
  "breakdown": {
    "intent": {...},
    "context": {...},
    "domain": {...}
  },
  "session_id": "session-123"
}
```

#### 4. CLARIFICATION_REQUESTED
```json
{
  "type": "clarification_requested",
  "reply": "I can help with that! What kind of story are you looking for? Sci-fi, children's book, or something else?",
  "improved_prompt": null,
  "breakdown": null,
  "session_id": "session-123"
}
```

#### 5. CLARIFICATION_RESOLVED
```json
{
  "type": "clarification_resolved",
  "reply": "Perfect — here's your engineered prompt.",
  "improved_prompt": "You are a seasoned science-fiction author. Write a 1,200-word short story...",
  "breakdown": null,
  "session_id": "session-123"
}
```

---

### POST /chat/stream

Streaming version of /chat using Server-Sent Events (SSE).

**Authentication:** Required (JWT)

**Request Schema:** Same as `/chat`

**Request Example:**
```typescript
const response = await fetch('http://localhost:8000/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    message: "write a story about a robot",
    session_id: "session-123"
  })
})

// Parse SSE stream
const reader = response.body?.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  
  const text = decoder.decode(value)
  const lines = text.split('\n')
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6))
      console.log('SSE Event:', event)
      // Handle based on event.type
    }
  }
}
```

**SSE Event Types:**

#### 1. status
```json
{
  "type": "status",
  "data": {
    "message": "Loading conversation history..."
  }
}
```

#### 2. kira_message
```json
{
  "type": "kira_message",
  "data": {
    "message": "H",
    "complete": false
  }
}
```

Completion signal:
```json
{
  "type": "kira_message",
  "data": {
    "message": "",
    "complete": true
  }
}
```

#### 3. result
```json
{
  "type": "result",
  "data": {
    "type": "prompt_improved",
    "reply": "Here's your supercharged prompt 🚀",
    "improved_prompt": "...",
    "memories_applied": 3,
    "latency_ms": 2500
  }
}
```

#### 4. done
```json
{
  "type": "done",
  "data": {
    "message": "Complete"
  }
}
```

#### 5. error
```json
{
  "type": "error",
  "data": {
    "message": "Error details"
  }
}
```

---

### GET /history

Retrieve past prompts from requests table.

**Authentication:** Required (JWT)

**Query Parameters:**
- `session_id` (optional): Filter by session
- `limit` (optional): Default 10, max 100

**Request Example:**
```typescript
const response = await fetch(
  'http://localhost:8000/history?session_id=session-123&limit=20',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
)
```

**Response Schema:**
```typescript
interface HistoryItem {
  id: string
  user_id: string
  raw_prompt: string
  improved_prompt: string
  session_id: string
  quality_score: {
    specificity: number
    clarity: number
    actionability: number
    overall: number
  }
  domain_analysis: {
    primary_domain: string
    sub_domain: string
    relevant_patterns: string[]
  }
  agents_used: string[]
  agents_skipped: string[]
  version_id: string
  version_number: number
  parent_version_id: string | null
  is_production: boolean
  created_at: string
}

interface HistoryResponse {
  items: HistoryItem[]
  total: number
}
```

**Response Example:**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "user_id": "user-uuid",
      "raw_prompt": "write a story about a robot",
      "improved_prompt": "You are a seasoned science-fiction author...",
      "session_id": "session-123",
      "quality_score": {
        "specificity": 4,
        "clarity": 5,
        "actionability": 5,
        "overall": 4.7
      },
      "domain_analysis": {
        "primary_domain": "creative_writing",
        "sub_domain": "science_fiction",
        "relevant_patterns": ["character_development", "world_building"]
      },
      "agents_used": ["intent", "context", "domain"],
      "agents_skipped": [],
      "version_id": "version-uuid",
      "version_number": 1,
      "parent_version_id": null,
      "is_production": true,
      "created_at": "2026-03-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### GET /conversation

Retrieve full chat history for a session.

**Authentication:** Required (JWT)

**Query Parameters:**
- `session_id` (required): Session identifier
- `limit` (optional): Default 50, max 200

**Request Example:**
```typescript
const response = await fetch(
  'http://localhost:8000/conversation?session_id=session-123&limit=50',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
)
```

**Response Schema:**
```typescript
interface ConversationTurn {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  message: string
  message_type: 'conversation' | 'new_prompt' | 'followup' | 'clarification_question' | 'clarification_answer' | 'prompt_improved'
  improved_prompt?: string
  created_at: string
}

interface ConversationResponse {
  session_id: string
  turns: ConversationTurn[]
  total: number
}
```

**Response Example:**
```json
{
  "session_id": "session-123",
  "turns": [
    {
      "id": "turn-1",
      "session_id": "session-123",
      "role": "user",
      "message": "write a story about a robot",
      "message_type": "new_prompt",
      "created_at": "2026-03-15T10:30:00Z"
    },
    {
      "id": "turn-2",
      "session_id": "session-123",
      "role": "assistant",
      "message": "I can help with that! What kind of story? Sci-fi, children's book, or something else?",
      "message_type": "clarification_question",
      "created_at": "2026-03-15T10:30:01Z"
    },
    {
      "id": "turn-3",
      "session_id": "session-123",
      "role": "user",
      "message": "Sci-fi story",
      "message_type": "clarification_answer",
      "created_at": "2026-03-15T10:30:15Z"
    },
    {
      "id": "turn-4",
      "session_id": "session-123",
      "role": "assistant",
      "message": "Here's your supercharged prompt 🚀",
      "message_type": "prompt_improved",
      "improved_prompt": "You are a seasoned science-fiction author...",
      "created_at": "2026-03-15T10:30:18Z"
    }
  ],
  "total": 4
}
```

---

### POST /transcribe

Transcribe voice audio to text using Whisper.

**Authentication:** Required (JWT)

**Request Schema:**
```typescript
// multipart/form-data
interface TranscribeRequest {
  audio: File  // Audio file (max 10MB, formats: mp3, wav, webm)
}
```

**Request Example:**
```typescript
const formData = new FormData()
formData.append('audio', audioBlob, 'recording.webm')

const response = await fetch('http://localhost:8000/transcribe', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
})
```

**Response Schema:**
```typescript
interface TranscribeResponse {
  text: string
  language?: string
  duration?: number
}
```

**Response Example:**
```json
{
  "text": "write a story about a robot",
  "language": "en",
  "duration": 2.5
}
```

---

### POST /upload

Upload file for multimodal processing (PDF, DOCX, TXT).

**Authentication:** Required (JWT)

**Request Schema:**
```typescript
// multipart/form-data
interface UploadRequest {
  file: File  // Max 10MB, formats: pdf, docx, txt
}
```

**Request Example:**
```typescript
const formData = new FormData()
formData.append('file', fileInput.files[0])

const response = await fetch('http://localhost:8000/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
})
```

**Response Schema:**
```typescript
interface UploadResponse {
  text: string
  filename: string
  file_type: string
  file_size: number
  page_count?: number
}
```

**Response Example:**
```json
{
  "text": "Extracted text content from document...",
  "filename": "document.pdf",
  "file_type": "application/pdf",
  "file_size": 102400,
  "page_count": 5
}
```

---

## ERROR HANDLING

### Standard Error Response Format

```typescript
interface ErrorResponse {
  detail: string | {
    message: string
    code: string
    field?: string
  }
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input, validation failed |
| 401 | Unauthorized | Missing authentication |
| 403 | Forbidden | Invalid/expired JWT |
| 429 | Too Many Requests | Rate limit exceeded (100 req/hour) |
| 500 | Internal Server Error | Server error |
| 504 | Gateway Timeout | LLM request timed out |

### Frontend Error Handling

```typescript
async function handleApiError(error: unknown) {
  if (error instanceof Response) {
    const status = error.status
    const body = await error.json()
    
    switch (status) {
      case 400:
        showToast('error', body.detail.message || 'Invalid input')
        break
      case 403:
        // Redirect to login
        redirectToLogin()
        break
      case 429:
        showToast('error', 'Rate limit exceeded. Please wait before sending more requests.')
        break
      case 504:
        showToast('error', 'Request timed out. Please try again.')
        break
      default:
        showToast('error', 'Something went wrong. Please try again.')
    }
  }
}
```

---

## RATE LIMITING

All endpoints are rate-limited to **100 requests per hour per user**.

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Window: 3600
```

### 429 Response

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "limit": "100 requests per hour",
  "remaining": 0
}
```

---

## CORS CONFIGURATION

Allowed origins (configured via `FRONTEND_URLS` env var):
- `http://localhost:3000`
- `http://localhost:9000`
- (Production URLs as configured)

### CORS Headers

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## EXAMPLE FRONTEND INTEGRATION

```typescript
// lib/api.ts
const BASE_URL = 'http://localhost:8000'

export class PromptForgeAPI {
  private token: string
  
  constructor(token: string) {
    this.token = token
  }
  
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
        ...options?.headers,
      },
    })
    
    if (!response.ok) {
      throw response
    }
    
    return response.json()
  }
  
  async refine(prompt: string, sessionId?: string) {
    return this.request<RefineResponse>('/refine', {
      method: 'POST',
      body: JSON.stringify({ prompt, session_id: sessionId }),
    })
  }
  
  async chat(message: string, sessionId: string) {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    })
  }
  
  async *chatStream(message: string, sessionId: string) {
    const response = await fetch(`${BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    })
    
    if (!response.ok) {
      throw response
    }
    
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader!.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const event = JSON.parse(line.slice(6))
          yield event
        }
      }
    }
  }
  
  async getHistory(sessionId?: string, limit?: number) {
    const params = new URLSearchParams()
    if (sessionId) params.append('session_id', sessionId)
    if (limit) params.append('limit', limit.toString())
    return this.request<HistoryResponse>(`/history?${params}`)
  }
  
  async getConversation(sessionId: string, limit?: number) {
    const params = new URLSearchParams()
    params.append('session_id', sessionId)
    if (limit) params.append('limit', limit.toString())
    return this.request<ConversationResponse>(`/conversation?${params}`)
  }
}
```

---

**End of API Reference**

# PromptForge — API Reference

**FastAPI backend endpoints**

Base URL: `http://localhost:8000` (local) or `https://your-backend.railway.app` (production)

---

## 🔐 Authentication

All endpoints (except `/health`) require JWT authentication.

**Header:**
```
Authorization: Bearer <your_jwt_token>
```

---

## 📡 Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{"status": "ok", "version": "2.0.0"}
```

---

### Chat (SSE Stream)

```http
POST /chat/stream
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "write a story about a robot"
}
```

**Response:** Server-Sent Events stream

---

### Refine Prompt

```http
POST /refine
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "write a story"
}
```

**Response:**
```json
{
  "improved_prompt": "You are a seasoned author...",
  "quality_score": {
    "specificity": 4,
    "clarity": 5,
    "actionability": 5
  }
}
```

---

### Get History

```http
GET /history
Authorization: Bearer <token>
```

**Response:**
```json
{
  "count": 10,
  "history": [
    {
      "id": "uuid",
      "raw_prompt": "...",
      "improved_prompt": "...",
      "created_at": "2026-03-24T..."
    }
  ]
}
```

---

### Get Analytics

```http
GET /history/analytics?days=30
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_prompts": 50,
  "avg_quality": 4.2,
  "unique_domains": 5,
  "hours_saved": 12.5,
  "quality_trend": [...],
  "domain_distribution": {...}
}
```

---

### User Profile

```http
GET /user/profile
Authorization: Bearer <token>
```

**Response:**
```json
{
  "primary_use": "software development",
  "audience": "technical",
  "preferred_tone": "direct"
}
```

---

### Update Profile

```http
POST /user/profile
Content-Type: application/json
Authorization: Bearer <token>

{
  "primary_use": "content creation",
  "preferred_tone": "casual"
}
```

---

## 📊 Rate Limits

- **100 requests/hour** per user
- **1000 requests/day** per user

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1616678400
```

---

## 🚨 Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request (invalid JSON) |
| 401 | Missing/invalid auth token |
| 403 | Token expired |
| 429 | Rate limit exceeded |
| 500 | Server error |

---

**For issues, open a GitHub issue.**

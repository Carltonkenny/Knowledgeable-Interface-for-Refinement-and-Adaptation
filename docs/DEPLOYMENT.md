# PromptForge — Deployment Guide

**Production-ready deployment instructions for Railway + Vercel**

---

## 🚀 Quick Deploy

### Backend (Railway)

```bash
# 1. Deploy from GitHub
Railway Dashboard → New Project → Deploy from GitHub

# 2. Set Environment Variables
SENTRY_DSN=your_sentry_dsn
POLLINATIONS_API_KEY=your_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
REDIS_URL=your_redis_url

# 3. Deploy
# Railway auto-detects Dockerfile and builds
```

### Frontend (Vercel)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
cd promptforge-web
vercel --prod

# 3. Set Environment Variables
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## 📋 Environment Variables

### Required (Backend)

```env
# Error Tracking
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
ENVIRONMENT=production

# LLM Provider
POLLINATIONS_API_KEY=sk_xxx
POLLINATIONS_BASE_URL=https://gen.pollinations.ai/v1
POLLINATIONS_MODEL_FULL=qwen-coder
POLLINATIONS_MODEL_FAST=gemini-fast

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx
SUPABASE_JWT_SECRET=xxx

# Redis
REDIS_URL=rediss://xxx:xxx@xxx.upstash.io:6379

# Embeddings
GEMINI_API_KEY=AIzaxxx

# CORS
FRONTEND_URLS=https://your-app.vercel.app
```

### Required (Frontend)

```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

---

## 🐳 Docker Deployment

### Local Testing

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f api

# Test
curl http://localhost:8000/health
```

### Production (Railway)

Railway auto-builds from `Dockerfile` in repo root.

---

## 📊 Monitoring

### Sentry (Errors)

- Dashboard: https://sentry.io
- Test: `curl https://your-url.railway.app/test-error`

### Better Stack (Uptime)

- Dashboard: https://betterstack.com/uptime
- Monitor: `https://your-url.railway.app/health`
- Interval: 3 minutes

### Railway Logs

- Dashboard → Project → Deployments → Logs
- Real-time streaming

---

## 🗄️ Database Schema

See: [`SUPABASE_SCHEMA.md`](./SUPABASE_SCHEMA.md)

---

## 🔧 Troubleshooting

### Backend won't start

1. Check Railway logs
2. Verify all env vars are set
3. Test health endpoint: `/health`

### Sentry not receiving errors

1. Check DSN is correct
2. Verify `sentry_sdk.init()` is called
3. Check firewall/proxy settings

### Frontend can't connect

1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check CORS settings in backend
3. Ensure backend is running

---

**For technical questions, open an issue on GitHub.**

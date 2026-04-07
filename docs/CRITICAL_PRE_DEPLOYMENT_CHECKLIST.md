# ⚠️ CRITICAL: Pre-Deployment Checklist

**DO THESE BEFORE DEPLOYING TO PRODUCTION**

---

## 🔴 CRITICAL SECURITY (Do Immediately)

### 1. Rotate ALL API Keys

Your `.env` file contains **real API keys** that are committed to git history. **Rotate these immediately:**

```bash
# 1. Supabase
- Go to: https://cckznjkzsfypssgecyya.supabase.co/project/settings/api
- Reset JWT Secret
- Reset Service Role Key
- Update `.env` with new values

# 2. Pollinations API
- Go to: https://gen.pollinations.ai
- Generate new API key
- Update `.env`

# 3. Google Gemini
- Go to: https://aistudio.google.com/app/apikey
- Delete old key, generate new one
- Update `.env`

# 4. Redis (Upstash)
- Go to: https://console.upstash.io
- Reset database password
- Update `.env` with new REDIS_URL
```

### 2. Add `.env` to `.gitignore` Immediately

```bash
# Verify .env is ignored
git check-ignore .env
# If no output, add to .gitignore:
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Ensure .env is never committed"
```

### 3. Run SQL Migrations

Go to Supabase SQL Editor and run:

```sql
-- Migration 025: Add user_timezone
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS user_timezone TEXT DEFAULT 'UTC';

-- Migration 026: Add last_profile_sync
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS last_profile_sync TIMESTAMPTZ;

-- Verify columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'user_profiles'
  AND column_name IN ('user_timezone', 'last_profile_sync');
```

---

## 🟡 HIGH PRIORITY (Before First User)

### 4. Update Environment Variables for Production

Edit `.env`:

```env
# Change from localhost to production domain
FRONTEND_URLS=https://your-domain.com,https://www.your-domain.com

# Ensure production environment
ENVIRONMENT=production

# Verify rate limiting is enabled
RATE_LIMIT_ENABLED=true
```

Edit `promptforge-web/.env.local`:

```env
# Update to production API URL when deployed
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

### 5. Enable Supabase Row-Level Security (RLS)

Run in Supabase SQL Editor:

```sql
-- Enable RLS on all tables
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE langmem_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;

-- Create policies (example for requests table)
CREATE POLICY "Users can only see their own requests"
ON requests
FOR ALL
USING (user_id = auth.uid());

-- Repeat for other tables...
```

### 6. Set Up Database Backups

1. Go to Supabase Dashboard → Settings → Database
2. Enable daily backups
3. Set retention period (recommend 30 days)
4. Test restore procedure

---

## 🟢 MEDIUM PRIORITY (First Week)

### 7. Deploy Backend

**Option A: Railway**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

**Option B: Render**
```bash
# Connect GitHub repo in Render dashboard
# Set environment variables
# Deploy
```

**Option C: Docker**
```bash
docker-compose up -d
# Verify health
curl http://localhost:8000/health
```

### 8. Deploy Frontend

**Vercel (Recommended)**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd promptforge-web
vercel
# Follow prompts, set environment variables
```

### 9. Configure Custom Domain (Optional)

1. Buy domain (Namecheap, GoDaddy, etc.)
2. Point DNS to Vercel/Railway
3. Add domain in Vercel/Railway dashboard
4. Enable HTTPS (automatic with Vercel/Railway)

### 10. Set Up Monitoring

1. **Sentry** — Already configured, verify DSN works
2. **Better Stack** — Set up uptime monitoring
3. **Supabase Logs** — Enable query logging
4. **Vercel Analytics** — Enable in dashboard

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify:

- [ ] Health check returns 200: `curl https://api.your-domain.com/health`
- [ ] Sign-up works end-to-end
- [ ] Login works end-to-end
- [ ] Chat endpoint responds (`/chat`)
- [ ] Streaming works (`/chat/stream`)
- [ ] History loads correctly
- [ ] Profile updates save
- [ ] Rate limiting works (spam 50+ requests)
- [ ] No errors in Sentry dashboard
- [ ] Database queries <200ms
- [ ] Mobile responsive (test on phone)
- [ ] Lighthouse score >90

---

## 🆘 EMERGENCY CONTACTS

If something breaks:

1. **Check Sentry** — https://sentry.io
2. **Check Supabase Logs** — https://supabase.com/dashboard/project/_/logs
3. **Check Vercel Logs** — https://vercel.com/dashboard
4. **Rollback** — Revert to previous deployment

---

## 📞 POST-DEPLOYMENT MONITORING

**First 24 Hours:**
- Check Sentry every 4 hours
- Monitor database query performance
- Watch for rate limit violations
- Check user sign-up flow

**First Week:**
- Daily error rate review
- User feedback collection
- Performance optimization
- Bug fixes

**First Month:**
- Weekly analytics review
- Feature usage analysis
- User retention metrics
- Plan next sprint

---

**Last Updated:** April 1, 2026  
**Next Review:** After first production deployment

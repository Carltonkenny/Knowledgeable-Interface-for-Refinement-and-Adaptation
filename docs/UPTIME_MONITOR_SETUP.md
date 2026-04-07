# Uptime Monitor Setup

## Quick Setup (UptimeRobot — Free)

1. Go to https://uptimerobot.com and sign up (free, 50 monitors, 5-min interval)

2. Add Monitor for API:
   - Monitor Type: HTTP(S)
   - Friendly Name: PromptForge API
   - URL: http://YOUR_SERVER_IP:8000/health
   - Monitoring Interval: 5 minutes
   - Alert Contacts: your email

3. Add Monitor for LangFuse:
   - Monitor Type: HTTP(S)
   - Friendly Name: LangFuse Dashboard
   - URL: http://YOUR_SERVER_IP:3001/api/public/health
   - Monitoring Interval: 5 minutes

4. Add Monitor for Frontend (if deployed):
   - Monitor Type: HTTP(S)
   - Friendly Name: PromptForge Frontend
   - URL: http://YOUR_SERVER_IP:3000
   - Monitoring Interval: 5 minutes

## What Happens
- Every 5 minutes, UptimeRobot pings your endpoints
- If any endpoint returns non-200 or times out, you get an email alert
- Dashboard shows uptime history (99.9%, downtime events, etc.)

## Alternative: Better Stack (Free, 10 monitors, 3-min interval)
- Go to https://betterstack.com
- Sign up free
- Add monitors same as above
- Gets alerts in 3 minutes instead of 5

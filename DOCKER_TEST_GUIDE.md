# ═══════════════════════════════════════════════════════════════
# PromptForge v2.0 - Docker Testing Guide
# ═══════════════════════════════════════════════════════════════

## ✅ DOCKER STATUS

Containers running:
- promptforge-api   → http://localhost:8000
- promptforge-redis → localhost:6379

Health check: http://localhost:8000/health


## ═══════════════════════════════════════════════════════════════
## QUICK TESTS (Copy-Paste to Terminal)
## ═══════════════════════════════════════════════════════════════

### 1. Health Check (No Auth Required)
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok","version":"2.0.0"}`


### 2. Test /refine Endpoint (Requires JWT)

First, generate a test JWT token:

```bash
# Create test token (run in Python)
python -c "
import jwt
import datetime
payload = {
    'user_id': '00000000-0000-0000-0000-000000000001',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}
token = jwt.encode(payload, '0144dddf-219e-4c2d-b8de-eb2aed6f597d', algorithm='HS256')
print(token)
"
```

Then use the token:

```bash
# Replace YOUR_TOKEN_HERE with the generated token
curl -X POST http://localhost:8000/refine ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  -d "{\"prompt\": \"write a story about a robot\", \"session_id\": \"test123\"}"
```


### 3. View Docker Logs
```bash
# See live logs from both containers
docker-compose logs -f

# See only API logs
docker-compose logs -f api

# See only Redis logs
docker-compose logs -f redis
```


### 4. Test Redis Connection
```bash
# Connect to Redis inside container
docker exec -it promptforge-redis redis-cli ping
```
Expected: `PONG`


### 5. Stop/Start Containers
```bash
# Stop all
docker-compose down

# Start all
docker-compose up -d

# Rebuild after code changes
docker-compose up -d --build
```


## ═══════════════════════════════════════════════════════════════
## INTERACTIVE TESTING (Swagger UI)
## ═══════════════════════════════════════════════════════════════

1. Open browser: http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"
6. See the response and curl command


## ═══════════════════════════════════════════════════════════════
## ENDPOINT TESTING EXAMPLES
## ═══════════════════════════════════════════════════════════════

### POST /refine - Single-shot prompt improvement

Request:
```json
{
  "prompt": "write a python function to sort a list",
  "session_id": "session-001"
}
```

Response includes:
- original_prompt: Your input
- improved_prompt: Engineered version with role, context, constraints
- breakdown: Analysis from intent, context, domain agents


### POST /chat - Conversational with memory

Request:
```json
{
  "message": "make it longer",
  "session_id": "session-001"
}
```

Response types:
- `conversation`: Casual chat reply
- `followup_refined`: Modified previous prompt
- `prompt_improved`: New engineered prompt


### GET /history - View prompt history

```bash
curl "http://localhost:8000/history?limit=10" ^
  -H "Authorization: Bearer YOUR_TOKEN"
```


### GET /conversation - View chat history for session

```bash
curl "http://localhost:8000/conversation?session_id=session-001&limit=20" ^
  -H "Authorization: Bearer YOUR_TOKEN"
```


## ═══════════════════════════════════════════════════════════════
## TROUBLESHOOTING
## ═══════════════════════════════════════════════════════════════

### Container won't start
```bash
# Check what's running
docker ps -a

# Remove old containers
docker rm -f promptforge-api promptforge-redis

# Start fresh
docker-compose up -d
```

### API returns 500 error
```bash
# Check logs for error details
docker-compose logs api | tail -50

# Verify .env file exists and has correct values
cat .env
```

### Redis connection fails
```bash
# Test Redis is responding
docker exec promptforge-redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### Port 8000 already in use
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
```


## ═══════════════════════════════════════════════════════════════
## NEXT STEPS
## ═══════════════════════════════════════════════════════════════

1. Test /refine with a vague prompt → see the 4-agent swarm in action
2. Test /chat with conversation → see classification routing
3. Check Swagger UI for interactive testing
4. View logs while testing → watch the agents work
5. Test edge cases → short messages, ambiguous requests, followups


## ═══════════════════════════════════════════════════════════════
## ARCHITECTURE REMINDER
## ═══════════════════════════════════════════════════════════════

When you call /refine or /chat with NEW_PROMPT:

1. Cache check → Instant if same prompt was run before
2. Intent agent → Analyzes WHAT user wants
3. Context agent → Analyzes WHO is asking  
4. Domain agent → Identifies domain/patterns
5. Prompt engineer → Rewrites using all analysis
6. Response → Returns improved prompt + breakdown

Total: 4 LLM calls, ~5-15 seconds


## ═══════════════════════════════════════════════════════════════
## TESTING COMPLETE CHECKLIST
## ═══════════════════════════════════════════════════════════════

[ ] Health endpoint returns OK
[ ] Redis responds to PING
[ ] /refine returns improved prompt
[ ] /chat classifies message correctly
[ ] Logs show agent processing
[ ] Swagger UI loads
[ ] History endpoint works
[ ] Conversation endpoint works

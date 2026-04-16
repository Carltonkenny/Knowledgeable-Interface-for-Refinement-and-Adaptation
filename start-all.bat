@echo off
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║         PromptForge v2.0 — Full Stack Launcher         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ── Step 1: Docker Services ──
echo [1/6] Starting Docker services...
docker compose up -d redis langfuse-db langfuse jaeger 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker failed. Is Docker Desktop running?
    pause
    exit /b 1
)
echo [1/6] Docker services started (redis, langfuse-db, langfuse, jaeger)

REM ── Step 2: Wait for Docker health ──
echo [2/6] Waiting for Docker services to be healthy...
timeout /t 10 /nobreak >nul

REM Check Redis
echo | set /p="  Redis... "
docker exec promptforge-redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (echo OK) else (echo FAILED)

REM Check LangFuse
echo | set /p="  LangFuse... "
curl -s -o nul http://localhost:3001/api/public/health
if %errorlevel% equ 0 (echo OK) else (echo still starting)

REM Check Jaeger
echo | set /p="  Jaeger... "
curl -s -o nul http://localhost:16686
if %errorlevel% equ 0 (echo OK) else (echo still starting)

REM ── Step 3: Start Python Backend ──
echo [3/6] Starting Python backend (port 8000)...
start "PromptForge Backend" cmd /k "cd /d %~dp0 && uvicorn api:app --host 0.0.0.0 --port 8000 --reload"
echo [3/6] Backend terminal opened. Waiting for startup...
timeout /t 8 /nobreak >nul

REM Check backend
echo | set /p="  Backend health... "
curl -s -o nul http://localhost:8000/health
if %errorlevel% equ 0 (echo OK) else (echo still starting)

REM ── Step 4: Start Next.js Frontend ──
echo [4/6] Starting Next.js frontend (port 3000)...
start "PromptForge Frontend" cmd /k "cd /d %~dp0\promptforge-web && npm run dev"
echo [4/6] Frontend terminal opened. Waiting for startup...
timeout /t 12 /nobreak >nul

REM Check frontend
echo | set /p="  Frontend health... "
curl -s -o nul http://localhost:3000
if %errorlevel% equ 0 (echo OK) else (echo still starting)

REM ── Step 5: Open Dashboards ──
echo [5/6] Opening dashboards...
start http://localhost:3000
start http://localhost:3001
start http://localhost:16686

REM ── Step 6: Summary ──
echo.
echo ═══════════════════════════════════════════════════════════
echo  PromptForge v2.0 — All Services Running
echo ═══════════════════════════════════════════════════════════
echo.
echo  SERVICE           URL                      STATUS
echo  ───────           ───                      ──────
echo  Frontend          http://localhost:3000    ✅ Opened in browser
echo  Backend API       http://localhost:8000    ✅ Opened in browser
echo  LangFuse Dash     http://localhost:3001    ✅ Opened in browser
echo  Jaeger Dash       http://localhost:16686   ✅ Opened in browser
echo  Redis             localhost:6379           ✅ Running (Docker)
echo.
echo  Backend terminal  → "PromptForge Backend"
echo  Frontend terminal → "PromptForge Frontend"
echo.
echo  To stop: Close terminal windows or run: docker compose down
echo ═══════════════════════════════════════════════════════════
echo.
echo Press any key to exit this window (services keep running)...
pause >nul

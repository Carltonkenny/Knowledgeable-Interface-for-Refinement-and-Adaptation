@echo off
echo ============================================================
echo PromptForge v2.0 - Docker Startup
echo ============================================================
echo.
echo Starting containers...
echo   - API:  http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo   - Redis: localhost:6379
echo.
docker-compose up --build
pause

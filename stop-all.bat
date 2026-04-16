@echo off
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║         PromptForge v2.0 — Stop All Services           ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo Stopping Docker services...
docker compose down

echo.
echo Killing remaining Node/Python processes...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul

echo.
echo All services stopped.
echo.
pause

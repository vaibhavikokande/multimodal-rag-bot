@echo off
echo ============================================
echo   Multimodal Enterprise RAG Bot - Starting
echo ============================================
echo.

echo Freeing ports 8000 and 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
timeout /t 2 /nobreak >nul

echo [1/2] Starting Backend on http://localhost:8000 ...
start "RAG Backend" cmd /k "cd /d C:\Users\Vaibhavi.Kokande\Downloads\multimodal-rag-bot\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 6 /nobreak >nul

echo [2/2] Starting Frontend on http://localhost:3000 ...
start "RAG Frontend" cmd /k "cd /d C:\Users\Vaibhavi.Kokande\Downloads\multimodal-rag-bot\frontend && npm run dev"

echo.
echo ============================================
echo   RAG Bot is starting up!
echo ============================================
echo   Frontend : http://localhost:3000
echo   Backend  : http://localhost:8000
echo   API Docs : http://localhost:8000/api/v1/docs
echo.
echo   Login: admin@company.com / Admin@123456
echo   Opening browser in 18 seconds...
echo ============================================
timeout /t 18 /nobreak >nul

start http://localhost:3000
pause

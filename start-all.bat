@echo off
echo ============================================
echo   Starting Tea services...
echo ============================================
echo.
echo [0/2] Checking and clearing old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do taskkill /f /pid %%a 2>nul
timeout /t 2 /nobreak >nul
echo.
echo [1/2] Python RAG service (port 8000)
start "Tea-RAG-8000" cmd /k D:\BMCY\start-rag.bat
echo [2/2] SpringBoot backend (port 8080)
start "Tea-Backend-8080" cmd /k D:\BMCY\start-backend.bat
echo.
echo Done. Two service windows opened:
echo   - RAG AI    http://127.0.0.1:8000
echo   - Backend   http://127.0.0.1:8080
echo.
echo Wait 30-50 seconds for SpringBoot to finish starting.
echo Run stop-all.bat to stop all services.
echo.
pause

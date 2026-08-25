@echo off
echo Stopping Tea services...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do taskkill /f /pid %%a 2>nul
echo.
echo Done. All services stopped.
echo.
pause

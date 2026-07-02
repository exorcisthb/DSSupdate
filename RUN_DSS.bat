@echo off
echo ========================================
echo   DSS VISUAL - FULL STACK LAUNCHER
echo ========================================
echo.

echo [1/3] Starting Backend API Server...
start "DSS API Server" cmd /k "python api\app.py"
timeout /t 3 /nobreak > nul

echo [2/3] Waiting for API to be ready...
timeout /t 2 /nobreak > nul

echo [3/3] Starting Frontend Dashboard...
start "DSS Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   DSS System Started!
echo ========================================
echo.
echo Backend API:  http://127.0.0.1:5000
echo Frontend:     http://localhost:5173
echo.
echo Press any key to stop all servers...
pause > nul

echo.
echo Stopping servers...
taskkill /FI "WINDOWTITLE eq DSS*" /T /F > nul 2>&1

echo Done!

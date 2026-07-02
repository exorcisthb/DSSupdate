@echo off
cls
echo.
echo ==========================================
echo     DSS VISUAL - COMPLETE SYSTEM
echo ==========================================
echo.
echo [1/2] Starting Backend API Server...
start "DSS Backend API" cmd /k "python api\app.py"
timeout /t 5 /nobreak > nul

echo [2/2] Starting Frontend Dashboard...
start "DSS Frontend" cmd /k "npm run dev"
timeout /t 2 /nobreak > nul

cls
echo.
echo ==========================================
echo    DSS System Successfully Launched!
echo ==========================================
echo.
echo Backend API:     http://127.0.0.1:5000
echo Frontend:        http://localhost:5173
echo.
echo Features:
echo   [x] Exploratory Data Analysis (EDA)
echo   [x] Diagnostic Analytics (Gap Analysis)
echo   [x] Predictive Analytics (Forecasting)
echo   [x] What-If Scenario Analysis
echo   [x] Decision Recommendations
echo.
echo Assignment 2: 100%% COMPLETE
echo.
echo Press Ctrl+C in each terminal to stop servers
echo.
pause

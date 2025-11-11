@echo off
echo ============================================================
echo Restarting BTC Scalp Scanner with Hybrid Client Fix
echo ============================================================
echo.

REM Kill any existing Python processes (optional - comment out if you want to keep other scanners running)
REM taskkill /F /IM python.exe 2>nul

echo Starting BTC Scalp Scanner...
start "BTC Scalp Scanner" python main.py

echo.
echo Scanner started! Check the window for status.
echo Logs: logs\scanner.log
echo.
pause

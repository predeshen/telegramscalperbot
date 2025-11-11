@echo off
title Quick Fix and Start - BTC Scanner
color 0A
echo.
echo ============================================================
echo   BTC Scanner - Quick Fix and Start
echo ============================================================
echo.

echo [1/3] Testing the fix...
python test_hybrid_fix.py
if errorlevel 1 (
    echo.
    echo ERROR: Fix test failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [2/3] Checking scanner status...
echo ============================================================
python check_scanner_status.py

echo.
echo ============================================================
echo [3/3] Starting BTC Scalp Scanner...
echo ============================================================
echo.
echo The scanner will start in a new window.
echo You should receive a Telegram notification when it's ready.
echo.
timeout /t 3 /nobreak >nul

start "BTC Scalp Scanner" python main.py

echo.
echo ============================================================
echo   Scanner Started!
echo ============================================================
echo.
echo Check:
echo   - New window titled "BTC Scalp Scanner"
echo   - Telegram for startup notification
echo   - logs\scanner.log for detailed logs
echo.
echo To stop: Close the scanner window or press Ctrl+C in it
echo.
pause

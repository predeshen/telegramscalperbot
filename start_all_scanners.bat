@echo off
REM Start All Trading Scanners
title Trading Scanners - Master Control
echo ========================================
echo Starting All Trading Scanners
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check for .env file
if not exist ".env" (
    echo WARNING: .env file not found
    echo Please create .env file with:
    echo   TELEGRAM_BOT_TOKEN=your_token
    echo   TELEGRAM_CHAT_ID=your_chat_id
    echo.
    pause
)

echo Starting scanners in separate windows...
echo.

REM Start each scanner in a new window
start "BTC Scalping Scanner" cmd /k "start_btc_scalp.bat"
timeout /t 2 /nobreak >nul

start "BTC Swing Scanner" cmd /k "start_btc_swing.bat"
timeout /t 2 /nobreak >nul

start "Gold Scalping Scanner" cmd /k "start_gold_scalp.bat"
timeout /t 2 /nobreak >nul

start "Gold Swing Scanner" cmd /k "start_gold_swing.bat"
timeout /t 2 /nobreak >nul

start "US30 Scalping Scanner" cmd /k "start_us30_scalp.bat"
timeout /t 2 /nobreak >nul

start "US30 Swing Scanner" cmd /k "start_us30_swing.bat"

echo.
echo ========================================
echo All Scanners Started!
echo ========================================
echo.
echo 6 scanner windows have been opened:
echo   - BTC Scalping Scanner (1m/5m)
echo   - BTC Swing Scanner (15m/1h/4h/1d)
echo   - Gold Scalping Scanner (1m/5m)
echo   - Gold Swing Scanner (1h/4h/1d)
echo   - US30 Scalping Scanner (5m/15m)
echo   - US30 Swing Scanner (4h/1d)
echo.
echo To stop all scanners, run: stop_all_scanners.bat
echo Or close each window individually with Ctrl+C
echo.
pause

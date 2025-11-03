@echo off
REM Gold (XAU/USD) Scalping Scanner (1m/5m timeframes)
title Gold Scalping Scanner
echo ========================================
echo Gold (XAU/USD) Scalping Scanner Starting...
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

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Checking dependencies...
pip install -r requirements.txt --quiet

REM Check for .env file
if not exist ".env" (
    echo WARNING: .env file not found
    echo Please create .env file with:
    echo   TELEGRAM_BOT_TOKEN=your_token
    echo   TELEGRAM_CHAT_ID=your_chat_id
    echo.
)

REM Start scanner
echo.
echo Starting Gold Scalping Scanner...
echo Press Ctrl+C to stop
echo.
python xauusd_scanner\main_gold.py

REM Deactivate virtual environment on exit
deactivate

pause

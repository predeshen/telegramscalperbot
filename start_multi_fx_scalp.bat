@echo off
REM Multi-FX Scalping Scanner (EUR/USD, GBP/USD - 5m/15m/1h)
title Multi-FX Scalping Scanner
echo ========================================
echo Multi-FX Scalping Scanner Starting...
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

REM Create logs directory if it doesn't exist
if not exist "logs\" mkdir logs

REM Start scanner
echo.
echo Starting Multi-FX Scalping Scanner...
echo Symbols: EUR/USD, GBP/USD
echo Timeframes: 5m, 15m, 1h
echo Press Ctrl+C to stop
echo.
python main_multi_symbol.py --config config/multi_fx_scalp.json

REM Deactivate virtual environment on exit
deactivate

pause

@echo off
title Scanner Logs - Live View
color 0B
echo.
echo ============================================================
echo   Scanner Logs - Live View
echo ============================================================
echo.
echo Select which scanner to watch:
echo.
echo   1. BTC Scalp Scanner
echo   2. BTC Swing Scanner
echo   3. US30 Scalp Scanner
echo   4. US30 Swing Scanner
echo   5. All Scanners (combined)
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    set logfile=logs\scanner.log
    set scanner=BTC Scalp Scanner
)
if "%choice%"=="2" (
    set logfile=logs\scanner_swing.log
    set scanner=BTC Swing Scanner
)
if "%choice%"=="3" (
    set logfile=logs\us30_scalp_scanner.log
    set scanner=US30 Scalp Scanner
)
if "%choice%"=="4" (
    set logfile=logs\us30_swing_scanner.log
    set scanner=US30 Swing Scanner
)
if "%choice%"=="5" (
    echo.
    echo Showing all scanner logs...
    echo Press Ctrl+C to stop
    echo.
    timeout /t 2 /nobreak >nul
    powershell -Command "Get-Content logs\*.log -Wait -Tail 20"
    exit /b 0
)

if not defined logfile (
    echo Invalid choice!
    pause
    exit /b 1
)

if not exist "%logfile%" (
    echo.
    echo ERROR: Log file not found: %logfile%
    echo The scanner may not have been started yet.
    echo.
    pause
    exit /b 1
)

echo.
echo Watching: %scanner%
echo Log file: %logfile%
echo.
echo Press Ctrl+C to stop
echo.
timeout /t 2 /nobreak >nul

REM Use PowerShell to tail the log file (like 'tail -f' on Linux)
powershell -Command "Get-Content '%logfile%' -Wait -Tail 20"

@echo off
REM Stop All Trading Scanners
title Stop All Scanners
echo ========================================
echo Stopping All Trading Scanners
echo ========================================
echo.

echo Searching for running Python scanner processes...
echo.

REM Kill all Python processes running scanner scripts
taskkill /FI "WINDOWTITLE eq BTC Scalping Scanner*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BTC Swing Scanner*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Gold Scalping Scanner*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Gold Swing Scanner*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq US30 Scalping Scanner*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq US30 Swing Scanner*" /F >nul 2>&1

REM Alternative: Kill Python processes running scanner files
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | find "main" >nul
    if not errorlevel 1 (
        echo Stopping scanner process %%a...
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo.
echo ========================================
echo All Scanners Stopped
echo ========================================
echo.
echo All scanner processes have been terminated.
echo You can now restart them with start_all_scanners.bat
echo.
pause

@echo off
REM ============================================================
REM  Client Finder — Auto Runner
REM  Place this in Windows Startup folder or use Task Scheduler.
REM  It checks if 12 hours passed, then runs the full pipeline.
REM ============================================================

cd /d "%~dp0"

echo ============================================================
echo  Client Finder — Checking if it's time to run...
echo ============================================================

c:\python314\python.exe automatic_main.py

echo.
echo Done. This window will close in 10 seconds.
timeout /t 10 /nobreak >nul

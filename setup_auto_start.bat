@echo off
REM ============================================================
REM  Setup: Register Client Finder in Windows Task Scheduler
REM  RIGHT-CLICK THIS FILE -> "Run as administrator"
REM  This creates a scheduled task that runs on every login.
REM ============================================================

set TASK_NAME=ClientFinderAutoRun
set SCRIPT_PATH=%~dp0run_client_finder.bat

echo.
echo  Setting up Client Finder to run automatically on login...
echo  Task Name: %TASK_NAME%
echo  Script:    %SCRIPT_PATH%
echo.

REM Delete existing task if any
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create task: runs on every logon, starts in project folder
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%SCRIPT_PATH%\"" ^
    /sc ONLOGON ^
    /rl HIGHEST ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo  SUCCESS! Client Finder will now run every time you log in.
    echo  It will automatically skip if less than 12 hours passed.
    echo.
    echo  To remove:  schtasks /delete /tn "%TASK_NAME%" /f
    echo  To run now: schtasks /run /tn "%TASK_NAME%"
) else (
    echo.
    echo  FAILED! Make sure you ran this as Administrator.
    echo  Right-click the file and select "Run as administrator"
)

echo.
pause

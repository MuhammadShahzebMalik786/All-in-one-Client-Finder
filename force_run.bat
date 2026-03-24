@echo off
REM ============================================================
REM  Client Finder — FORCE RUN until 300 emails sent
REM  Loops the pipeline, resetting cooldown each cycle,
REM  until sent_emails.csv reaches 300 rows.
REM ============================================================

cd /d "%~dp0"

set TARGET=300
set SENT_FILE=data\sent_emails.csv

echo ============================================================
echo  Client Finder — Force Run (target: %TARGET% emails)
echo ============================================================

:LOOP

REM --- Count sent emails (subtract 1 for header row) ---
set SENT_COUNT=0
if exist "%SENT_FILE%" (
    for /f %%A in ('find /c /v "" ^< "%SENT_FILE%"') do set SENT_COUNT=%%A
    if %SENT_COUNT% GTR 0 set /a SENT_COUNT=%SENT_COUNT%-1
)

echo.
echo  [%date% %time%] Emails sent so far: %SENT_COUNT% / %TARGET%

if %SENT_COUNT% GEQ %TARGET% (
    echo.
    echo  ============================================================
    echo   TARGET REACHED! %SENT_COUNT% emails sent.
    echo  ============================================================
    goto DONE
)

REM --- Reset cooldown so pipeline always runs ---
if exist "data\last_run.txt" del "data\last_run.txt"

echo  Cooldown reset — starting pipeline cycle...
echo.

c:\python314\python.exe automatic_main.py

echo.
echo  Cycle complete. Waiting 60 seconds before next cycle...
timeout /t 60 /nobreak >nul

goto LOOP

:DONE
echo.
echo Done. This window will close in 30 seconds.
timeout /t 30 /nobreak >nul

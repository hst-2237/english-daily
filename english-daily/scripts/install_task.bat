@echo off
rem Double-click this file to create / update the daily push task.
rem It registers two triggers: daily 07:30 AND at every logon (2 min delay).
rem The script itself de-duplicates by date, so you get one push per day.
setlocal
cd /d "%~dp0.."

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_task.ps1" %*
if errorlevel 1 (
    echo.
    echo [!] Failed. Right-click this file and choose "Run as administrator".
)
echo.
pause
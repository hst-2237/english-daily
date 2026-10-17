@echo off
rem 计划任务每天调用这个脚本：切到项目目录，跑一句，日志写进 logs\daily.log
setlocal
cd /d "%~dp0.."

if not exist logs mkdir logs

set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

"%PY%" run.py >> "logs\daily.log" 2>&1

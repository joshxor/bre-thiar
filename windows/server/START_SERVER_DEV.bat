@echo off
setlocal
cd /d "%~dp0"
set PORT=8765
set HOST=127.0.0.1
set OPEN_BROWSER=0
node server.mjs
if errorlevel 1 pause

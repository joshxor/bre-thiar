@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File tools\build-windows-exe.ps1
if errorlevel 1 (
  echo.
  echo WINDOWS EXPORT FAILED
  pause
  exit /b 1
)
echo.
echo Windows package created under build\
pause

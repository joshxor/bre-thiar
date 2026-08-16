@echo off
setlocal
cd /d "%~dp0"
python client\tests\validate_windows_project.py || goto :fail
python client\tests\validate_network_contract.py || goto :fail
cd server
node --check server.mjs || goto :fail
node tests\windows-network-smoke.mjs || goto :fail
cd ..
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run-godot-self-check.ps1 || goto :fail
echo.
echo ALL BRE THIAR WINDOWS VALIDATION PASSED
exit /b 0
:fail
echo.
echo VALIDATION FAILED
pause
exit /b 1

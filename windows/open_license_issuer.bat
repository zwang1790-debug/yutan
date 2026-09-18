@echo off
setlocal
cd /d "%~dp0.."

where python >nul 2>nul
if %errorlevel%==0 (
    python tools\license_issuer_gui.pyw
    exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 tools\license_issuer_gui.pyw
    exit /b %errorlevel%
)

echo Python 3 was not found. Please install Python 3.10 or later.
pause
exit /b 1

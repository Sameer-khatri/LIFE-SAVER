@echo off
title LIFE SAVER - Execution System
echo.
echo  ========================================
echo   LIFE SAVER - Starting Execution System
echo  ========================================
echo.

:: Navigate to the app directory
cd /d "%~dp0"

:: Check for Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :found
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :found
)

echo  [ERROR] Python not found.
echo  Install Python from https://python.org and ensure it is in PATH.
echo.
pause
exit /b 1

:found
echo  Using: %PYTHON_CMD%
echo  App directory: %cd%
echo.

:: Check Flask is installed
%PYTHON_CMD% -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Flask is not installed.
    echo  Run: %PYTHON_CMD% -m pip install flask
    echo.
    pause
    exit /b 1
)

:: Open browser after a short delay (runs in background)
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

:: Start the Flask app
echo  Starting Flask server on http://127.0.0.1:5000 ...
echo  Press Ctrl+C to stop.
echo.
%PYTHON_CMD% app.py

:: If we get here, the app exited
echo.
echo  [STOPPED] Flask server has stopped.
echo.
pause

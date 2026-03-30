@echo off
title Seedance Video AI
echo.
echo   Starting Seedance Video AI...
echo   (Keep this window open while using the app)
echo.
node "%~dp0seedance-server.js"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   ERROR: Node.js is not installed or not in PATH.
    echo   Download it from https://nodejs.org
    echo.
    pause
)

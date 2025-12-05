@echo off
title Quiz Server - Quick Stop
color 0C

echo.
echo ========================================
echo      ⛔ QUIZ SERVER QUICK STOP ⛔
echo ========================================
echo.

echo 🛑 Stopping all Python/Flask processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM py.exe >nul 2>&1

echo.
echo ✅ Quiz server stopped successfully!
echo.
echo 💡 To start again, use:
echo    - QUICK_START.bat (simple start)
echo    - SERVER_CONTROL.bat (advanced options)
echo.
pause
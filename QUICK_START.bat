@echo off
title Quiz Server - Quick Start
color 0A

echo.
echo ========================================
echo      🚀 QUIZ SERVER QUICK START 🚀
echo ========================================
echo.

REM Get IP address for display
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do set "IP=%%a"
for /f "tokens=1" %%a in ('echo %IP%') do set "CLEAN_IP=%%a"

echo 📡 Starting server...
start "Quiz Server" cmd /c "start_quiz_server.bat"

echo.
echo ✅ Server starting in background!
echo.
echo 🌐 ACCESS LINKS:
echo ================
echo.
echo 👥 STUDENTS: http://%CLEAN_IP%:5000
echo 👨‍💼 ADMIN:    http://%CLEAN_IP%:5000/admin_dashboard  
echo 💻 LOCAL:    http://localhost:5000
echo.
echo 📋 Admin Login: admin / admin123
echo.
echo ========================================
echo.
echo ✨ Your quiz server is now running!
echo    Use SERVER_CONTROL.bat for advanced options
echo.
pause